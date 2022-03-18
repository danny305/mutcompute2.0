from pathlib import Path
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from tempfile import TemporaryDirectory

import settings
from settings import logger


def get_server(host, port, username, password):
    server = smtplib.SMTP(host, port)
    server.connect(host, port)
    server.starttls()
    server.login(username, password)

    logger.info("Connected to SMTP server")
    return server


def inference_email(user_email, pdb_id, df):
    """This is an aws ses function."""

    view_url = f"https://{settings.hostname}/view/{pdb_id}"

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

    logger.info("Generating csv file for predictions")
    with TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        csv_file = tmp_dir / f'{pdb_id}.csv'

        df.to_csv(csv_file)
        logger.info("csv saved to file")

        with csv_file.open('rb') as f:
            attachment =  MIMEBase('text', 'csv')
            attachment.set_payload(f.read())

        attachment.add_header('Content-Disposition', "attachment", filename=f'{pdb_id}.csv')
        msg.attach(attachment)
        logger.info("csv attached to email")

    try:
        server = get_server(
            settings.ses_email_host,
            settings.ses_email_port,
            settings.ses_smtp_username,
            settings.ses_smtp_password
        )

        server.sendmail(
            from_name, [user_email, "danny.diaz@utexas.edu"], msg.as_string()
        )
        logger.info("Sent email for %s", pdb_id)

    except Exception:
        logger.error("Failed to send email to %s for pdb %s.", user_email, pdb_id)
        server.quit()
        return False

    server.quit()
    return True


def inference_fail_email(user_email, pdb_id, problem='nn'):

    subject = f'MutCompute Prediction Failure: {pdb_id}'
    from_name = 'no-reply@mutcompute.com'
    recipients = [user_email, 'danny.diaz@utexas.edu']

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['FROM'] = from_name

    message = ''
    if problem == 'nn':
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

    elif problem == 'email':
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

    mime_html = MIMEText(message, 'html')
    msg.attach(mime_html)

    try:
        server = get_server(
            settings.ses_email_host,
            settings.ses_email_port,
            settings.ses_smtp_username,
            settings.ses_smtp_password
        )
        if problem=='nn':
            for recipient in recipients:
                msg['To'] = recipient
                server.sendmail(from_name, recipient, msg.as_string())

        else:
            msg['To'] = recipients[1]
            server.sendmail(from_name, recipients[1], msg.as_string()) # Sending this only to me

        logger.info("Sent failure email for %s", pdb_id)

    except Exception as e:  
        logger.error("Failed to failure send email to %s for pdb %s.", user_email, pdb_id)
        server.quit()
        return False


    server.quit()
    print('Sent NN failure email')
    return True