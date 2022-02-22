
CREATE TABLE "NN_Query" (
	id INTEGER NOT NULL, 
	user_email INTEGER, 
	pdb_query VARCHAR(8), 
	query_time DATETIME NOT NULL, 
	query_inf TEXT(4294000000), 
	query_email_sent BOOLEAN, 
	PRIMARY KEY (id), 
	CHECK (NOT(pdb_query IS NULL AND query_inf IS NULL)), 
	FOREIGN KEY(user_email) REFERENCES "Users" (email), 
	CHECK (query_email_sent IN (0, 1))
);

CREATE TABLE "Users" (
	id INTEGER NOT NULL, 
	first_name VARCHAR(20) NOT NULL, 
	last_name VARCHAR(20) NOT NULL, 
	email VARCHAR(80) NOT NULL, 
	password VARCHAR(25) NOT NULL, 
	organization VARCHAR(50) NOT NULL, 
	registered_on DATETIME NOT NULL, confirmation_link_sent_on DATETIME, email_confirmed BOOLEAN, email_confirmed_on DATETIME, 
	PRIMARY KEY (id)
);

CREATE INDEX "ix_NN_Query_query_time" ON "NN_Query" (query_time);

CREATE UNIQUE INDEX "ix_Users_email" ON "Users" (email);

INSERT INTO "main"."Users" ("id", "first_name", "last_name", "email", "password", "organization", "registered_on", "confirmation_link_sent_on", "email_confirmed", "email_confirmed_on") VALUES ('1', 'James', 'Loy', 'jamesmadiganloy@gmail.com', '$2b$12$M2Xq663pFpUSehM46/2GBek3iHL4XdPFNMgNAJQubC.NZ3K3PP3rW', 'Me', '2022-02-21 00:08:22.852200', '', '1', '2022-02-21 00:09:04.424646');