# MutCompute 2.0 - MLaaS for Protein Engineering

## Run in Production
First create a `.env` file with the correct values for the following:

|Name | Description|
|-----|-------------|
|SES_EMAIL_HOST| Host for SMTP service|
|SES_EMAIL_PORT| Port for the SMTP service|
|SES_SMTP_USERNAME| Username for the SMTP service|
|SES_SMTP_PASSWORD| Password for the SMTP service|
|DB_URI_NN_API| The URI for the sqlite DB in the NN API service|
|DB_URI_BACKEND| The URI for the sqlite DB in the backend API service|
|DB_NN_TABLE| The table name for the NN predictions|
|HOSTNAME| The hostname for mutcompute|
|PORT| The port for mutcompute|

Then, run the following command:

`$ docker compose up`

## Run tests
No need to have a `.env` file-- in fact, you should not use it at all.  To run the integration tests, simply run the following command:

`$ ./run_tests.sh`

This will do the following:
1. Create a test sqlite database
2. Start up mutcompute using the test database
3. Run pytests
4. Shut down mutcompute
5. Delete the database and remove any extra files