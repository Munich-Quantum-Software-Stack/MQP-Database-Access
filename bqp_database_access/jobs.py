"""This module implement the circuit job related database access functions."""

from datetime import datetime
from typing import Optional

from pony.orm import db_session  # type: ignore

from ._database import open_database
from .budgets import fetch_budgets_of_identity


@db_session
def fetch_by_identity(identity: str) -> list["CircuitJob"]:  # type: ignore
    quantum_db = open_database()

    user = quantum_db.User.get(identity=identity)

    if user is None:
        return []

    return list(quantum_db.CircuitJob.select(owner=identity))


@db_session
def fetch_hamiltonian_job_by_identity(identity: str) -> list["HamiltonianJob"]:  # type: ignore
    quantum_db = open_database()

    user = quantum_db.User.get(identity=identity)

    if user is None:
        return []

    return list(quantum_db.HamiltonianJob.select(owner=identity))


@db_session
def fetch_hamiltonian_job_by_task_id(task_id: int) -> list["HamiltonianJob"]:  # type: ignore
    quantum_db = open_database()

    return list(quantum_db.HamiltonianJob.select(id=task_id))


def fetch_result_by_job_id_and_identity(
    job_id: str, identity: str
) -> Optional["CircuitJob"]:  # type: ignore

    if len(identity) == 0 or len(job_id) == 0:
        return None

    quantum_db = open_database()

    return quantum_db.CircuitJob.get(
        lambda job: job.id == job_id and job.owner.identity == identity
    )


@db_session
def create_job(
    shots: int,
    circuit: str,
    owner: str,
    budget: str,
    target_spec: str,
    circuit_format: str,
    no_modify: bool = False,
) -> "CircuitJob":  # type: ignore
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
        no_modify=no_modify,
    )

    quantum_db.commit()

    return job


@db_session
def create_hamiltonian_job(
    interaction_str: str,
    coefficients_str: str,
    owner: str,
    budget: str,
    target_spec: str,
) -> "HamiltonianJob":  # type: ignore
    quantum_db = open_database()

    _cost = 0

    _budget = list(fetch_budgets_of_identity(identity=owner))

    assert len(_budget) > 0

    job = quantum_db.HamiltonianJob(
        interaction_str=interaction_str,
        coefficients_str=coefficients_str,
        timestamp_submitted=datetime.now(),
        cost=0,
        owner=owner,
        budget=budget,
        target_specification=target_spec,
    )

    quantum_db.commit()

    return job


@db_session
def fetch_all_pending_jobs() -> list["CircuitJob"]:  # type: ignore
    quantum_db = open_database()

    jobs = list(quantum_db.CircuitJob.select(status="PENDING"))

    for job in jobs:
        job.timestamp_scheduled = datetime.now()
        job.status = "WAITING"

    return jobs


@db_session
def fetch_all_pending_hamiltonian_jobs() -> list["HamiltonianJob"]:  # type: ignore
    quantum_db = open_database()

    jobs = list(quantum_db.HamiltonianJob.select(status="PENDING"))

    for job in jobs:
        job.timestamp_scheduled = datetime.now()
        job.status = "WAITING"

    return jobs


@db_session
def fetch_all_waiting_jobs() -> list["CircuitJob"]:  # type: ignore
    quantum_db = open_database()

    return list(quantum_db.CircuitJob.select(status="WAITING"))


@db_session
def fetch_all_waiting_hamiltonian_jobs() -> list["HamiltonianJob"]:  # type: ignore
    quantum_db = open_database()

    return list(quantum_db.HamiltonianJob.select(status="WAITING"))


@db_session
def complete_job_with_result(
    job_id: int,
    result: str,
    executed_resource: str,
    executed_circuit: str,
    note: str = "",
) -> None:
    quantum_db = open_database()

    job = quantum_db.CircuitJob.get(id=job_id)

    job.result = result
    job.note = note
    job.executed_resource = quantum_db.Resource.get(name=executed_resource)
    job.executed_circuit = executed_circuit
    job.timestamp_completed = datetime.now()
    job.status = "COMPLETED"
    # TODO set shots completed


@db_session
def update_hybrid_job(
    job_id: int, epochs: int, params: str, parametric_circuit: str, note: str
) -> None:
    quantum_db = open_database()

    job = quantum_db.HamiltonianJob.get(id=job_id)

    job.parametric_circuit = parametric_circuit
    job.params = params
    job.epochs = epochs
    job.note = note


@db_session
def complete_hamiltonian_job_with_result(
    job_id: int,
    result: str,
    executed_resource: str,
    executed_circuit: str,
    note: str = "",
) -> None:
    quantum_db = open_database()

    job = quantum_db.HamiltonianJob.get(id=job_id)

    job.result = result
    job.note = note
    job.executed_resource = quantum_db.Resource.get(name=executed_resource)
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


@db_session
def cancel_hamiltonian_job(job_id: int, note: str) -> None:
    quantum_db = open_database()

    job = quantum_db.HamiltonianJob.get(id=job_id)

    job.note = note
    job.timestamp_cancelled = datetime.now()
    job.status = "CANCELLED"
