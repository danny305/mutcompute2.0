import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from os import environ

from flask import render_template, url_for
from itsdangerous import URLSafeTimedSerializer

from app import app

HOSTNAME = environ.get('HOSTNAME', 'mutcompute.com')
PORT= environ.get('PORT', 80)

def send_email_confirmation(user_email):

    confirm_serializer = URLSafeTimedSerializer(app.config['MAIL_SECRET_KEY'])
    token = confirm_serializer.dumps(user_email, salt=app.config['MAIL_SALT'])

    #TODO refactor for deployment.
    confirm_url = f"http://{HOSTNAME}{url_for('confirm_email', token=token)}" 

    html = render_template('email_confirmation.html', confirm_url=confirm_url)

    subject = 'MutCompute Email Confirmation'
    sender_email = "no-reply@mutcompute.com"

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['FROM'] = sender_email
    msg['To'] = str(user_email)

    html_mime = MIMEText(html, 'html')

    msg.attach(html_mime)

    server = smtplib.SMTP(app.config['SES_EMAIL_HOST'], app.config['SES_EMAIL_PORT'])
    server.connect(app.config['SES_EMAIL_HOST'], app.config['SES_EMAIL_PORT'])
    server.starttls()
    server.login(app.config["SES_SMTP_USERNAME"], app.config["SES_SMTP_PASSWORD"])

    print("Confirmation url: ", confirm_url, file=sys.stderr)

    try:
        server.sendmail(sender_email, [user_email, 'danny.diaz@utexas.edu'], msg.as_string())

    except Exception as e:
        print(f'Error in sending confirmation email to user: {user_email}')
        server.quit()
        return False, ""

    server.quit()
    print('Sent email')
    return True, token


def send_password_reset(user_email):

    confirm_serializer = URLSafeTimedSerializer(app.config['MAIL_SECRET_KEY'])
    token = confirm_serializer.dumps(user_email, salt=app.config['MAIL_SALT'])

    reset_url = f"http://{HOSTNAME}{url_for('reset_password', token=token)}" 

    html = render_template('reset_pass.html', reset_url=reset_url)

    subject = 'MutCompute Password Reset'
    sender_email = "no-reply@mutcompute.com"

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['FROM'] = sender_email
    msg['To'] = str(user_email)

    html_mime = MIMEText(html, 'html')

    msg.attach(html_mime)

    server = smtplib.SMTP(app.config['SES_EMAIL_HOST'], app.config['SES_EMAIL_PORT'])
    server.connect(app.config['SES_EMAIL_HOST'], app.config['SES_EMAIL_PORT'])
    server.starttls()
    server.login(app.config["SES_SMTP_USERNAME"], app.config["SES_SMTP_PASSWORD"])

    print("Reset url: ", reset_url, file=sys.stderr)

    try:
        server.sendmail(sender_email, user_email, msg.as_string())

    except Exception as e:
        print(f'Error in sending password reset email to user: {user_email}')
        server.quit()
        return False

    server.quit()
    print('Sent email')
    return True

