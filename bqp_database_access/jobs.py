""""""
from datetime import datetime
from pony.orm import db_session  # type: ignore

from datetime import datetime

from ._database import open_database
from .budgets import fetch_budgets_of_identity


@db_session
def fetch_by_identity(identity: str) -> list["CircuitJob"]:
    quantum_db = open_database()

    user = quantum_db.User.get(identity=identity)

    if user is None:
        return []

    return list(quantum_db.CircuitJob.select(owner=identity))


@db_session
def create_job(
    shots: int,
    circuit: str,
    owner: str,
    budget: str,
    target_spec: str,
    circuit_format: str = "qasm",
) -> "Job":
    quantum_db = open_database()

    # TODO calculate cost when it is decided
    _cost = 0
    # TODO select the budget to be used for this job
    _budget = list(fetch_budgets_of_identity(identity=owner))
    assert len(_budget) > 0

    job = quantum_db.CircuitJob(
        shots=shots,
        circuit=circuit,
        circuit_format=circuit_format,
        timestamp_submitted=datetime.now(),
        cost=0,
        owner=owner,
        budget=budget,
        target_specification=target_spec,
    )

    quantum_db.commit()

    return job


@db_session
def fetch_all_pending_jobs() -> list["CircuitJob"]:
    quantum_db = open_database()

    jobs = list(quantum_db.CircuitJob.select(status="PENDING"))

    for job in jobs:
        job.timestamp_scheduled = datetime.now()
        job.status = "WAITING"

    return jobs


@db_session
def fetch_all_waiting_jobs() -> list["CircuitJob"]:
    quantum_db = open_database()

    return list(quantum_db.CircuitJob.select(status="WAITING"))


@db_session
def complete_job_with_result(
    job_id: int,
    result: str,
    note: str = "",
    executed_resource: str = "",
    executed_circuit: str = "",
) -> None:
    quantum_db = open_database()

    job = quantum_db.CircuitJob.get(id=job_id)

    job.result = result
    job.note = note
    job.executed_resource = quantum_db.Resource.select(name=executed_resource)
    job.executed_circuit = executed_circuit
    job.timestamp_completed = datetime.now()
    job.status = "COMPLETED"
    # TODO set shots completed


@db_session
def cancel_job(job_id: int, note: str) -> None:
    quantum_db = open_database()

    job = quantum_db.CircuitJob.get(id=job_id)

    job.note = note
    job.timestamp_cancelled = datetime.now()
    job.status = "CANCELLED"
