import sqlalchemy as db
from sqlalchemy import text
from datetime import datetime
from json import loads

from settings import logger


class SqliteUpdater:
    def __init__(self, nn_table, uri):

        self.db_engine = db.create_engine(f"sqlite:///{uri}")
        self.meta_data = db.MetaData()
        self.nn_table = db.Table(
            nn_table, self.meta_data, autoload=True, autoload_with=self.db_engine
        )

    def update_db(self, email, pdb_id, df, email_sent):

        stmt = db.insert(self.nn_table).values(
            user_email=email,
            pdb_query=pdb_id,
            query_time=datetime.now(),
            query_inf=df.to_json(orient="index"),
            query_email_sent=email_sent,
        )

        try:
            with self.db_engine.connect() as conn:
                conn.execute(stmt)
                logger.info("Added query %s, %s to the NN_Query table.", email, pdb_id)
        except Exception:
            logger.error("Could not update db with entry for %s, %s", email, pdb_id, exc_info=True)

    def get_prediction(self, pdb_id):
        sql = text(
            f"SELECT * FROM NN_Query WHERE pdb_query == '{pdb_id.upper()}' LIMIT 1"
        )

        try:
            preds = None
            with self.db_engine.connect() as conn:
                res = conn.execute(sql)

                for row in res:
                    preds = loads(row[4])
            return preds
        except Exception:
            logger.error("Could not query for pdb %s", pdb_id, exc_info=True)
