cat test_db.sql | sqlite3 resources/data/test_db.db

docker compose -f ../docker-compose.yml -f docker-compose.test.yml up celery nn_api backend -d

pytest -s ./api

docker compose down

rm resources/data/test_db.db