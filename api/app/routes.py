import os
import flask
# import flask_praetorian
# import flask_cors
import json
# import jwt

from app import app, db
from app.email import send_password_reset_email, send_failure_email
from app.models import User
from flask_login import current_user, login_user

from time import time
from datetime import datetime, timedelta
from flask_mail import Mail

# cors = flask_cors.CORS()
# guard = flask_praetorian.Praetorian()

# # Initialize the flask-praetorian instance for the app
#guard.init_app(app, User)


# Set up some routes for the example
@app.before_request
def before_request():
    current_user.last_seen = datetime.utcnow()
    db.session.commit()


@app.route('/api/')
def home():
    return {"Hello": "World"}, 200

  
@app.route('/api/login', methods=['POST'])
def login():
    """
    Logs a user in by parsing a POST request containing user credentials and
    issuing a JWT token.
    .. example::
       $ curl http://localhost:5000/api/login -X POST 
         -d '{"username":"Yasoob","password":"strongpassword"}'
    """
    req = flask.request.get_json(force=True)
    email = req.get('email', None)
    password = req.get('password', None)
    print(password)
    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
    #if user is None or not guard.authenticate(email, password):
        ret = {'Invalid username or password for': user.email}, 418
    else:
       #token = user.get_login_token()
        # ret = {'access_token': guard.encode_jwt_token(user)}, 200
        #token = jwt.encode({'exp': datetime.utcnow()+timedelta(days=0,minutes=30,seconds=0) }, app.config['SECRET_KEY'], algorithm='HS256' )
        # not json serializable 
        #token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhIjoiYiJ9.dvOo58OBDHiuSHD4uW88nfJikhYAXc_sfUHq1mDi4G0'
        token = user.get_login_token().decode('utf-8')
        print(token)
        ret = {'access_token': token}, 200
    return ret


@app.route('/api/register', methods=['POST'])
def register():
    """
    Logs a user in by parsing a POST request containing user credentials and
    issuing a JWT token.
    .. example::
       $ curl http://localhost:5000/api/login -X POST \
         -d '{"email":"Yasoob","password":"strongpassword"}'
    """
    req = flask.request.get_json(force=True)
    print(req)
    email = req.get('email', None)
    first_name = req.get('first', None)
    last_name = req.get('last', None)
    organization = req.get('org', None)
    password = req.get('password', None)
    user = User.query.filter_by(email=email).count()
    print(user)

    if user >= 1:
        message={'There is already an account associated with that email': email}, 418
        #prefer not to return object
    else:
        message = {'Welcome': first_name}, 200
        user = User(email=email, first_name=first_name, last_name=last_name, organization=organization)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
    # guard.send_registration_email(email, user=User, template=None, confirmation_sender=None, confirmation_uri=None, subject=None, override_access_lifespan=None)
    #should we log user in automatically?
    
    return message
  
@app.route('/api/refresh', methods=['POST'])
def refresh():
    """
    Refreshes an existing JWT by creating a new one that is a copy of the old
    except that it has a refrehsed access expiration.
    .. example::
       $ curl http://localhost:5000/api/refresh -X GET \
         -H "Authorization: Bearer <your_token>"
    """
    print("refresh request")
    old_token = flask.request.get_data()
    new_token = guard.refresh_jwt_token(old_token)
    ret = {'access_token': new_token}, 200
    return ret
  

@app.route('/api/nn', methods=['POST'])
def nn ():
    req = flask.request.get_data()
    if isinstance(req, str):
        message = 'string'
        print(req)
    else:
        message = 'file'
        print(req)
    return message


# @app.route('/api/protected')
# @flask_praetorian.auth_required
# def protected():
#     """
#     A protected endpoint. The auth_required decorator will require a header
#     containing a valid JWT
#     .. example::
#        $ curl http://localhost:5000/api/protected -X GET \
#          -H "Authorization: Bearer <your_token>"
#     """
#     return {'message': f'protected endpoint (allowed user {flask_praetorian.current_user().email})'}

@app.route('/api/forgot', methods=['GET', 'POST'])
def forgot():
    req = flask.request.get_json(force=True)
    #print(req)
    email = req.get('email', None)
    user = User.query.filter_by(email=email).first()
    print('****User:', user)
    if user is not None:
        print('user is not none')
        send_password_reset_email(user)
        message={'email sent to': email}, 200
    else:
        #should send an error email saying that the email does not exist in db
        send_failure_email(email)
        message={'email sent to': email}, 418
        
        
    return message


@app.route('/api/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    
    user = User.verify_reset_password_token(token)
    print(user, token)
    req = flask.request.get_json(force=True)
    new_password = req.get('password', None)
    print(new_password)
    if user:
        #should also make sure password is not the same
        user.set_password(new_password)
        db.session.add(user)
        db.session.commit()
        message={'password reset for': user.email}, 200
    else:
        message= {'invalid token': None }, 418
    return message
    

# Run the example
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)