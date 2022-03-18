from settings import logger
import tempfile
import tarfile
from pathlib import Path
from dataclasses import asdict
import time
from json import loads

import numpy as np

from ApBioInfo.snapshots import SSResidue, SSCodeResidue, SSFileResidue

from ApBio.Schemas.Pipeline import Pipeline
from ApBio.SnapshotProducer import AdHocSnapshotProducer

from Negatron.models.tf import load_model
from Negatron.data_processing import (
    prediction_df,
    average_predictions,
)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def batches_snapshots(pl, n):
    boxes = list()
    snapshots = list()
    for x, _, ss in pl(n):
        boxes.append(x)
        snapshots.extend(ss)

    return boxes, snapshots


def _convert_ss(ss):
    if ss["type"] == "CODE_CHAIN_RESIDUE":
        return SSCodeResidue(**ss)
    elif ss["type"] == "FILE_CHAIN_RESIDUE":
        return SSFileResidue(**ss)
    else:
        raise RuntimeError(f"Unexpected residue schema: {ss}")


class SinglePipelineEnsemblePredictor:
    def __init__(self, s3bucket, models, pipeline, n_threads=5):

        self.models = list()
        self.n_threads = n_threads

        try:
            self.apbio_pipeline = self._load_pipeline(s3bucket, pipeline)
        except Exception:
            logger.error("Failed to load pipeline %s", pipeline, exc_info=True)
            raise

        for model in models:
            try:
                loaded_model = self._load_model(s3bucket, model)
                self.models.append(loaded_model)
            except Exception:
                logger.error("Failed to load model %s", model, pipeline)
                raise

    def _load_pipeline(self, bucket_client, pipeline):

        with tempfile.TemporaryDirectory() as pipeline_dir:
            pipeline_file = pipeline_dir + "/" + pipeline

            bucket_client.download_file(pipeline, pipeline_file)
            logger.info(
                "Downloaded pipeline %s to location %s", pipeline, pipeline_file
            )

            loaded_pipeline = Pipeline.parse_file(pipeline_file)
            logger.info("Parsed pipeline")
            return loaded_pipeline

    def _load_model(self, bucket_client, model):

        with tempfile.TemporaryDirectory() as model_dir:

            model_file = model_dir + "/" + model
            bucket_client.download_file(model, model_file)
            logger.info("Downloaded model tarball %s to file %s", model, model_file)

            tarball = tarfile.open(model_file, "r")
            model_folder = tarball.getmembers()[0].name
            logger.info(
                "Model tarball has top level member called %s", model_folder,
            )
            tarball.extractall(path=model_dir)
            logger.info("Extracted model")

            loaded_model = load_model(Path(model_dir + "/" + model_folder))
            logger.info("Loaded model")
            return loaded_model

    def predict(self, snapshots, doc_creator):

        logger.info("Starting ensemble prediction for %i snapshots", len(snapshots))
        l_size = int(float(len(snapshots) + self.n_threads - 1) / float(self.n_threads))

        producers = list()
        for split_ss in chunks(list(snapshots), l_size):
            producers.append(AdHocSnapshotProducer([asdict(ss) for ss in split_ss]))

        pl = self.apbio_pipeline.instantiate(producers, [doc_creator] * self.n_threads)

        t_start = time.time()
        batches, ss = batches_snapshots(pl, 100)
        boxes = np.vstack(batches)
        t_elapsed = time.time() - t_start
        ss = [_convert_ss(loads(s)) for s in ss]

        logger.info(
            "Created boxes in %d seconds, shape: %s", t_elapsed, boxes.shape
        )

        all_preds = list()
        for i, model in enumerate(self.models):
            logger.info("Running predictions for model %i", i)

            preds = model.predict(boxes, verbose=1)
            logger.info("Finished predictions for model %i", i)
            all_preds.append(prediction_df(ss, preds))

        logger.info("Finished all predictions, averaging now")
        averages = average_predictions(all_preds)
        logger.info("Finished predict")
        return averages
