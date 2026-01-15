import pytest
import os
from bqp_database_access import create_app
from bqp_database_access._database import open_database
import bqp_database_access as database_access
from pony.orm import db_session
from pony.orm import count
from pony.orm import TransactionError
from pony.orm import select
from datetime import datetime
from http import HTTPStatus
from werkzeug.datastructures import Headers

from bqp_database_access._database import open_database


def delete_local_database() -> None:
    db = open_database()

    filename = getattr(db.provider.pool, "filename", None)
    if not filename:
        db.disconnect()
        return
    
    db.disconnect()
    os.remove(filename)

@pytest.fixture
def empty_db():
    db = open_database(create_tables=True)
    yield db
    db.disconnect()

    delete_local_database()

@pytest.fixture(scope="module")
def app():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )

    # other setup can go here
    create_local_database()

    yield app

    # clean up / reset resources here

    delete_local_database()

def create_local_database():
    db = open_database(create_tables=True)
    db.disconnect()

    try:
        with db_session:
            database_access.users.create_new_security_level(
                "BASIC",
                token_max_live_count=1,
                token_max_lifetime=30,
                token_min_creation_interval=1,
                token_max_jobs=100,
                token_max_budget=100,
                token_max_rate=1,
                login_max_interval=365,
            )

            database_access.users.create_new_user_with_secret(
                "test_user", "test_password", "BASIC", "test@lrz.de", "LRZ", "QUANTUM"
            )

            database_access.users.create_new_user_with_secret(
                "mqp_edu_test_user", "test_password", "BASIC", "mqp_edu_test@lrz.de", "LRZ", "QUANTUM"
            )

            quantum_db = open_database()
            quantum_db.insert("budget", name="temp_budget", note=' ', owner="test_user", credits=1000)

            quantum_db.insert("resource_security_level", name="BASIC", note=' ', job_min_interval=10, budget_max_per_job=10, unique_token_required=False, token_max_lifetime=10)

            quantum_db.insert("resource", name="Q5", note=" ", maintenance=False, qubits=5, connectivity=" ", instructions=" ", quantum_technology=" ", num_queued_jobs=1, resource_cost_modifier=1, security_level="BASIC")
            
            quantum_db.insert("target_specification", name="Q5", note=' ', specification_type=' ', minimum_qubits="1", quantum_technology=' ', resource_name="Q5")

            quantum_db.insert("circuit_job", id=111, note=" ", status="PENDING", shots=200, circuit="OPENQASM 2.0;", circuit_format="qasm", no_modify=True, timestamp_submitted="2024-07-17 11:17:32.397618", timestamp_scheduled=" 2024-07-17 11:17:32.397618", timestamp_completed=" 2024-07-17 11:17:32.397618", cost=0, result='{"10": 76, "11": 425, "01": 91, "00": 408}', owner="test_user", budget="temp_budget", executed_resource="Q5", target_specification="Q5", executed_circuit="OPENQASM 2.0;", queued=True)
            quantum_db.insert("circuit_job", id=112, note=" ", status="CANCELLED", shots=200, circuit="OPENQASM 2.0;", circuit_format="qasm", no_modify=True, timestamp_submitted="2024-07-17 11:17:32.397618", timestamp_scheduled=" 2024-07-17 11:17:32.397618", timestamp_completed=" 2024-07-17 11:17:32.397618", cost=0, result='{"10": 76, "11": 425, "01": 91, "00": 408}', owner="test_user", budget="temp_budget", executed_resource="Q5", target_specification="Q5", executed_circuit="OPENQASM 2.0;", queued=True)
            quantum_db.insert("circuit_job", id=113, note=" ", status="COMPLETED", shots=200, circuit="OPENQASM 2.0;", circuit_format="qasm", no_modify=True, timestamp_submitted="2024-07-17 11:17:32.397618", timestamp_scheduled=" 2024-07-17 11:17:32.397618", timestamp_completed=" 2024-07-17 11:17:32.397618", cost=0, result='{"10": 76, "11": 425, "01": 91, "00": 408}', owner="test_user", budget="temp_budget", executed_resource="Q5", target_specification="Q5", executed_circuit="OPENQASM 2.0;", queued=True)

            quantum_db.UserGroup(name="MQP_EDU", note="MQP_EDU group for testing purposes", owner="mqp_edu_test_user", cost_modifier=1)

            quantum_db.insert("users_in_user_groups", user="mqp_edu_test_user", usergroup="MQP_EDU")

            quantum_db.insert("user", identity="blocked_test_user", note=' ', email="test@lrz.de", affiliation="LRZ", association="LDAP", security_level="BASIC", blocked=True, block_reason="Testing blocked user", secret_hash="testing", force_secret_reset=True)
            quantum_db.commit()

            database_access.users.create_new_user_with_secret(
                "ldap_test_user",
                "test_password",
                "BASIC",
                "test@lrz.de",
                "LRZ",
                "LDAP",
            )

            database_access.users.create_new_ldap_user(
                "ldap_test_user", "BASIC", "ldaptest@lrz.de", "LRZ", "LDAP"
            )

    except TransactionError as error:
        pass


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def inactive_client(app):
    return app.test_client()


@pytest.fixture(scope="module")
def active_client(app):
    client = app.test_client()

    user_data = {"identity": "test_user", "secret": "test_password"}
    login_response = client.post("/login", json=user_data)

    assert (
        login_response.status_code == HTTPStatus.OK
        and login_response.json["access_token"] is not None
    )

    client.headers = Headers()
    client.headers.add("Content-Type", "application/json")
    client.headers.add("Authorization", "Bearer " + login_response.json["access_token"])

    return client

@pytest.fixture(scope="module")
def active_client_mqp_edu(app):
    client = app.test_client()

    user_data = {"identity": "mqp_edu_test_user","secret": "test_password"}
    login_response = client.post("/login", json=user_data)

    assert (
        login_response.status_code == HTTPStatus.OK
        and login_response.json["access_token"] is not None
    )

    client.headers = Headers()
    client.headers.add("Content-Type", "application/json")
    client.headers.add("Authorization", "Bearer " + login_response.json["access_token"])

    return client

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()