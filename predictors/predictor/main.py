from settings import logger
import settings
import tempfile
from pathlib import Path
import sys

import boto3
import time

import signal
from json import dumps

from pydantic import BaseModel

import pandas as pd

from predictors import SinglePipelineEnsemblePredictor
from notify import inference_email, inference_fail_email
from db_update import SqliteUpdater

from ApChem.cif import process_pdb, run_chimX_fw2_freesasa_pipeline
from Negatron.data_processing import snapshots_from_cif
from ApBio.ApBioGemmi import LocalDocumentCreator


class PredictCommand(BaseModel):
    pdb_code: str
    user_email: str


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True


def make_prediction(pdb_code, predictor: SinglePipelineEnsemblePredictor):
    with tempfile.TemporaryDirectory() as cif_dir:
        logger.info("Fetching pdb file")

        try:
            init_cif = process_pdb(pdb_code, Path(cif_dir))
            the_cif = run_chimX_fw2_freesasa_pipeline(init_cif)

        except Exception:
            logger.error(
                "Unable to fetch pdb file for code %s", pdb_code, exc_info=True
            )
            return

        logger.info("Successfully fetched pdb file")

        snapshots = snapshots_from_cif(the_cif)
        logger.info("Generated %i snapshots", len(snapshots))

        doc_creator = LocalDocumentCreator(cif_dir, "", ".fw2.sasa", 20)

        return predictor.predict(snapshots, doc_creator)


def handle_command(command: PredictCommand, predictor: SinglePipelineEnsemblePredictor):

    try:
        updater = SqliteUpdater(settings.nn_table, settings.db_uri)
        preds_json = updater.get_prediction(command.pdb_code)

        if preds_json is not None:
            logger.info("Using cached prediction for pdb %s", command.pdb_code)
            df = pd.DataFrame.from_dict(preds_json)
        else:
            t_start = time.time()
            df = make_prediction(command.pdb_code, predictor)
            t_predict = time.time() - t_start
            logger.info(
                "Finished prediction in %f seconds for pdb %s",
                t_predict,
                command.pdb_code,
            )

    except Exception:
        logger.error("Unable to make prediction", exc_info=True)
        inference_fail_email(command.user_email, command.pdb_code)
    else:
        email_sent = inference_email(command.user_email, command.pdb_code, df)
        updater.update_db(command.user_email, command.pdb_code, df, email_sent)


def listen(sqs_client, queue_url, predictor):
    gk = GracefulKiller()

    while not gk.kill_now:
        response = sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
        logger.debug("Got response %s", response)

        if "Messages" in response:

            message = response["Messages"][0]

            try:
                command = PredictCommand.parse_raw(message["Body"])
            except Exception:
                logger.error(
                    "Unable to decode message %s", message["Body"], exc_info=True
                )
            else:
                handle_command(command, predictor)

            sqs.delete_message(
                QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"]
            )
            logger.info("Message deleted from queue")


if __name__ == "__main__":

    logger.info("Starting worker")
    sqs = boto3.client("sqs", region_name=settings.aws_region)
    logger.info("Created SQS client")

    s3 = boto3.resource("s3", region_name=settings.aws_region)
    bucket = s3.Bucket(settings.model_bucket)
    logger.info("Connected to bucket")

    pred = SinglePipelineEnsemblePredictor(bucket, settings.models, settings.pipeline)

    logger.info("Starting listening loop")
    try:
        listen(sqs, settings.job_queue_url, pred)
    except Exception:
        logger.error("Listening loop exited with uncaught exception", exc_info=True)
        sys.exit(1)

    logger.info("Exiting predictor.")
