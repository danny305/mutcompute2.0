from os import environ
from pathlib import Path
from datetime import datetime
from tempfile import TemporaryDirectory

import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase

from celery import Celery
import sqlalchemy as db
import pandas as pd

from mutcompute.scripts.run import gen_ensemble_inference


HOSTNAME = environ.get("HOSTNAME", "mutcompute.com")
PORT = environ.get("PORT", 80)

CELERY_BROKER_URL = environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery = Celery("task", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

db_engine = db.create_engine(f'sqlite:///{environ.get("DB_URI", "/tmp/temp.db")}')
meta_data = db.MetaData()
nn_table = db.Table(
    environ.get("DB_NN_TABLE", "NN_Query"),
    meta_data,
    autoload=True,
    autoload_with=db_engine,
)


# TODO I can turn this into a decorator so all you have to is pass in a net function and a few parameters
@celery.task(name="task.run_mutcompute")
def run_mutcompute(
    email,
    pdb_code,
    dir="/mutcompute_2020/mutcompute/data/pdb_files",
    out_dir="/mutcompute_2020/mutcompute/data/inference_CSVs",
    fs_pdb=False,
    load_cache=False,
):

    pdb_id = pdb_code[:4]

    try:
        if load_cache:
            print("LOADING CACHED RESULTS")
            df = retrieve_cache_predictions(pdb_id)
        else:
            df = gen_ensemble_inference(
                pdb_code, dir=dir, out_dir=out_dir, fs_pdb=fs_pdb
            )

    except Exception as e:
        print("FAIL: ", e)
        inference_fail_email(email, pdb_id, problem="nn")
        return False

    else:
        email_status = inference_email(email, pdb_id, df)

        stmt = db.insert(nn_table).values(
            user_email=email,
            pdb_query=pdb_id,
            query_time=datetime.now(),
            query_inf=df.to_json(orient="index"),
            query_email_sent=email_status,
        )

        with db_engine.connect() as conn:
            conn.execute(stmt)
            print(f"Added query {email}, {pdb_id} to the NN_Query table.")

        return True


def retrieve_cache_predictions(pdb_id):

    stmt = db.select(nn_table.c.query_inf).where(nn_table.c.pdb_query == pdb_id)

    with db_engine.connect() as conn:
        # This returns a LegacyRow object from sqlalchemy
        predictions = conn.execute(stmt).first()

    df = pd.DataFrame.from_dict(json.loads(predictions[0])).T

    return df


def inference_email(user_email, pdb_id, df=None):
    """This is an aws ses function."""

    view_url = f"https://{HOSTNAME}/view/{pdb_id}"

    html = f"""
        <div>
            <p>
                Thank you for using MutCompute!
            </p>
            <p>
                Predictions for all residues are attached as a CSV. 
                To visualize the predictions with MutCompute-View visit <a href="{view_url}">{view_url}</a>.
            </p>
        </div>
    """

    subject = f"MutCompute Predictions: {pdb_id}"
    from_name = "no-reply@mutcompute.com"

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["FROM"] = from_name
    msg["To"] = user_email

    html_mime = MIMEText(html, "html")
    msg.attach(html_mime)

    if not df is None:
        with TemporaryDirectory() as tmp_dir:

            csv_file = tmp_dir + f"/{pdb_id}.csv"
            df.to_csv(csv_file)

            with open(csv_file, "rb") as f:
                attachment = MIMEBase("text", "csv")
                attachment.set_payload(f.read())

            attachment.add_header(
                "Content-Disposition", "attachment", filename=f"{pdb_id}.csv"
            )
            msg.attach(attachment)

    server = smtplib.SMTP(environ["SES_EMAIL_HOST"], environ["SES_EMAIL_PORT"])
    server.connect(environ["SES_EMAIL_HOST"], environ["SES_EMAIL_PORT"])
    server.starttls()
    server.login(environ["SES_SMTP_USERNAME"], environ["SES_SMTP_PASSWORD"])

    try:
        recipients = [user_email, "danny.diaz@utexas.edu", "jamesmadiganloy@gmail.com"]
        server.sendmail(from_name, recipients, msg.as_string())
        print(f"Sent email for {pdb_id}")

    except Exception as e:
        print("Failed to send NN email.")
        server.quit()
        return False

    server.quit()
    print("Sent NN email")
    return True


def inference_fail_email(user_email, pdb_id, problem="nn"):

    subject = f"MutCompute Prediction Failure: {pdb_id}"
    from_name = "no-reply@mutcompute.com"
    recipients = [user_email, "danny.diaz@utexas.edu", "jamesmadiganloy@gmail.com"]

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["FROM"] = from_name

    message = ""
    if problem == "nn":
        message = f"""
            <div>
                <p>
                    Thank you for using MutCompute!
                </p>
                <p>
                    Unfortunately, we ran into a problem while computing the predictions on PDB: {pdb_id}.
                </p>
                <p>
                    We have been notified of the issue and expect an email from us over the next 48 hours 
                    with more details.
                    <br>
                    Sorry for the inconvenience.
                </p>
            </div>
        """

    elif problem == "email":
        message = f"""
            <div>
                <p>
                    There was a problem sending email to user: {user_email} for pdb: {pdb_id}. 
                    However, the MutCompute ran successfully.
                    <br>
                </p>
            </div>
        """
    else:
        message = f"""
            <div>
                <p>
                    There was an unknown problem with pdb: {pdb_id} for user: {user_email}. 
                </p>
            </div>
        """

    mime_html = MIMEText(message, "html")
    msg.attach(mime_html)

    server = smtplib.SMTP(environ["SES_EMAIL_HOST"], environ["SES_EMAIL_PORT"])
    server.connect(environ["SES_EMAIL_HOST"], environ["SES_EMAIL_PORT"])
    server.starttls()
    server.login(environ["SES_SMTP_USERNAME"], environ["SES_SMTP_PASSWORD"])

    try:
        if problem == "nn":
            for recipient in recipients:
                msg["To"] = recipient
                server.sendmail(from_name, recipient, msg.as_string())

        else:
            msg["To"] = recipients[1]
            server.sendmail(
                from_name, recipients[1], msg.as_string()
            )  # Sending this only to me

    except Exception as e:
        print(f"Failed to send NN email.\n{e}")
        server.quit()
        return False

    server.quit()
    print("Sent NN failure email")
    return True
