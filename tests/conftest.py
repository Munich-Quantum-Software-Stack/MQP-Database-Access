import pytest
import os
from bqp_database_access._database import open_database
import bqp_database_access as database_access
from pony.orm import db_session
from pony.orm import count
from pony.orm import TransactionError
from pony.orm import select
from werkzeug.datastructures import Headers
from pathlib import Path
import datetime; now = datetime.datetime.now()


os.environ.update(
    {
        "QUANTUM_DB_HOST": "quantum_db",
        "QUANTUM_DB_PORT": "5432",
        "QUANTUM_DB_USER": "postgres",
        "QUANTUM_DB_PASS": "example",
        "QUANTUM_DB_NAME": "postgres",
    }
)


def create_local_database():
    db = open_database(create_tables=True)

    db.drop_all_tables(with_all_data=True)
    db.create_tables()

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
                "test_user2", "test_password", "BASIC", "test@lrz.de", "LRZ", "QUANTUM"
            )

            database_access.users.create_new_user_with_secret(
                "mqp_edu_test_user", "test_password", "BASIC", "mqp_edu_test@lrz.de", "LRZ", "QUANTUM"
            )

            quantum_db = open_database()
            quantum_db.insert("budget", name="temp_budget", note=' ', owner="test_user", credits=1000)

            user = quantum_db.User.get(identity="test_user")
            user2 = quantum_db.User.get(identity="test_user2")
            budget = quantum_db.Budget.get(name="temp_budget")
            group = quantum_db.UserGroup.get(name="TEST_USER_GROUP")
            if group is None:
                group = quantum_db.UserGroup(
                    name="TEST_USER_GROUP",
                    note="Group granting test_user access to temp_budget (seeded for tests)",
                    owner=user,
                    cost_modifier=1.0,
                )
            user.user_groups.add(group)
            user2.user_groups.add(group)
            budget.user_groups.add(group)

            quantum_db.insert("resource_security_level", name="BASIC", note=' ', job_min_interval=10, budget_max_per_job=10, unique_token_required=False, token_max_lifetime=10)
            
            quantum_db.insert("resource", name="Q5", note=" ", maintenance=False, qubits=5, connectivity=" ", instructions=" ", quantum_technology=" ", num_queued_jobs=1, resource_cost_modifier=1, security_level="BASIC")
            quantum_db.insert("resource", name="Q4", note=" ", maintenance=True, qubits=5, connectivity=" ", instructions=" ", quantum_technology=" ", num_queued_jobs=1, resource_cost_modifier=1, security_level="BASIC")
            
            quantum_db.insert("target_specification", name="TS_Q5", note=' ', specification_type=' ', minimum_qubits="1", quantum_technology=' ', resource_name="Q5")
            quantum_db.insert("target_specification", name="TS_Q4", note=' ', specification_type=' ', minimum_qubits="1", quantum_technology=' ', resource_name="Q4")

            quantum_db.insert(
                "circuit_job",
                id=201,
                note="JOB_PENDING_QUEUED_Q5",
                status="PENDING",
                shots=1,
                circuit="OPENQASM 2.0;",
                circuit_format="qasm",
                no_modify=True,
                timestamp_submitted=now,
                timestamp_scheduled=None,
                timestamp_completed=None,
                cost=0,
                result='{"10": 76, "11": 425, "01": 91, "00": 408}',
                owner="test_user2",
                budget="temp_budget",
                executed_resource="Q5",
                target_specification="TS_Q5",
                executed_circuit="OPENQASM 2.0;",
                queued=True,
            )
            quantum_db.insert(
                "circuit_job",
                id=202,
                note="JOB_PENDING_QUEUED_Q4",
                status="PENDING",
                shots=1,
                circuit="OPENQASM 2.0;",
                circuit_format="qasm",
                no_modify=True,
                timestamp_submitted=now,
                timestamp_scheduled=None,
                timestamp_completed=None,
                cost=0,
                result='{"10": 76, "11": 425, "01": 91, "00": 408}',
                owner="test_user2",
                budget="temp_budget",
                executed_resource="Q4",
                target_specification="TS_Q4",
                executed_circuit="OPENQASM 2.0;",
                queued=True,
            )

            quantum_db.insert("circuit_job", id=111, note=" ", status="PENDING", shots=200, circuit="OPENQASM 2.0;", circuit_format="qasm", no_modify=True, timestamp_submitted=now, timestamp_scheduled= None, timestamp_completed=" 2024-07-17 11:17:32.397618", cost=0, result='{"10": 76, "11": 425, "01": 91, "00": 408}', owner="test_user", budget="temp_budget", executed_resource="Q5", target_specification="TS_Q5", executed_circuit="OPENQASM 2.0;", queued=False)
            quantum_db.insert("circuit_job", id=112, note=" ", status="CANCELLED", shots=200, circuit="OPENQASM 2.0;", circuit_format="qasm", no_modify=True, timestamp_submitted="2024-07-17 11:17:32.397618", timestamp_scheduled=" 2024-07-17 11:17:32.397618", timestamp_completed=" 2024-07-17 11:17:32.397618", cost=0, result='{"10": 76, "11": 425, "01": 91, "00": 408}', owner="test_user", budget="temp_budget", executed_resource="Q5", target_specification="TS_Q5", executed_circuit="OPENQASM 2.0;", queued=True)
            quantum_db.insert("circuit_job", id=113, note=" ", status="COMPLETED", shots=200, circuit="OPENQASM 2.0;", circuit_format="qasm", no_modify=True, timestamp_submitted="2024-07-17 11:17:32.397618", timestamp_scheduled=" 2024-07-17 11:17:32.397618", timestamp_completed=" 2024-07-17 11:17:32.397618", cost=0, result='{"10": 76, "11": 425, "01": 91, "00": 408}', owner="test_user", budget="temp_budget", executed_resource="Q5", target_specification="TS_Q5", executed_circuit="OPENQASM 2.0;", queued=True)

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

@pytest.fixture(scope="function")
def active_job_limit_db(seeded_db):
    """Seed dedicated jobs used by `test_is_within_active_job_limit`.

    Creates one subject job plus two WAITING jobs on the same
    (owner, target_specification), and several noise jobs that must not be
    counted by `is_within_active_job_limit`.
    """
    with db_session:
        now_local = datetime.datetime.now()
        budget = seeded_db.Budget.get(name="temp_budget")
        target_q5 = seeded_db.TargetSpecification.get(name="TS_Q5")
        target_q4 = seeded_db.TargetSpecification.get(name="TS_Q4")

        assert budget is not None
        assert target_q5 is not None
        assert target_q4 is not None

        seeded_db.CircuitJob(
            id=901,
            note="fixture_subject",
            status="PENDING",
            shots=32,
            circuit="OPENQASM 2.0;",
            circuit_format="qasm",
            no_modify=False,
            timestamp_submitted=now_local,
            timestamp_scheduled=None,
            timestamp_completed=None,
            cost=0,
            result="",
            owner="test_user",
            budget=budget,
            executed_resource="Q5",
            target_specification=target_q5,
            executed_circuit="",
            queued=False,
        )

        seeded_db.CircuitJob(
            id=902,
            note="fixture_waiting_1",
            status="WAITING",
            shots=32,
            circuit="OPENQASM 2.0;",
            circuit_format="qasm",
            no_modify=False,
            timestamp_submitted=now_local,
            timestamp_scheduled=now_local,
            timestamp_completed=None,
            cost=0,
            result="",
            owner="test_user",
            budget=budget,
            executed_resource="Q5",
            target_specification=target_q5,
            executed_circuit="",
            queued=False,
        )

        seeded_db.CircuitJob(
            id=903,
            note="fixture_waiting_2",
            status="WAITING",
            shots=32,
            circuit="OPENQASM 2.0;",
            circuit_format="qasm",
            no_modify=False,
            timestamp_submitted=now_local,
            timestamp_scheduled=now_local,
            timestamp_completed=None,
            cost=0,
            result="",
            owner="test_user",
            budget=budget,
            executed_resource="Q5",
            target_specification=target_q5,
            executed_circuit="",
            queued=False,
        )

        # Noise jobs that must be ignored by the active-job-limit check
        seeded_db.CircuitJob(
            id=904,
            note="fixture_noise_other_user",
            status="WAITING",
            shots=32,
            circuit="OPENQASM 2.0;",
            circuit_format="qasm",
            no_modify=False,
            timestamp_submitted=now_local,
            timestamp_scheduled=now_local,
            timestamp_completed=None,
            cost=0,
            result="",
            owner="test_user2",
            budget=budget,
            executed_resource="Q5",
            target_specification=target_q5,
            executed_circuit="",
            queued=False,
        )

        seeded_db.CircuitJob(
            id=905,
            note="fixture_noise_other_target",
            status="WAITING",
            shots=32,
            circuit="OPENQASM 2.0;",
            circuit_format="qasm",
            no_modify=False,
            timestamp_submitted=now_local,
            timestamp_scheduled=now_local,
            timestamp_completed=None,
            cost=0,
            result="",
            owner="test_user",
            budget=budget,
            executed_resource="Q4",
            target_specification=target_q4,
            executed_circuit="",
            queued=False,
        )

        seeded_db.CircuitJob(
            id=906,
            note="fixture_noise_non_waiting",
            status="COMPLETED",
            shots=32,
            circuit="OPENQASM 2.0;",
            circuit_format="qasm",
            no_modify=False,
            timestamp_submitted=now_local,
            timestamp_scheduled=now_local,
            timestamp_completed=now_local,
            cost=0,
            result="{}",
            owner="test_user",
            budget=budget,
            executed_resource="Q5",
            target_specification=target_q5,
            executed_circuit="",
            queued=False,
        )

    yield seeded_db


@pytest.fixture(scope="function")
def seeded_db(tmp_path, monkeypatch):
    db_file = tmp_path / "quantum_test.sqlite"
    monkeypatch.setenv("BQP_DB_FILENAME", str(db_file))

    create_local_database()

    db = open_database()
    yield db
    db.disconnect()


@pytest.fixture
def empty_db(tmp_path, monkeypatch):
    db_file = tmp_path / "empty.sqlite"
    monkeypatch.setenv("BQP_DB_FILENAME", str(db_file))
    db = open_database(create_tables=True)
    yield db
    db.disconnect()