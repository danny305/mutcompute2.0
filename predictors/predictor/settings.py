import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(pathname)s:%(lineno)d:%(levelname)s :: %(message)s')

ch.setFormatter(formatter)
logger.addHandler(ch)

aws_region = os.getenv("AWS_REGION", "us-east-1")
job_queue_url = os.getenv("JOB_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/444461107311/predictor-test.fifo")

model_bucket = os.getenv("MODEL_BUCKET", "mutcompute-models")

def _get_comma_sep(var):
    var_string = os.getenv(var)
    var_list = var_string.split(",")
    return var_list

models = _get_comma_sep("MODEL_LIST")
pipeline = os.getenv("PIPELINE_FILE")

hostname = os.getenv("HOSTNAME", "mutcompute.com")
ses_email_host = os.getenv("SES_EMAIL_HOST")
ses_email_port = int(os.getenv("SES_EMAIL_PORT"))
ses_smtp_username = os.getenv("SES_SMTP_USERNAME")
ses_smtp_password = os.getenv("SES_SMTP_PASSWORD")

nn_table = os.getenv("DB_NN_TABLE")
db_uri = os.getenv("DB_URI")