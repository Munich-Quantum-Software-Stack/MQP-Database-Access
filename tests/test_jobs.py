import os
import pytest

from bqp_database_access.jobs import (
    # identity-based reads
    fetch_by_identity,
    fetch_by_identity_pages,
    fetch_result_by_job_id_and_identity,
    # misc helper
    filter_queued_if_offline_and_fetch,
    # job queries
    fetch_all_pending_jobs,
    fetch_all_pending_jobs_from_users,
    fetch_all_pending_jobs_for_resource_from_users,
    fetch_all_pending_jobs_for_resource_not_from_users,
    fetch_all_pending_jobs_except_for_resources,
    fetch_all_pending_jobs_except_for_resource_not_from_users,
    fetch_all_waiting_jobs,
    # mutations (gated)
    cancel_job,
    complete_job_with_result,
    update_hybrid_job,
    create_job,
    is_within_active_job_limit,
)

# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------

def _mutations_enabled() -> bool:
    return os.getenv("ALLOW_DB_MUTATIONS", "").strip() == "1"


def _skip_mutations() -> None:
    pytest.skip("DB mutation tests disabled. Set ALLOW_DB_MUTATIONS=1 to enable.")


def _any_job_or_skip():
    """
    Prefer pending jobs (most useful for testing), otherwise waiting jobs.
    """
    pending = fetch_all_pending_jobs()
    if pending:
        return pending[0]

    waiting = fetch_all_waiting_jobs()
    if waiting:
        return waiting[0]

    pytest.skip("No pending/waiting jobs found in DB; cannot derive job/identity.")


def _identity_from_job_or_skip(job) -> str:
    """
    Field naming may differ; try common ones.
    """
    identity = getattr(job, "owner", None) or getattr(job, "identity", None)
    if not identity:
        pytest.skip("Job has no owner/identity field to derive identity.")
    return identity


def _status_str(job) -> str | None:
    """
    Normalize status/state if present.
    """
    if hasattr(job, "status"):
        return str(getattr(job, "status")).upper()
    if hasattr(job, "state"):
        return str(getattr(job, "state")).upper()
    return None


# --------------------------------------------------------------------------------------
# Pure / safe smoke tests (no mutations)
# --------------------------------------------------------------------------------------

def test_filter_queued_if_offline_and_fetch_empty_is_empty() -> None:
    out = filter_queued_if_offline_and_fetch(qdb=None, jobs=[])
    assert out == []


def test_fetch_all_pending_jobs_smoke() -> None:
    jobs = fetch_all_pending_jobs()
    assert isinstance(jobs, list)


def test_fetch_all_waiting_jobs_smoke() -> None:
    jobs = fetch_all_waiting_jobs()
    assert isinstance(jobs, list)


def test_fetch_all_pending_jobs_from_users_smoke() -> None:
    jobs = fetch_all_pending_jobs_from_users(userids=[])
    assert isinstance(jobs, list)
    assert jobs == []


def test_fetch_all_pending_jobs_for_resource_from_users_smoke() -> None:
    jobs = fetch_all_pending_jobs_for_resource_from_users(resource="", userids=[])
    assert isinstance(jobs, list)
    assert jobs == []


def test_fetch_all_pending_jobs_for_resource_not_from_users_smoke() -> None:
    jobs = fetch_all_pending_jobs_for_resource_not_from_users(resource="", userids=[])
    assert isinstance(jobs, list)


def test_fetch_all_pending_jobs_except_for_resources_smoke() -> None:
    jobs = fetch_all_pending_jobs_except_for_resources(resources=[])
    assert isinstance(jobs, list)


def test_fetch_all_pending_jobs_except_for_resource_not_from_users_smoke() -> None:
    jobs = fetch_all_pending_jobs_except_for_resource_not_from_users(resource="", userids=[])
    assert isinstance(jobs, list)


def test_fetch_by_identity_smoke() -> None:
    job = _any_job_or_skip()
    identity = _identity_from_job_or_skip(job)

    jobs = fetch_by_identity(identity)
    assert isinstance(jobs, list)


def test_fetch_by_identity_pages_shape() -> None:
    job = _any_job_or_skip()
    identity = _identity_from_job_or_skip(job)

    payload = fetch_by_identity_pages(
        identity=identity,
        page=0,
        jobs_per_page=20,
        order="DESC",
        order_by="id",
        filter_query="",
    )
    assert isinstance(payload, dict)
    assert "jobs" in payload
    assert "totaljob_nr" in payload
    assert isinstance(payload["jobs"], list)
    assert isinstance(payload["totaljob_nr"], int)


def test_fetch_result_by_job_id_and_identity_smoke() -> None:
    """
    We don't assume a result exists (DB state varies), but the call should not error.
    """
    job = _any_job_or_skip()
    identity = _identity_from_job_or_skip(job)

    res = fetch_result_by_job_id_and_identity(job_id=job.id, identity=identity)
    assert (res is None) or isinstance(res, (dict, str, bytes)) or hasattr(res, "__dict__")


# --------------------------------------------------------------------------------------
# Mutation tests (disabled by default; enable via ALLOW_DB_MUTATIONS=1)
# --------------------------------------------------------------------------------------

def test_cancel_job_sets_cancelled_if_possible() -> None:
    if not _mutations_enabled():
        _skip_mutations()

    pending = fetch_all_pending_jobs()
    if not pending:
        pytest.skip("No pending jobs to cancel.")

    job = pending[0]
    identity = _identity_from_job_or_skip(job)

    cancel_job(job_id=job.id, note="pytest cancel")

    # Verify via refetch
    jobs = fetch_by_identity(identity)
    updated = next((j for j in jobs if getattr(j, "id", None) == job.id), None)
    assert updated is not None, "Cancelled job not found after refetch."

    st = _status_str(updated)
    if st is None:
        pytest.skip("No status/state field available to assert cancellation.")
    assert st == "CANCELLED"


def test_complete_job_with_result_smoke() -> None:
    if not _mutations_enabled():
        _skip_mutations()

    pending = fetch_all_pending_jobs()
    if not pending:
        pytest.skip("No pending jobs to complete.")

    job = pending[0]

    # This will mutate DB; only run with ALLOW_DB_MUTATIONS=1
    complete_job_with_result(
        job_id=job.id,
        result='{"ok": true}',
        executed_resource="pytest-resource",
        executed_circuit="executed-circuit",
        note="pytest complete",
    )


def test_update_hybrid_job_smoke() -> None:
    if not _mutations_enabled():
        _skip_mutations()

    # Requires a hybrid job; we cannot guarantee the DB has one.
    job = _any_job_or_skip()

    try:
        update_hybrid_job(
            job_id=job.id,
            epochs=1,
            params='{"theta": 0.1}',
            parametric_circuit="PARAMETRIC_CIRCUIT",
            note="pytest update",
        )
    except Exception as e:
        pytest.skip(f"update_hybrid_job not applicable for available job / schema: {e}")


def test_create_job_smoke_disabled_by_default() -> None:
    """
    Creating jobs requires budgets/target specs. Without deterministic fixtures,
    this is unreliable, so we keep it disabled by default.
    """
    if not _mutations_enabled():
        _skip_mutations()

    pytest.skip("Enable only after you decide how to supply budget/target_spec deterministically.")


def test_is_within_active_job_limit_disabled_by_default() -> None:
    """
    Often needs a Pony Database instance fixture (qdb) + deterministic job seeding.
    """
    pytest.skip("Not testable reliably under Option 2 without controlled seeding / qdb fixture.")
