"""This module contains all helpers related to job metrics for resources in the database."""

from datetime import datetime

from pony.orm import db_session  # type: ignore

from ._database import open_database


@db_session
def fill_job_metrics(job_id: int, metrics: dict) -> None:
    """Given the job_id and metrics, fill the new TimestampData table.
    This is being called by the

    Args:
        job_id (int): uuid of the circuit jobs
        metrics (dict): Dictionary of the runtime metrics
    """
    quantum_db = open_database()

    job = quantum_db.TimestampData.get(id=job_id)

    if job is None:
        return

    # list of timestamp attribute names on the TimestampData entity
    timestamp_attrs = [
        "api_entry",
        "api_exit",
        "qdb_entry",
        "qdb_exit",
        "qjr_entry",
        "qjr_exit",
        "isv_jr_entry",
        "isv_jr_exit",
        "quantum_daemon_jr_entry",
        "quantum_daemon_jr_exit",
        "generator_entry",
        "generator_exit",
        "scheduler_entry",
        "scheduler_exit",
        "pass_runner_entry",
        "pass_runner_exit",
        "passes_applied",
        "transpiler_entry",
        "transpiler_exit",
        "submitter_entry",
        "submitter_exit",
        "pass_selection_entry",
        "pass_selection_exit",
        "knitter_entry",
        "knitter_exit",
        "job_execution_start",
        "job_execution_end",
    ]

    for attr in timestamp_attrs:
        match_key = next((k for k in metrics.keys() if k.lower() == attr.lower()), None)
        if match_key is None:
            continue
        value = metrics.get(match_key)
        if value is None:
            continue
        try:
            setattr(job, attr, value)
        except Exception:
            continue

    quantum_db.commit()


@db_session
def update_timestamp_data_submitted(id: str) -> None:
    """Fills the timestamp_completed field of the TimestampData table, since
    that information is already filled on the CircuitJob table.

    Args:
        id (str): job id of a CircuitJob.
    """
    quantum_db = open_database()

    jobs = list(
        quantum_db.CircuitJob.select(status="COMPLETED").filter(
            lambda job: (job.id == id)
        )
    )
    timestamp_job = quantum_db.TimestampData.get(id=id)
    timestamp_job.job_execution_end = jobs.timestamp_completed


@db_session
def fetch_timestamp_data_by_job_id(
    id: str,
) -> list["TimestampData"] | None:
    quantum_db = open_database()

    try:
        query = quantum_db.TimestampData.select(id=id)
        job = list(query)
    except Exception as e:
        print("Job metrics cannot be found (or not specifed) for this job")
        return None
    if not job:
        print(f"Job metrics cannot be found (or not specified) for this job")
        return None
    return job
