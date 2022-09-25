import json
import sys
import requests
import pandas as pd

from flask import request, redirect, url_for
from flask_praetorian import auth_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

from app import app, db, guard
from app.email import send_email_confirmation, send_password_reset
from app.models import Users, NN_Query



@app.route("/api/")
def home():
    return {"Hello": "Protein Engineer"}, 200


@app.route("/api/login", methods=["POST"])
def login():
    req = request.get_json(force=True)
    email = req.get("email", None)
    password = req.get("password", None)
    user = guard.authenticate(email, password)
    print(f"User praetorian: {user}", file=sys.stderr)
    if user is None or not user.check_password(password):
        return {"access_token": None}, 401

    token = guard.encode_jwt_token(user)
    return {"access_token": token}, 200


@app.route("/api/register", methods=["POST"])
def register():
    req = request.get_json(force=True)

    print(req, file=sys.stderr)

    email = req.get("email", None)
    first_name = req.get("first", None)
    last_name = req.get("last", None)
    organization = req.get("org", None)
    password = req.get("password", None)
    user = Users.query.filter_by(email=email).count()

    if user > 0 and Users.query.filter_by(email=email).one().email_confirmed:
        return {"Status": "Account already exist for this email."}, 418

    # Add to database or overwrite if user is already present but not confirmed.
    user = Users(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        organization=organization,
    )
    user.save_to_db()

    email_success, token = send_email_confirmation(email)
    if email_success:
        return {"Status": "Sent email confirmation link", "token": token}, 200

    return {"Status": "Failed to send confirmation link. Please email us."}, 500


@app.route("/api/refresh", methods=["POST"])
def refresh():
    """
    Refreshes an existing JWT by creating a new one that is a copy of the old
    except that it has a refrehsed access expiration.
    .. example::
       $ curl http://localhost:5000/api/refresh -X GET \
         -H "Authorization: Bearer <your_token>"
    """
    print("refresh request")
    old_token = request.get_data()
    new_token = guard.refresh_jwt_token(old_token)
    ret = {"access_token": new_token}, 200
    return ret


@app.route("/api/nn", methods=["POST"])
@auth_required
def nn():
    data = request.get_json()
    load_cache = data.get("loadCache", True)
    pdb_id = data["id"]

    payload = {
        "username": current_user().email,
        "pdb_code": pdb_id,
        "load_cache": False,
    }

    if load_cache and NN_Query.query.filter_by(pdb_query=pdb_id).count():
        payload["load_cache"] = True

    response = requests.post("http://nn_api:8000/inference", json=payload)

    return response.json(), response.status_code


@app.route("/api/fetch_predictions", methods=["POST"])
def fetch_pdb_predictions():
    pdb_id = json.loads(request.get_data())
    exist = NN_Query.query.filter_by(pdb_query=pdb_id).count()

    if exist:
        db_row = NN_Query.query.filter_by(pdb_query=pdb_id).first()

        df = pd.DataFrame.from_dict(json.loads(db_row.query_inf)).T
        csv = df.to_csv()

        return {"pdb": pdb_id, "predictions": csv}, 200

    else:
        return {"pdb": pdb_id, "predictions": None}, 400


@app.route("/api/forgot", methods=["GET", "POST"])
def forgot():
    req = request.get_json(force=True)
    email = req.get("email", None)

    user = Users.query.filter_by(email=email).first()
    if user:
        print("user is not none")
        send_password_reset(user.email)
        return {"Status": f"Sent email to {email}"}, 200
    else:
        # TODO react should say email is invalid
        # should send an error email saying that the email does not exist in db
        return {"Status": "invalid email"}, 400


@app.route("/api/email_confirmation/<token>")
def confirm_email(token):
    confirm_serializer = URLSafeTimedSerializer(app.config["MAIL_SECRET_KEY"])
    email = None
    try:
        email = confirm_serializer.loads(
            token, salt=app.config["MAIL_SALT"], max_age=86400
        )  # 604800 is 7 days

    except SignatureExpired:
        # TODO work with brad to see what he wants to do here.
        print("The confirmation link has an expired signature.", file=sys.stderr)
        return {"access_token": None}, 400
        # redirect(url_for('login'))

    except BadTimeSignature:
        # TODO work with brad to see what he wants to do here.
        print("The token has expired.", file=sys.stderr)
        return {"access_token": None}, 400
        # redirect(url_for('login'))

    else:
        user = Users.query.filter_by(email=email).first()

        print(f"Confirming email for {user.email}")

        if user.email_confirmed:
            print(f"User {user.email} has already confirmed his email", file=sys.stderr)

        else:
            user.confirm_email()
            print(
                f"Email has been successfully confirmed for {user.email}",
                file=sys.stderr,
            )

        token = guard.encode_jwt_token(user)
        return {"access_token": token}, 200


@app.route("/api/reset/<token>", methods=["POST"])
def reset_password(token):

    confirm_serializer = URLSafeTimedSerializer(app.config["MAIL_SECRET_KEY"])

    try:
        email = confirm_serializer.loads(
            token, salt=app.config["MAIL_SALT"], max_age=86400
        )  # 604800 is 7 days

    except SignatureExpired:
        # TODO work with brad to see what he wants to do here.
        print("The confirmation link has an expired signature.", file=sys.stderr)
        return {"Status": "Token Expired"}, 400
        # redirect(url_for('login'))

    except BadTimeSignature:
        # TODO work with brad to see what he wants to do here.
        print("The token has expired.", file=sys.stderr)
        return {"Status": "Token Expired"}, 400
        # redirect(url_for('login'))
    else:
        new_password = request.get_json(force=True)
        user = Users.query.filter_by(email=email).first()
        user.set_password(new_password)

        return {"Status": "Success"}, 200
