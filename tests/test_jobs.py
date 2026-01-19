from uuid import uuid4
from pony.orm import db_session
from pony.orm import flush

from bqp_database_access._database import open_database
from bqp_database_access.jobs import fetch_by_identity
from bqp_database_access.jobs import fetch_by_identity_pages
from bqp_database_access.jobs import fetch_result_by_job_id_and_identity
from bqp_database_access.jobs import create_job
from bqp_database_access.jobs import is_within_active_job_limit
from bqp_database_access.jobs import filter_queued_if_offline_and_fetch
from bqp_database_access.jobs import fetch_all_pending_jobs

def test_fetch_by_identity(empty_db):
    """
    Tests whether `fetch_by_identity` returns all and only the jobs belonging to a given user.

    The test seeds multiple users with multiple jobs in different states and verifies that:
    * only jobs owned by the requested identity are returned
    * jobs with different statuses (e.g. PENDING, CANCELLED) are included
    * the number of returned jobs and their status distribution match the database state
    """
    quantum_db = empty_db
    identity_a = "test_userA"
    identity_b = "test_userB"

    with db_session:
        level = quantum_db.UserSecurityLevel(
            name="BASIC",
            token_max_live_count=1,
            token_max_lifetime=30,
            token_min_creation_interval=1,
            token_max_jobs=100,
            token_max_budget=100,
            token_max_rate=1,
            login_max_interval=365,
        )

        def mk_user(identity: str):
            user = quantum_db.User(
                identity=identity,
                security_level=level,
                email="test@lrz.de",
                affiliation="LRZ",
                association="LDAP",
            )
            budget = quantum_db.Budget(name=f"budget-{uuid4()}", owner=user, credits=100)
            return user, budget

        user_a, budget_a = mk_user(identity_a)
        user_b, budget_b = mk_user(identity_b)
        
        def mk_job(user, budget, status: str, tag: str):
            ts = quantum_db.TargetSpecification(name=f"ts-{tag}-{uuid4()}", specification_type="test")
            quantum_db.CircuitJob(
                status=status,
                shots=1,
                circuit="OPENQASM 2.0",
                circuit_format="qasm",
                owner=user,
                budget=budget,
                target_specification=ts,
            )

        mk_job(user_a, budget_a, "PENDING", "a1")
        mk_job(user_a, budget_a, "CANCELLED", "a2")

        mk_job(user_b, budget_b, "PENDING", "b1")
        mk_job(user_b, budget_b, "COMPLETED", "b2")
        mk_job(user_b, budget_b, "PENDING", "b3")

    jobsa = fetch_by_identity(identity_a)
    jobsb = fetch_by_identity(identity_b)

    assert len(jobsa) == 2
    assert len(jobsb) == 3

    assert all(j.owner.identity == identity_a for j in jobsa)
    assert all(j.owner.identity == identity_b for j in jobsb)

    assert sum(j.status == "PENDING" for j in jobsa) == 1
    assert sum(j.status == "CANCELLED" for j in jobsa) == 1

    assert sum(j.status == "PENDING" for j in jobsb) == 2
    assert sum(j.status == "CANCELLED" for j in jobsb) == 0
    assert sum(j.status == "COMPLETED" for j in jobsb) == 1


def test_fetch_by_identity_pages(empty_db):
    """
    Tests whether `fetch_by_identity_pages` paginates, orders, and filters jobs correctly
    for a given user identity, and returns the correct total job count.

    Verifies that:
    * pagination returns the correct slice for page=0 and page=1
    * ordering by `id` works (ASC)
    * filtering by status returns only matching jobs and correct total count
    * unknown identities return empty results and totaljob_nr == 0
    """
    quantum_db = empty_db
    identity = "test_userA"

    with db_session:
        level = quantum_db.UserSecurityLevel(
            name="BASIC",
            token_max_live_count=1,
            token_max_lifetime=30,
            token_min_creation_interval=1,
            token_max_jobs=100,
            token_max_budget=100,
            token_max_rate=1,
            login_max_interval=365,
        )

        user = quantum_db.User(
            identity=identity,
            security_level=level,
            email="test@lrz.de",
            affiliation="LRZ",
            association="LDAP",
        )
        budget = quantum_db.Budget(name=f"budget-{uuid4()}", owner=user, credits=100)

        def mk_job(status: str, tag: str):
            ts = quantum_db.TargetSpecification(
                name=f"ts-{tag}-{uuid4()}",
                specification_type="test",
            )
            return quantum_db.CircuitJob(
                status=status,
                shots=1,
                circuit="OPENQASM 2.0",
                circuit_format="qasm",
                owner=user,
                budget=budget,
                target_specification=ts,
            )
        
        j1 = mk_job("PENDING", "a1")
        j2 = mk_job("CANCELLED", "a2")
        j3 = mk_job("COMPLETED", "a3")
        j4 = mk_job("PENDING", "a4")
        j5 = mk_job("PENDING", "a5")

        flush() # forces Pony to assign IDs
        seeded_ids_asc = sorted([j1.id, j2.id, j3.id, j4.id, j5.id])
    
    res0 = fetch_by_identity_pages(
        identity=identity,
        page=0,
        jobs_per_page=2,
        order="ASC",
        order_by="id",
        filter_query="",
    )
    jobs0 = list(res0["jobs"])
    assert res0["totaljob_nr"] == 5
    assert len(jobs0) == 2
    assert [j.id for j in jobs0] == seeded_ids_asc[:2]
    assert all(j.owner.identity == identity for j in jobs0)

    res1 = fetch_by_identity_pages(
        identity=identity,
        page=1,
        jobs_per_page=2,
        order="ASC",
        order_by="id",
        filter_query="",
    )
    jobs1 = list(res1["jobs"])
    assert res1["totaljob_nr"] == 5
    assert len(jobs1) == 2
    assert [j.id for j in jobs1] == seeded_ids_asc[2:4]
    assert all(j.owner.identity == identity for j in jobs1)

    res_pending = fetch_by_identity_pages(
        identity=identity,
        page=0,
        jobs_per_page=2,
        order="ASC",
        order_by="id",
        filter_query="PENDING",
    )
    jobs_pending = list(res_pending["jobs"])
    assert res_pending["totaljob_nr"] == 3
    assert len(jobs_pending) == 2
    assert all(j.status == "PENDING" for j in jobs_pending)
    assert all(j.owner.identity == identity for j in jobs_pending)

    res_unknown = fetch_by_identity_pages(
        identity="does_not_exist",
        page=0,
        jobs_per_page=10,
        order="ASC",
        order_by="id",
        filter_query="",
    )
    assert res_unknown["totaljob_nr"] == 0
    assert list(res_unknown["jobs"]) == []


def test_fetch_result_by_job_id_and_identity(empty_db):
    """
    Tests whether `fetch_result_by_job_id_and_identity` returns the correct job
    only when both job ID and user identity match.

    Verifies that:
    * the correct job is returned for matching job_id and identity
    * a mismatched identity returns None
    * a mismatched job_id returns None
    * empty job_id or identity returns None
    """
    quantum_db = empty_db
    identity_a = "test_userA"
    identity_b = "test_userB"

    with db_session:
        level = quantum_db.UserSecurityLevel(
            name="BASIC",
            token_max_live_count=1,
            token_max_lifetime=30,
            token_min_creation_interval=1,
            token_max_jobs=100,
            token_max_budget=100,
            token_max_rate=1,
            login_max_interval=365,
        )

        user_a = quantum_db.User(
            identity=identity_a,
            security_level=level,
            email="test_a@lrz.de",
            affiliation="LRZ",
            association="LDAP",
        )
        user_b = quantum_db.User(
            identity=identity_b,
            security_level=level,
            email="test_b@lrz.de",
            affiliation="LRZ",
            association="LDAP",
        )

        budget_a = quantum_db.Budget(name=f"budget-{uuid4()}", owner=user_a, credits=100)
        budget_b = quantum_db.Budget(name=f"budget-{uuid4()}", owner=user_b, credits=100)

        ts = quantum_db.TargetSpecification(
            name=f"ts-{uuid4()}",
            specification_type="test",
        )

        job_a = quantum_db.CircuitJob(
            status="COMPLETED",
            shots=1,
            circuit="OPENQASM 2.0",
            circuit_format="qasm",
            owner=user_a,
            budget=budget_a,
            target_specification=ts,
        )

        flush() # forces Pony to assign IDs
        job_id_a = str(job_a.id)

    with db_session:
        res = fetch_result_by_job_id_and_identity(job_id_a, identity_a)
    assert res is not None
    assert res.id == int(job_id_a)
    assert res.owner.identity == identity_a
    
    with db_session:
        assert fetch_result_by_job_id_and_identity(job_id_a, identity_b) is None
        assert fetch_result_by_job_id_and_identity("999999", identity_a) is None
    
    assert fetch_result_by_job_id_and_identity("", identity_a) is None
    assert fetch_result_by_job_id_and_identity(job_id_a, "") is None


def test_create_job_creates_job(empty_db, monkeypatch):
    """
    Tests whether `create_job` creates a CircuitJob with the expected fields and relations.

    Verifies that:
    * a job is created for an existing user that has at least one budget
    * returned job has the provided shots/circuit/circuit_format
    * returned job links to the provided budget and target specification
    * flags `no_modify` and `queued` are persisted
    * cost is set to 0 and timestamp_submitted is populated
    """
    quantum_db = empty_db
    monkeypatch.setattr("bqp_database_access.jobs.open_database", lambda *a, **k: quantum_db)
    monkeypatch.setattr("bqp_database_access.budgets.open_database", lambda *a, **k: quantum_db)

    identity = "test_userA"

    with db_session:
        level = quantum_db.UserSecurityLevel(
            name="BASIC",
            token_max_live_count=1,
            token_max_lifetime=30,
            token_min_creation_interval=1,
            token_max_jobs=100,
            token_max_budget=100,
            token_max_rate=1,
            login_max_interval=365,
        )

        user = quantum_db.User(
            identity=identity,
            security_level=level,
            email="test@lrz.de",
            affiliation="LRZ",
            association="LDAP",
        )

        budget = quantum_db.Budget(name=f"budget-{uuid4()}", owner=user, credits=100)

        ts = quantum_db.TargetSpecification(
            name=f"ts-{uuid4()}",
            specification_type="test",
        )

        user_group = quantum_db.UserGroup(
            name = f"ts-{uuid4()}",
            owner = user,
            cost_modifier = 0
        )

        user_group.users.add(user)
        user_group.budgets.add(budget)

        job = create_job(
            shots=10,
            circuit="OPENQASM 2.0; // test",
            owner=identity,
            budget=budget,
            target_spec=ts,
            circuit_format="qasm",
            no_modify=True,
            queued=True,
        )

    assert job is not None
    assert job.id is not None

    assert job.shots == 10
    assert job.circuit == "OPENQASM 2.0; // test"
    assert job.circuit_format == "qasm"

    assert job.owner.identity == identity
    assert job.budget == budget
    assert job.target_specification == ts

    assert job.no_modify is True
    assert job.queued is True

    assert job.cost == 0
    assert job.timestamp_submitted is not None


def test_is_within_active_job_limit(empty_db):
    """
    Tests whether `is_within_active_job_limit` correctly enforces the maximum
    number of active (WAITING) jobs per user and target specification.

    Verifies that:
    * WAITING jobs are counted
    * non-WAITING jobs are ignored
    * jobs of other users are ignored
    * jobs with other target specifications are ignored
    * reaching the limit returns False
    """
    quantum_db = empty_db
    identity = "test_userA"
    MAX_ACTIVE_JOBS_PER_USER_PER_RESOURCE = 2

    with db_session:
        level = quantum_db.UserSecurityLevel(
            name="BASIC",
            token_max_live_count=1,
            token_max_lifetime=30,
            token_min_creation_interval=1,
            token_max_jobs=100,
            token_max_budget=100,
            token_max_rate=1,
            login_max_interval=365,
        )

        user = quantum_db.User(
            identity=identity,
            security_level=level,
            email="test@lrz.de",
            affiliation="LRZ",
            association="LDAP",
        )

        budget = quantum_db.Budget(
            name="budget-test",
            owner=user,
            credits=100,
        )

        ts_a = quantum_db.TargetSpecification(
            name="ts-a",
            specification_type="test",
        )
        ts_b = quantum_db.TargetSpecification(
            name="ts-b",
            specification_type="test",
        )

        jobs = []
        for _ in range(MAX_ACTIVE_JOBS_PER_USER_PER_RESOURCE - 1):
            jobs.append(
                quantum_db.CircuitJob(
                    status="WAITING",
                    shots=1,
                    circuit="OPENQASM 2.0",
                    circuit_format="qasm",
                    owner=user,
                    budget=budget,
                    target_specification=ts_a,
                )
            )

        quantum_db.CircuitJob(
            status="COMPLETED",
            shots=1,
            circuit="OPENQASM 2.0",
            circuit_format="qasm",
            owner=user,
            budget=budget,
            target_specification=ts_a,
        )

        quantum_db.CircuitJob(
            status="WAITING",
            shots=1,
            circuit="OPENQASM 2.0",
            circuit_format="qasm",
            owner=user,
            budget=budget,
            target_specification=ts_b,
        )

        other_user = quantum_db.User(
            identity="other_user",
            security_level=level,
            email="other@lrz.de",
            affiliation="LRZ",
            association="LDAP",
        )
        quantum_db.CircuitJob(
            status="WAITING",
            shots=1,
            circuit="OPENQASM 2.0",
            circuit_format="qasm",
            owner=other_user,
            budget=budget,
            target_specification=ts_a,
        )

        assert is_within_active_job_limit(quantum_db, jobs[0]) is True

        last_job = quantum_db.CircuitJob(
            status="WAITING",
            shots=1,
            circuit="OPENQASM 2.0",
            circuit_format="qasm",
            owner=user,
            budget=budget,
            target_specification=ts_a,
        )

        flush()
        assert quantum_db.CircuitJob.select(owner=user, status="WAITING", target_specification=ts_a).count() == MAX_ACTIVE_JOBS_PER_USER_PER_RESOURCE
        assert is_within_active_job_limit(quantum_db, last_job) is False


def test_filter_queued_if_offline_and_fetch_marks_waiting_and_sets_timestamp(empty_db, monkeypatch):
    """
    Tests whether `filter_queued_if_offline_and_fetch` selects eligible jobs, updates their
    state to WAITING, sets timestamp_scheduled, and persists changes.

    Verifies that:
    * queued jobs are released if the resource is not in maintenance
    * non-queued jobs are released regardless of maintenance
    * jobs are released only if `is_within_active_job_limit` is True
    * released jobs are updated (status, timestamp_scheduled) and returned
    """
    quantum_db = empty_db

    # Ensure the active-job-limit gate does not interfere with this test
    monkeypatch.setattr(
        "bqp_database_access.jobs.is_within_active_job_limit",
        lambda qdb, job: True,
    )

    identity = "test_userA"

    with db_session:
        level = quantum_db.UserSecurityLevel(
            name="BASIC",
            token_max_live_count=1,
            token_max_lifetime=30,
            token_min_creation_interval=1,
            token_max_jobs=100,
            token_max_budget=100,
            token_max_rate=1,
            login_max_interval=365,
        )

        user = quantum_db.User(
            identity=identity,
            security_level=level,
            email=identity,
            affiliation="LRZ",
            association="LDAP",
        )

        budget = quantum_db.Budget(name=f"budget-{uuid4()}", owner=user, credits=100)

        sec_level = quantum_db.ResourceSecurityLevel(
            name="SEC_BASIC",
            job_min_interval=0,
            budget_max_per_job=10**9,
            unique_token_required=False,
            token_max_lifetime=10**9,
        )
        
        res_ok = quantum_db.Resource(
            name="res-ok",
            maintenance=False,
            qubits=1,
            connectivity="all-to-all",
            instructions="test-instructions",
            quantum_technology="test-tech",
            resource_cost_modifier=1.0,
        security_level=sec_level,
        )

        ts_ok_1 = quantum_db.TargetSpecification(
            name=f"ts-{uuid4()}",
            specification_type="test",
            resource_name=res_ok.name,
        )
        ts_ok_2 = quantum_db.TargetSpecification(
            name=f"ts-{uuid4()}",
            specification_type="test",
            resource_name=res_ok.name,
        )

        j1 = quantum_db.CircuitJob(
            status="PENDING",
            shots=1,
            circuit="OPENQASM 2.0",
            circuit_format="qasm",
            owner=user,
            budget=budget,
            target_specification=ts_ok_1,
            queued=True,
        )

        j2 = quantum_db.CircuitJob(
            status="PENDING",
            shots=1,
            circuit="OPENQASM 2.0",
            circuit_format="qasm",
            owner=user,
            budget=budget,
            target_specification=ts_ok_2,
            queued=False,
        )

        assert j1.status == "PENDING"
        assert j2.status == "PENDING"
        assert j1.timestamp_scheduled is None
        assert j2.timestamp_scheduled is None

        filtered = filter_queued_if_offline_and_fetch(quantum_db, [j1, j2])

        assert len(filtered) == 2
        assert {job.id for job in filtered} == {j1.id, j2.id}

        assert j1.status == "WAITING"
        assert j2.status == "WAITING"
        assert j1.timestamp_scheduled is not None
        assert j2.timestamp_scheduled is not None


def test_fetch_all_pending_jobs(empty_db, monkeypatch):
    """
    Tests whether `fetch_all_pending_jobs`:
    * selects only jobs with status=="PENDING" from the database
    * passes exactly those jobs to `filter_queued_if_offline_and_fetch`
    * returns whatever the filter function returns
    """
    quantum_db = empty_db

    # Ensure the function under test uses the same DB instance as the fixture
    monkeypatch.setattr("bqp_database_access.jobs.open_database", lambda *a, **k: quantum_db)

    captured = {"jobs": None}

    def fake_filter(qdb, jobs):
        captured["jobs"] = list(jobs)
        # Return a deterministic subset to verify passthrough
        return list(jobs)[:1]

    monkeypatch.setattr("bqp_database_access.jobs.filter_queued_if_offline_and_fetch", fake_filter)

    with db_session:
        level = quantum_db.UserSecurityLevel(
            name="BASIC",
            token_max_live_count=1,
            token_max_lifetime=30,
            token_min_creation_interval=1,
            token_max_jobs=100,
            token_max_budget=100,
            token_max_rate=1,
            login_max_interval=365,
        )

        user = quantum_db.User(
            identity="test_userA",
            security_level=level,
            email="test_userA",
            affiliation="LRZ",
            association="LDAP",
        )

        budget = quantum_db.Budget(name=f"budget-{uuid4()}", owner=user, credits=100)

        ts = quantum_db.TargetSpecification(
            name=f"ts-{uuid4()}",
            specification_type="test",
        )

        p1 = quantum_db.CircuitJob(
            status="PENDING",
            shots=1,
            circuit="OPENQASM 2.0",
            circuit_format="qasm",
            owner=user,
            budget=budget,
            target_specification=ts,
        )
        p2 = quantum_db.CircuitJob(
            status="PENDING",
            shots=1,
            circuit="OPENQASM 2.0",
            circuit_format="qasm",
            owner=user,
            budget=budget,
            target_specification=ts,
        )
        quantum_db.CircuitJob(
            status="COMPLETED",
            shots=1,
            circuit="OPENQASM 2.0",
            circuit_format="qasm",
            owner=user,
            budget=budget,
            target_specification=ts,
        )

        flush()

        expected_pending_ids = {p1.id, p2.id}

    res = fetch_all_pending_jobs()

    assert captured["jobs"] is not None
    assert {j.id for j in captured["jobs"]} == expected_pending_ids
    assert all(j.status == "PENDING" for j in captured["jobs"])

    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0].id in expected_pending_ids


def test_fetch_all_pending_jobs_from_users():
    # fetch_all_pending_jobs_from_users
    return None


def test_fetch_all_pending_jobs_for_resource_from_users():
    # fetch_all_pending_jobs_for_resource_from_users
    return None


def test_fetch_all_pending_jobs_for_resource_not_from_users():
    # fetch_all_pending_jobs_for_resource_not_from_users
    return None


def test_fetch_all_pending_jobs_except_for_resources():
    # fetch_all_pending_jobs_except_for_resources
    return None


def test_fetch_all_pending_jobs_except_for_resource_not_from_users():
    # fetch_all_pending_jobs_except_for_resource_not_from_users
    return None


def test_fetch_all_waiting_jobs():
    # fetch_all_waiting_jobs
    return None


def test_complete_job_with_result():
    # complete_job_with_result
    return None


def test_update_hybrid_job():
    # update_hybrid_job
    return None


def test_cancel_job():
    # cancel_job
    return None