cat test/test_db.sql | sqlite3 test/resources/data/test_db.db

docker compose -f ./docker-compose.yml -f ./test/docker-compose.test.yml up celery nn_api backend -d

pytest -s ./test/api

docker compose down --remove-orphans 

rm ./test/resources/data/test_db.db
rm -rf ./nets/data