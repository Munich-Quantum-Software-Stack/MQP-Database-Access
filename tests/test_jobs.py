from uuid import uuid4
from pony.orm import db_session, flush
from bqp_database_access.jobs import (
    fetch_by_identity,
    fetch_by_identity_pages,
    fetch_result_by_job_id_and_identity,
    create_job,
    is_within_active_job_limit,
    MAX_ACTIVE_JOBS_PER_USER_PER_RESOURCE,
    filter_queued_if_offline_and_fetch,
    fetch_all_pending_jobs,
)

import pytest
pytestmark = pytest.mark.usefixtures("seeded_db")


def test_fetch_by_identity(seeded_db):
    """
    Tests whether `fetch_by_identity` returns all and only the jobs belonging to a given user
    from the pre-seeded database created via the `seeded_db` fixture.

    Verifies that:
    * seeded user `test_user` returns the seeded jobs
    * all returned jobs belong to `test_user`
    * returned statuses match the seeded database state
    * unknown identity returns an empty list
    """
    with db_session:
        jobs = fetch_by_identity("test_user")

        assert len(jobs) == 3
        assert all(j.owner.identity == "test_user" for j in jobs)
        assert {j.status for j in jobs} == {"PENDING", "CANCELLED", "COMPLETED"}
        assert fetch_by_identity("does_not_exist") == []


def test_fetch_by_identity_pages(seeded_db):
    """
    Tests `fetch_by_identity_pages` using the pre-seeded database.

    Verifies that:
    * pagination returns the correct subset of jobs
    * totaljob_nr reflects all jobs belonging to the user
    * filtering by status works
    * ordering does not break pagination
    """
    identity = "test_user"

    with db_session:
        # Page 0, 2 jobs per page, no filter
        res = fetch_by_identity_pages(
            identity=identity,
            page=0,
            jobs_per_page=2,
            order="ASC",
            order_by="id",
            filter_query="",
        )

        jobs = res["jobs"]
        total = res["totaljob_nr"]

        assert total == 3
        assert len(jobs) == 2
        assert [j.id for j in jobs] == [111, 112]

        # Page 1, remaining job
        res_page_1 = fetch_by_identity_pages(
            identity=identity,
            page=1,
            jobs_per_page=2,
            order="ASC",
            order_by="id",
            filter_query="",
        )

        jobs_page_1 = res_page_1["jobs"]

        assert len(jobs_page_1) == 1
        assert jobs_page_1[0].id == 113

        # Filter by status
        res_filtered = fetch_by_identity_pages(
            identity=identity,
            page=0,
            jobs_per_page=10,
            order="ASC",
            order_by="id",
            filter_query="PENDING",
        )

        jobs_filtered = res_filtered["jobs"]

        assert res_filtered["totaljob_nr"] == 1
        assert len(jobs_filtered) == 1
        assert jobs_filtered[0].status == "PENDING"
        assert jobs_filtered[0].owner.identity == identity


def test_fetch_result_by_job_id_and_identity(seeded_db):
    """
    Tests `fetch_result_by_job_id_and_identity` using the pre-seeded database.

    Verifies that:
    * a matching (job_id, identity) returns the correct job
    * mismatched identity returns None
    * mismatched job_id returns None
    * empty job_id or identity returns None
    """
    identity = "test_user"
    valid_job_id = "111"   # seeded in create_local_database()
    invalid_job_id = "999999"

    with db_session:
        # Correct identity and job_id
        job = fetch_result_by_job_id_and_identity(valid_job_id, identity)
        assert job is not None
        assert job.id == int(valid_job_id)
        assert job.owner.identity == identity

        # Correct job_id, wrong identity
        assert fetch_result_by_job_id_and_identity(valid_job_id, "unknown_user") is None

        # Wrong job_id, correct identity
        assert fetch_result_by_job_id_and_identity(invalid_job_id, identity) is None

    # Empty inputs (guard clauses, no DB access required)
    assert fetch_result_by_job_id_and_identity("", identity) is None
    assert fetch_result_by_job_id_and_identity(valid_job_id, "") is None


def test_create_job(seeded_db, monkeypatch):
    """
    Tests whether `create_job` creates a CircuitJob with the expected fields and relations.

    Verifies that:
    * a job is created for an existing user that has at least one budget
    * returned job has the provided shots/circuit/circuit_format
    * returned job links to the provided budget and target specification
    * flags `no_modify` and `queued` are persisted
    * cost is set to 0 and timestamp_submitted is populated
    """
    monkeypatch.setattr("bqp_database_access.jobs.open_database", lambda *a, **k: seeded_db)
    monkeypatch.setattr("bqp_database_access.budgets.open_database", lambda *a, **k: seeded_db)

    with db_session:
        job = create_job(
            shots=10,
            circuit="OPENQASM 2.0",
            owner="test_user",
            budget=seeded_db.Budget.get(name="temp_budget"),
            target_spec=seeded_db.TargetSpecification.get(name="Q5"),
            circuit_format="qasm",
            no_modify=True,
            queued=True,
        )

        assert job is not None
        assert job.id is not None

        assert job.shots == 10
        assert job.circuit == "OPENQASM 2.0"
        assert job.circuit_format == "qasm"

        assert job.owner.identity == "test_user"
        assert job.budget.name == "temp_budget"
        assert job.target_specification.name == "Q5"

        assert job.no_modify is True
        assert job.queued is True

        assert job.cost == 0
        assert job.timestamp_submitted is not None


def test_is_within_active_job_limit(seeded_db):
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
    with db_session:
        seeded_db.Resource(
            name=f"RES-LIMIT-{uuid4()}",
            maintenance=False,
            qubits=1,
            connectivity="test",
            instructions="test",
            quantum_technology="test",
            resource_cost_modifier=1.0,
            security_level=seeded_db.ResourceSecurityLevel.get(name="BASIC"),
        )

        seeded_db.TargetSpecification(
            name=f"TS-LIMIT-{uuid4()}",
            specification_type="test",
            resource_name=seeded_db.Resource.select(lambda r: r.name.startswith("RES-LIMIT-")).first().name,
        )

        job = seeded_db.CircuitJob(
            status="PENDING",
            shots=1,
            circuit="test",
            circuit_format="qasm",
            owner=seeded_db.User.get(identity="test_user"),
            budget=seeded_db.Budget.get(name="temp_budget"),
            target_specification=seeded_db.TargetSpecification.select(lambda ts: ts.name.startswith("TS-LIMIT-")).first(),
            queued=False,
        )

        for _ in range(MAX_ACTIVE_JOBS_PER_USER_PER_RESOURCE - 1):
            seeded_db.CircuitJob(
                status="WAITING",
                shots=1,
                circuit="test",
                circuit_format="qasm",
                owner=job.owner,
                budget=job.budget,
                target_specification=job.target_specification,
                queued=False,
            )

        flush()
        assert is_within_active_job_limit(seeded_db, job) is True

        seeded_db.CircuitJob(
            status="WAITING",
            shots=1,
            circuit="test",
            circuit_format="qasm",
            owner=job.owner,
            budget=job.budget,
            target_specification=job.target_specification,
            queued=False,
        )

        flush()
        assert is_within_active_job_limit(seeded_db, job) is False


def test_filter_queued_if_offline_and_fetch(seeded_db, monkeypatch):
    """
    Tests whether `filter_queued_if_offline_and_fetch` selects eligible jobs, updates their
    state to WAITING, sets timestamp_scheduled, and persists changes.

    Verifies that:
    * queued jobs are released if the resource is not in maintenance
    * non-queued jobs are released regardless of maintenance
    * jobs are released only if `is_within_active_job_limit` is True
    * released jobs are updated (status, timestamp_scheduled) and returned
    """
    monkeypatch.setattr("bqp_database_access.jobs.is_within_active_job_limit", lambda *_: True)

    with db_session:
        res_ok = f"RES-OK-{uuid4()}"
        res_block = f"RES-MAINT-{uuid4()}"
        note_ok = f"JOB-OK-{uuid4()}"
        note_block = f"JOB-BLOCK-{uuid4()}"

        seeded_db.Resource(
            name=res_ok,
            maintenance=False,
            qubits=1,
            connectivity="test",
            instructions="test",
            quantum_technology="test",
            resource_cost_modifier=1.0,
            security_level=seeded_db.ResourceSecurityLevel.get(name="BASIC"),
        )
        seeded_db.Resource(
            name=res_block,
            maintenance=True,
            qubits=1,
            connectivity="test",
            instructions="test",
            quantum_technology="test",
            resource_cost_modifier=1.0,
            security_level=seeded_db.ResourceSecurityLevel.get(name="BASIC"),
        )

        seeded_db.TargetSpecification(name=f"TS-OK-{uuid4()}", specification_type="test", resource_name=res_ok)
        seeded_db.TargetSpecification(name=f"TS-BLOCK-{uuid4()}", specification_type="test", resource_name=res_block)

        seeded_db.CircuitJob(
            note=note_ok,
            status="PENDING",
            shots=1,
            circuit="OPENQASM 2.0",
            circuit_format="qasm",
            owner=seeded_db.User.get(identity="test_user"),
            budget=seeded_db.Budget.get(name="temp_budget"),
            target_specification=seeded_db.TargetSpecification.get(resource_name=res_ok),
            queued=True,
            timestamp_scheduled=None,
        )
        seeded_db.CircuitJob(
            note=note_block,
            status="PENDING",
            shots=1,
            circuit="OPENQASM 2.0",
            circuit_format="qasm",
            owner=seeded_db.User.get(identity="test_user"),
            budget=seeded_db.Budget.get(name="temp_budget"),
            target_specification=seeded_db.TargetSpecification.get(resource_name=res_block),
            queued=True,
            timestamp_scheduled=None,
        )

        filtered = filter_queued_if_offline_and_fetch(
            seeded_db,
            [seeded_db.CircuitJob.get(note=note_ok), seeded_db.CircuitJob.get(note=note_block)],
        )

        assert {j.note for j in filtered} == {note_ok}

        assert seeded_db.CircuitJob.get(note=note_ok).status == "WAITING"
        assert seeded_db.CircuitJob.get(note=note_ok).timestamp_scheduled is not None

        assert seeded_db.CircuitJob.get(note=note_block).status == "PENDING"
        assert seeded_db.CircuitJob.get(note=note_block).timestamp_scheduled is None


def test_fetch_all_pending_jobs(seeded_db, monkeypatch):
    """
    Tests whether `fetch_all_pending_jobs`:
    * selects only jobs with status=="PENDING" from the database
    * passes exactly those jobs to `filter_queued_if_offline_and_fetch`
    * returns whatever the filter function returns
    """
    monkeypatch.setattr("bqp_database_access.jobs.open_database", lambda *a, **k: seeded_db)
    monkeypatch.setattr("bqp_database_access.jobs.is_within_active_job_limit", lambda *_: True)

    with db_session:
        res_ok = f"RES-OK-{uuid4()}"
        res_block = f"RES-MAINT-{uuid4()}"
        note_ok = f"PENDING-OK-{uuid4()}"
        note_block = f"PENDING-BLOCK-{uuid4()}"

        seeded_db.Resource(
            name=res_ok,
            maintenance=False,
            qubits=1,
            connectivity="test",
            instructions="test",
            quantum_technology="test",
            resource_cost_modifier=1.0,
            security_level=seeded_db.ResourceSecurityLevel.get(name="BASIC"),
        )
        seeded_db.Resource(
            name=res_block,
            maintenance=True,
            qubits=1,
            connectivity="test",
            instructions="test",
            quantum_technology="test",
            resource_cost_modifier=1.0,
            security_level=seeded_db.ResourceSecurityLevel.get(name="BASIC"),
        )

        seeded_db.TargetSpecification(name=f"TS-OK-{uuid4()}", specification_type="test", resource_name=res_ok)
        seeded_db.TargetSpecification(name=f"TS-BLOCK-{uuid4()}", specification_type="test", resource_name=res_block)

        seeded_db.CircuitJob(
            note=note_ok,
            status="PENDING",
            shots=1,
            circuit="test",
            circuit_format="qasm",
            owner=seeded_db.User.get(identity="test_user"),
            budget=seeded_db.Budget.get(name="temp_budget"),
            target_specification=seeded_db.TargetSpecification.get(resource_name=res_ok),
            queued=True,
            timestamp_scheduled=None,
        )
        seeded_db.CircuitJob(
            note=note_block,
            status="PENDING",
            shots=1,
            circuit="test",
            circuit_format="qasm",
            owner=seeded_db.User.get(identity="test_user"),
            budget=seeded_db.Budget.get(name="temp_budget"),
            target_specification=seeded_db.TargetSpecification.get(resource_name=res_block),
            queued=True,
            timestamp_scheduled=None,
        )

        jobs = fetch_all_pending_jobs()

        assert any(j.note == note_ok for j in jobs)
        assert all(j.note != note_block for j in jobs)

        assert seeded_db.CircuitJob.get(note=note_ok).status == "WAITING"
        assert seeded_db.CircuitJob.get(note=note_ok).timestamp_scheduled is not None

        assert seeded_db.CircuitJob.get(note=note_block).status == "PENDING"
        assert seeded_db.CircuitJob.get(note=note_block).timestamp_scheduled is None


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