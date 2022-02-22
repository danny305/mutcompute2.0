import requests
import json
import pytest
import sqlite3
import time


@pytest.fixture(scope="session")
def auth_token():
    url = "http://localhost:5000/api/login"

    payload = json.dumps({
    "email": "jamesmadiganloy@gmail.com",
    "password": "password"
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    assert response.status_code == 200
    resp_json = response.json()
    assert "access_token" in resp_json
    return resp_json["access_token"]


def test_info():

    url = "http://localhost:5000/api"

    payload={}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    assert response.status_code == 200

def test_login():

    url = "http://localhost:5000/api/login"

    payload = json.dumps({
    "email": "jamesmadiganloy@gmail.com",
    "password": "password"
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    assert response.status_code == 200
    resp_json = response.json()
    assert "access_token" in resp_json

def test_predict_backend(auth_token):
    url = "http://localhost:5000/api/nn"

    payload = json.dumps({
    "loadCache": False,
    "id": "1B67"
    })
    headers = {
    'Authorization': f'Bearer {auth_token}',
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    assert response.status_code == 201
    con = sqlite3.connect("resources/data/test_db.db")

    t_start = time.time()
    t_elapsed = 0.0
    complete = False
    while t_elapsed < 150.0:
        t_elapsed = t_start - time.time()
        nn_queries = list(con.execute("SELECT * from NN_Query"))
        if nn_queries:
            complete = True
            break
        time.sleep(5)

    assert complete
    assert nn_queries[0][1] == "jamesmadiganloy@gmail.com"
    assert nn_queries[0][2] == "1B67"
