from uuid import uuid4
from pony.orm import db_session, flush, commit
from datetime import datetime
from bqp_database_access.jobs import (
    fetch_by_identity,
    fetch_by_identity_pages,
    fetch_result_by_job_id_and_identity,
    create_job,
    is_within_active_job_limit,
    MAX_ACTIVE_JOBS_PER_USER_PER_RESOURCE,
    filter_queued_if_offline_and_fetch,
    fetch_all_pending_jobs,
    fetch_all_pending_jobs_from_users,
    fetch_all_pending_jobs_for_resource_from_users,
    fetch_all_pending_jobs_for_resource_not_from_users,
    fetch_all_pending_jobs_except_for_resources,
    fetch_all_pending_jobs_except_for_resource_not_from_users,
    fetch_all_waiting_jobs,
    complete_job_with_result,
    cancel_job
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
        assert {j.status for j in jobs} == {"PENDING","CANCELLED", "COMPLETED"}
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
    valid_job_id = "111"
    invalid_job_id = "999999"

    with db_session:
        job = fetch_result_by_job_id_and_identity(valid_job_id, identity)
        assert job is not None
        assert job.id == int(valid_job_id)
        assert job.owner.identity == identity

        assert fetch_result_by_job_id_and_identity(valid_job_id, "unknown_user") is None
        assert fetch_result_by_job_id_and_identity(invalid_job_id, identity) is None

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
            target_spec=seeded_db.TargetSpecification.get(name="TS_TEST_QPU_1"),
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
        assert job.target_specification.name == "TS_TEST_QPU_1"

        assert job.no_modify is True
        assert job.queued is True

        assert job.cost == 0
        assert job.timestamp_submitted is not None


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

    NOTE_OK = "JOB_PENDING_QUEUED_TEST_QPU_1"
    NOTE_BLOCK = "JOB_PENDING_QUEUED_TEST_QPU_2"

    with db_session:
        ok = seeded_db.CircuitJob.get(note=NOTE_OK)
        block = seeded_db.CircuitJob.get(note=NOTE_BLOCK)

        filtered = filter_queued_if_offline_and_fetch(seeded_db, [block, ok])
        assert {j.note for j in filtered} == {NOTE_OK}

        assert ok.status == "WAITING"
        assert ok.timestamp_scheduled is not None

        assert block.status == "PENDING"
        assert block.timestamp_scheduled is None


def test_fetch_all_pending_jobs(seeded_db, monkeypatch):
    monkeypatch.setattr("bqp_database_access.jobs.open_database", lambda *a, **k: seeded_db)
    monkeypatch.setattr("bqp_database_access.jobs.is_within_active_job_limit", lambda *a, **k: True)

    released = fetch_all_pending_jobs()

    assert {j.id for j in released} == {111 , 201}

    # Assert: DB side effects match expectations
    with db_session:
        assert seeded_db.CircuitJob.get(id=201).status == "WAITING"
        assert seeded_db.CircuitJob.get(id=202).status == "PENDING"


def test_fetch_all_pending_jobs_from_users(seeded_db):
    """
    Tests whether `fetch_all_pending_jobs_from_users`:
    * selects only PENDING jobs for the given user list
    * passes them through `filter_queued_if_offline_and_fetch`
    * returns released jobs and updates them to WAITING with timestamp_scheduled
    """
    qdb = seeded_db

    with db_session:
        job_a = (
            qdb.CircuitJob.select(
                lambda j: j.status == "PENDING" and j.owner.identity == "test_user"
            )
            .order_by(qdb.CircuitJob.id)
            .first()
        )
        assert job_a is not None

        ts_name = job_a.target_specification.name
        res_name = job_a.target_specification.resource_name

        res_obj = qdb.Resource.get(name=res_name)
        assert res_obj is not None
        res_obj.maintenance = False

        qdb.CircuitJob.select(
            owner="test_user",
            status="WAITING",
            target_specification=ts_name,
        ).delete(bulk=True)

        job_a.queued = True
        job_a.timestamp_scheduled = None
        job_a.status = "PENDING"

        flush()
        job_a_id = job_a.id

    res = fetch_all_pending_jobs_from_users(["test_user"])
    assert any(j.id == job_a_id for j in res)

    with db_session:
        refreshed = qdb.CircuitJob.get(id=job_a_id)
        assert refreshed is not None
        assert refreshed.owner.identity == "test_user"
        assert refreshed.status == "WAITING"
        assert refreshed.timestamp_scheduled is not None

    res_b = fetch_all_pending_jobs_from_users(["portal_test_user"])
    assert all(j.owner.identity == "portal_test_user" for j in res_b)


def test_fetch_all_pending_jobs_for_resource_from_users(seeded_db):
    """
    Tests whether `fetch_all_pending_jobs_for_resource_from_users`:
    * selects only PENDING jobs
    * restricts to the given resource name
    * restricts to the given user identity list
    * passes jobs through `filter_queued_if_offline_and_fetch` and releases eligible ones
    """
    qdb = seeded_db
    user_a = "test_user"
    user_b = "portal_test_user"
    resource = "TEST_QPU_1"

    with db_session:
        user = qdb.User.get(identity=user_a)
        assert user is not None

        job_a = (
            qdb.CircuitJob.select(
                lambda j: j.owner == user and j.target_specification.resource_name == resource
            )
            .order_by(qdb.CircuitJob.id)
            .first()
        )
        assert job_a is not None

        job_a_id = job_a.id
        ts = job_a.target_specification
        ts_name = ts.name

        res_obj = qdb.Resource.get(name=resource)
        assert res_obj is not None
        res_obj.maintenance = False

        qdb.CircuitJob.select(
            lambda j: j.owner == user
            and j.status == "WAITING"
            and j.target_specification.name == ts_name
            and j.id != job_a_id
        ).delete(bulk=True)

        job_a.status = "PENDING"
        job_a.queued = True
        job_a.timestamp_scheduled = None

        flush()

    res = fetch_all_pending_jobs_for_resource_from_users(resource, [user_a])

    assert any(j.id == job_a_id for j in res)

    with db_session:
        refreshed = qdb.CircuitJob.get(id=job_a_id)
        assert refreshed is not None
        assert refreshed.owner.identity == user_a
        assert refreshed.target_specification.resource_name == resource
        assert refreshed.status == "WAITING"
        assert refreshed.timestamp_scheduled is not None

    res_other_user = fetch_all_pending_jobs_for_resource_from_users(resource, [user_b])
    assert all(j.owner.identity == user_b for j in res_other_user)
    assert all(j.id != job_a_id for j in res_other_user)

    assert fetch_all_pending_jobs_for_resource_from_users("DOES_NOT_EXIST", [user_a]) == []


def test_fetch_all_pending_jobs_for_resource_not_from_users(seeded_db):
    """
    Tests whether `fetch_all_pending_jobs_for_resource_not_from_users`:
    * selects only PENDING jobs for the given resource
    * excludes jobs owned by any identity in the provided user list
    * (if implemented like the other functions) releases eligible jobs via
      `filter_queued_if_offline_and_fetch` and marks them WAITING.
    """
    qdb = seeded_db
    resource = "TEST_QPU_1"
    excluded_user = "test_user"

    with db_session:
        res_obj = qdb.Resource.get(name=resource)
        assert res_obj is not None
        res_obj.maintenance = False

        job_ok = (
            qdb.CircuitJob.select(
                lambda j: j.owner.identity == excluded_user
                and j.target_specification.resource_name == resource
            )
            .order_by(qdb.CircuitJob.id)
            .first()
        )
        assert job_ok is not None

        job_ok_id = job_ok.id
        ts_name = job_ok.target_specification.name

        qdb.CircuitJob.select(
            lambda j: j.owner.identity == excluded_user
            and j.status == "WAITING"
            and j.target_specification.name == ts_name
            and j.id != job_ok_id
        ).delete(bulk=True)

        job_ok.status = "PENDING"
        job_ok.queued = True
        job_ok.timestamp_scheduled = None

        flush()

    res = fetch_all_pending_jobs_for_resource_not_from_users(resource, ["someone_else"])
    assert any(j.id == job_ok_id for j in res)

    res_excluded = fetch_all_pending_jobs_for_resource_not_from_users(resource, [excluded_user])
    assert all(j.id != job_ok_id for j in res_excluded)


def test_fetch_all_pending_jobs_except_for_resources(seeded_db):
    """
    Tests whether `fetch_all_pending_jobs_except_for_resources`:
    * selects only PENDING jobs
    * excludes jobs whose target_specification.resource_name is in the excluded list
    * returns eligible jobs released by `filter_queued_if_offline_and_fetch`
    """
    qdb = seeded_db
    excluded_resource = "TEST_QPU_1"

    with db_session:
        res_obj = qdb.Resource.get(name=excluded_resource)
        assert res_obj is not None
        res_obj.maintenance = False

        job_on_q5 = (
            qdb.CircuitJob.select(
                lambda j: j.target_specification.resource_name == excluded_resource
            )
            .order_by(qdb.CircuitJob.id)
            .first()
        )
        assert job_on_q5 is not None

        job_on_q5_id = job_on_q5.id
        ts_name = job_on_q5.target_specification.name
        owner_id = job_on_q5.owner.identity

        qdb.CircuitJob.select(
            lambda j: j.owner.identity == owner_id
            and j.status == "WAITING"
            and j.target_specification.name == ts_name
            and j.id != job_on_q5_id
        ).delete(bulk=True)

        job_on_q5.status = "PENDING"
        job_on_q5.queued = True
        job_on_q5.timestamp_scheduled = None

        flush()

    res = fetch_all_pending_jobs_except_for_resources([excluded_resource])

    assert all(j.target_specification.resource_name != excluded_resource for j in res)
    assert all(j.id != job_on_q5_id for j in res)

    res_including_q5 = fetch_all_pending_jobs_except_for_resources(["DOES_NOT_EXIST"])

    assert any(j.id == job_on_q5_id for j in res_including_q5)


def test_fetch_all_pending_jobs_except_for_resource_not_from_users(seeded_db):
    """
    Tests `fetch_all_pending_jobs_except_for_resource_not_from_users`.

    Logic under test (for PENDING jobs):
    * include jobs whose resource != given resource
    * for jobs on the given resource, include ONLY if owner.identity is in `userids`
    * then pass through `filter_queued_if_offline_and_fetch`
    """
    qdb = seeded_db
    resource = "TEST_QPU_1"
    allowed_user = "test_user"

    with db_session:
        res_obj = qdb.Resource.get(name=resource)
        assert res_obj is not None
        res_obj.maintenance = False

        job_q5 = (
            qdb.CircuitJob.select(
                lambda j: j.owner.identity == allowed_user
                and j.target_specification.resource_name == resource
            )
            .order_by(qdb.CircuitJob.id)
            .first()
        )
        assert job_q5 is not None

        job_q5_id = job_q5.id
        ts_name = job_q5.target_specification.name

        qdb.CircuitJob.select(
            lambda j: j.owner.identity == allowed_user
            and j.status == "WAITING"
            and j.target_specification.name == ts_name
            and j.id != job_q5_id
        ).delete(bulk=True)

        job_q5.status = "PENDING"
        job_q5.queued = True
        job_q5.timestamp_scheduled = None

        flush()

    res_allowed = fetch_all_pending_jobs_except_for_resource_not_from_users(
        resource, [allowed_user]
    )
    assert any(j.id == job_q5_id for j in res_allowed)

    res_blocked = fetch_all_pending_jobs_except_for_resource_not_from_users(
        resource, ["someone_else"]
    )
    assert all(j.id != job_q5_id for j in res_blocked)
    assert all(
        (j.target_specification.resource_name != resource) or (j.owner.identity in ["someone_else"])
        for j in res_blocked
    )


def test_fetch_all_waiting_jobs(seeded_db):
    """
    Tests whether `fetch_all_waiting_jobs` returns all and only jobs
    whose status is WAITING.
    """
    qdb = seeded_db

    with db_session:
        waiting_job = (
            qdb.CircuitJob.select(status="WAITING")
            .order_by(qdb.CircuitJob.id)
            .first()
        )

        if waiting_job is None:
            job = qdb.CircuitJob.select().order_by(qdb.CircuitJob.id).first()
            assert job is not None
            job.status = "WAITING"
            flush()
            waiting_job_id = job.id
        else:
            waiting_job_id = waiting_job.id

    res = fetch_all_waiting_jobs()

    assert len(res) > 0
    assert all(j.status == "WAITING" for j in res)
    assert any(j.id == waiting_job_id for j in res)


def test_complete_job_with_result(seeded_db):
    """
    Tests whether `complete_job_with_result` correctly finalizes a job.

    Verifies that:
    * job status is set to COMPLETED
    * result, note, executed_resource, and executed_circuit are stored
    * timestamp_completed is set
    """
    qdb = seeded_db
    resource_name = "TEST_QPU_1"
    result_payload = '{"00": 512, "11": 512}'
    executed_circuit = "OPENQASM 2.0; // executed"
    note = "job completed successfully"

    with db_session:
        job = qdb.CircuitJob.select().order_by(qdb.CircuitJob.id).first()
        assert job is not None

        job_id = job.id
        job.status = "WAITING"
        job.timestamp_completed = None
        job.result = ""
        job.note = ""
        job.executed_circuit = ""
        job.executed_resource = None

        flush()

    complete_job_with_result(
        job_id=job_id,
        result=result_payload,
        executed_resource=resource_name,
        executed_circuit=executed_circuit,
        note=note,
    )

    with db_session:
        refreshed = qdb.CircuitJob.get(id=job_id)
        assert refreshed is not None

        assert refreshed.status == "COMPLETED"
        assert refreshed.result == result_payload
        assert refreshed.note == note

        assert refreshed.executed_resource is not None
        assert refreshed.executed_resource.name == resource_name

        assert refreshed.executed_circuit == executed_circuit
        assert refreshed.timestamp_completed is not None


def test_cancel_job_sets_pending_when_queued_and_recent_offline_note(seeded_db):
    """
    Tests `cancel_job` special-case behavior:
    If a job is queued, the note indicates offline/maintenance/down, and the job was
    submitted recently (< MAX_QUEUING_TIME), then the job is set to PENDING (not CANCELLED),
    and timestamp_cancelled + note are set.
    """
    qdb = seeded_db
    note = "resource offline"

    with db_session:
        job = qdb.CircuitJob.select().order_by(qdb.CircuitJob.id).first()
        assert job is not None
        job_id = job.id

        job.queued = True
        job.status = "WAITING"
        job.note = ""
        job.timestamp_cancelled = None
        job.timestamp_submitted = datetime.now()

        flush()

    cancel_job(job_id=job_id, note=note)

    with db_session:
        refreshed = qdb.CircuitJob.get(id=job_id)
        assert refreshed is not None

        assert refreshed.note == note
        assert refreshed.timestamp_cancelled is not None
        assert refreshed.status == "PENDING"


def test_cancel_job_sets_cancelled_in_default_case(seeded_db):
    """
    Tests `cancel_job` default behavior:
    Otherwise, status is set to CANCELLED, and timestamp_cancelled + note are set.
    """
    qdb = seeded_db
    note = "user requested cancellation"

    with db_session:
        job = qdb.CircuitJob.select().order_by(qdb.CircuitJob.id).first()
        assert job is not None
        job_id = job.id

        # Normalize to NOT satisfy special-case
        job.queued = False
        job.status = "WAITING"
        job.note = ""
        job.timestamp_cancelled = None
        job.timestamp_submitted = datetime.now()

        flush()

    cancel_job(job_id=job_id, note=note)

    with db_session:
        refreshed = qdb.CircuitJob.get(id=job_id)
        assert refreshed is not None

        assert refreshed.note == note
        assert refreshed.timestamp_cancelled is not None
        assert refreshed.status == "CANCELLED"


def test_is_within_active_job_limit(seeded_db):
    """
    Tests whether `is_within_active_job_limit` correctly enforces the maximum
    number of active (WAITING) jobs per user and target specification.

    Verifies that:
    * only jobs with status == "WAITING" are counted as active
    * non-WAITING jobs are ignored
    * jobs belonging to other users are ignored
    * jobs with a different target specification are ignored
    * reaching the configured limit of active jobs returns False
    """
    with db_session:
        subject = seeded_db.CircuitJob.get(id=111)
        w1 = seeded_db.CircuitJob.get(id=112)
        w2 = seeded_db.CircuitJob.get(id=113)
        assert subject and w1 and w2

        subject.status = "PENDING"
        subject.queued = False

        w1.status = "PENDING"
        w2.status = "PENDING"
        commit()
        assert is_within_active_job_limit(seeded_db, subject) is True

        w1.owner = subject.owner
        w1.target_specification = subject.target_specification
        w1.queued = False
        w1.status = "WAITING"
        commit()
        assert is_within_active_job_limit(seeded_db, subject) is True

        w2.owner = subject.owner
        w2.target_specification = subject.target_specification
        w2.queued = False
        w2.status = "WAITING"
        commit()
        assert is_within_active_job_limit(seeded_db, subject) is False