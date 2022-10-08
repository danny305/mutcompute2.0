import pytest
from uuid import uuid4
import sqlalchemy
from email.parser import Parser


class MockSMTPServer:
    def __init__(self):
        self.host = None
        self.port = None
        self.connect_calls = []
        self.starttls_calls = 0
        self.login_calls = []
        self.send_calls = []
        self.quit_calls = 0

    def __call__(self, host, port):
        self.host = host
        self.port = port
        return self

    def connect(self, host, port):
        self.connect_calls.append((host, port))

    def starttls(self):
        self.starttls_calls += 1

    def login(self, username, password):
        self.login_calls.append((username, password))

    def sendmail(self, from_name, recipient, msg):
        self.send_calls.append((from_name, recipient, msg))

    def quit(self):
        self.quit_calls += 1


class MockDf:
    def __init__(self):
        self.contents = uuid4()

    def to_csv(self, the_file):
        with open(the_file, "w") as f:
            f.write(str(self.contents))


@pytest.fixture(autouse=True)
def emails_patch(monkeypatch):
    monkeypatch.setattr(sqlalchemy, "create_engine", lambda x: None)

    def table(*args, **kwargs):
        return None

    monkeypatch.setattr(sqlalchemy, "Table", table)
    monkeypatch.setenv("SES_EMAIL_HOST", "some_host")
    monkeypatch.setenv("SES_EMAIL_PORT", "some_port")
    monkeypatch.setenv("SES_SMTP_USERNAME", "some_user")
    monkeypatch.setenv("SES_SMTP_PASSWORD", "some_pw")


def test_fail_email_nn(emails_patch, monkeypatch):
    from task import inference_fail_email
    import smtplib

    mock_server = MockSMTPServer()
    monkeypatch.setattr(smtplib, "SMTP", mock_server)

    user_email = "me@test.com"
    pdb_id = "1234"
    inference_fail_email(user_email, pdb_id)

    assert len(mock_server.send_calls) == 3
    for actual, expected in zip(
        mock_server.send_calls,
        [user_email, "danny.diaz@utexas.edu", "jamesmadiganloy@gmail.com"],
    ):
        assert actual[1] == expected

    assert mock_server.quit_calls == 1


def test_fail_email(emails_patch, monkeypatch):
    from task import inference_fail_email
    import smtplib

    mock_server = MockSMTPServer()
    monkeypatch.setattr(smtplib, "SMTP", mock_server)

    user_email = "me@test.com"
    pdb_id = "1234"
    inference_fail_email(user_email, pdb_id, problem="other_problem")

    assert len(mock_server.send_calls) == 1
    assert mock_server.send_calls[0][1] == "danny.diaz@utexas.edu"

    assert mock_server.quit_calls == 1


def test_success_email(emails_patch, monkeypatch):
    from task import inference_email
    import smtplib

    mock_server = MockSMTPServer()
    monkeypatch.setattr(smtplib, "SMTP", mock_server)

    user_email = "me@test.com"
    pdb_id = "1234"
    df = MockDf()
    inference_email(user_email, pdb_id, df)

    assert len(mock_server.send_calls) == 1
    assert mock_server.send_calls[0][1][0] == user_email
    assert mock_server.send_calls[0][1][1] == "danny.diaz@utexas.edu"
    assert mock_server.send_calls[0][1][2] == "jamesmadiganloy@gmail.com"

    p = Parser()
    msg = p.parsestr(mock_server.send_calls[0][2])
    assert msg.is_multipart()
    for part in msg.walk():
        if part.get_content_type() == "text/csv":
            assert part.get_payload() == str(df.contents)
