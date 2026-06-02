# ------------------------------------------------------------------------------
# Copyright 2026 Munich Quantum Software Stack Project
#
# Licensed under the Apache License, Version 2.0 with LLVM Exceptions (the
# "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://github.com/Munich-Quantum-Software-Stack/QDMI/blob/develop/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# ------------------------------------------------------------------------------

"""MQP-Database-Access Job module"""

from datetime import datetime
from typing import Optional

from pony.orm import db_session, commit  # type: ignore

from ._database import open_database
from .budgets import fetch_budgets_of_identity

MAX_QUEUING_TIME = 86400  # 24 hour
MAX_ACTIVE_JOBS_PER_USER_PER_RESOURCE = 2


@db_session
def fetch_by_identity(identity: str) -> list["CircuitJob"]:  # type: ignore
    """Return all circuit jobs owned by the given identity."""

    quantum_db = open_database()

    user = quantum_db.User.get(identity=identity)

    if user is None:
        return []

    return list(quantum_db.CircuitJob.select(owner=identity))


@db_session
def fetch_by_identity_pages(
    identity: str,
    page: int,
    jobs_per_page: int,
    order: str,
    order_by: str,
    filter_query: str,
    ) -> dict[str, list["CircuitJob"] | int]:  # type: ignore
    """Fetch paginated circuit jobs belonging to a user identity.

    Only the requested page of jobs is fetched, instead of all database
    entries. This reduces query load when jobs are displayed on the MQP
    website.
    """

    start_list = page * jobs_per_page
    quantum_db = open_database()
    user = quantum_db.User.get(identity=identity)
    table = quantum_db.CircuitJob
    if user is None:
        return {"jobs": [], "totaljob_nr": 0}
    query = f"SELECT * FROM circuit_job WHERE owner = '{identity}'"

    if filter_query:
        n_total = quantum_db.select(
            "SELECT COUNT(*) FROM circuit_job "
            f"WHERE owner = '{identity}' AND status = '{filter_query}'"
        )[0]
        query += f"AND status = '{filter_query}'"
    else:
        n_total = quantum_db.select(
        "SELECT COUNT(*) FROM circuit_job "
        f"WHERE owner = '{identity}'"
        )[0]
    if order_by:
        query+=f" ORDER BY {order_by}"

    query+=f" {order}"
    query+=f" LIMIT {jobs_per_page}"
    query+=f" OFFSET {start_list}"
    query_res = table.select_by_sql(query)
    return {"jobs": query_res,
            "totaljob_nr": int(n_total)}

@db_session
def fetch_hamiltonian_job_by_identity(identity: str) -> list["HamiltonianJob"]:  # type: ignore
    """Return all Hamiltonian jobs owned by the given identity."""

    quantum_db = open_database()

    user = quantum_db.User.get(identity=identity)

    if user is None:
        return []

    return list(quantum_db.HamiltonianJob.select(owner=identity))


@db_session
def fetch_hamiltonian_job_by_task_id(task_id: int) -> list["HamiltonianJob"]:  # type: ignore
    """Return Hamiltonian jobs matching the provided task ID."""

    quantum_db = open_database()

    return list(quantum_db.HamiltonianJob.select(id=task_id))


def fetch_result_by_job_id_and_identity(
    job_id: str, identity: str
) -> Optional["CircuitJob"]:  # type: ignore
    """Return a circuit job by ID for an identity, or ``None`` if unavailable."""

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
    queued: bool = False,
) -> "CircuitJob":  # type: ignore
    """Create and persist a new circuit job."""

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
        queued=queued,
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
    """Create and persist a new Hamiltonian job."""

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


def is_within_active_job_limit(qdb, job: "CircuitJob") -> bool:  # type: ignore
    """Count the number of active jobs for a given user."""

    return (
        qdb.CircuitJob.select(
            owner=job.owner.identity,
            status="WAITING",
            target_specification=job.target_specification.name,
        ).count()
        < MAX_ACTIVE_JOBS_PER_USER_PER_RESOURCE
    )


def filter_queued_if_offline_and_fetch(
    qdb, jobs: list["CircuitJob"]  # type: ignore
) -> list["CircuitJob"]:  # type: ignore
    """Return pending jobs that are eligible to move into waiting state."""

    filtered_jobs = []
    for job in jobs:
        if (
            not job.queued
            or not qdb.Resource.get(
                name=job.target_specification.resource_name
            ).maintenance
            or (datetime.now() - job.timestamp_submitted).total_seconds()
            > MAX_QUEUING_TIME
        ) and (is_within_active_job_limit(qdb, job)):
            job.timestamp_scheduled = datetime.now()
            job.status = "WAITING"
            job.flush()
            commit()
            filtered_jobs.append(job)
    return filtered_jobs


@db_session
def fetch_all_pending_jobs() -> list["CircuitJob"]:  # type: ignore
    """Return all pending circuit jobs that can be scheduled."""

    quantum_db = open_database()

    jobs = list(quantum_db.CircuitJob.select(status="PENDING"))

    return filter_queued_if_offline_and_fetch(quantum_db, jobs)


@db_session
def fetch_all_pending_jobs_from_users(
    userids: list[str],
) -> list["CircuitJob"]:  # type: ignore
    """Return schedulable pending jobs owned by the provided users."""

    quantum_db = open_database()

    jobs = list(
        quantum_db.CircuitJob.select(status="PENDING").filter(
            lambda job: job.owner.identity in userids
        )
    )

    return filter_queued_if_offline_and_fetch(quantum_db, jobs)


@db_session
def fetch_all_pending_jobs_for_resource_from_users(
    resource: str, userids: list[str]
) -> list["CircuitJob"]:  # type: ignore
    """Return schedulable pending jobs for a resource from selected users."""

    quantum_db = open_database()

    jobs = list(
        quantum_db.CircuitJob.select(status="PENDING").filter(
            lambda job: job.target_specification.resource_name == resource
            and job.owner.identity in userids
        )
    )

    return filter_queued_if_offline_and_fetch(quantum_db, jobs)


@db_session
def fetch_all_pending_jobs_for_resource_not_from_users(
    resource: str, userids: list[str]
) -> list["CircuitJob"]:  # type: ignore
    """Return schedulable pending jobs for a resource excluding selected users."""

    quantum_db = open_database()

    jobs = list(
        quantum_db.CircuitJob.select(status="PENDING").filter(
            lambda job: job.target_specification.resource_name == resource
            and job.owner.identity not in userids
        )
    )

    return filter_queued_if_offline_and_fetch(quantum_db, jobs)


@db_session
def fetch_all_pending_jobs_except_for_resources(
    resources: list[str],
) -> list["CircuitJob"]:  # type: ignore
    """Return schedulable pending jobs excluding the listed resources."""

    quantum_db = open_database()

    jobs = list(
        quantum_db.CircuitJob.select(status="PENDING").filter(
            lambda job: job.target_specification.resource_name not in resources
        )
    )

    return filter_queued_if_offline_and_fetch(quantum_db, jobs)


@db_session
def fetch_all_pending_jobs_except_for_resource_not_from_users(
    resource: str, userids: list[str]
) -> list["CircuitJob"]:  # type: ignore
    """Return schedulable pending jobs, except a resource for non-listed users."""

    quantum_db = open_database()

    jobs = list(
        quantum_db.CircuitJob.select(status="PENDING").filter(
            lambda job: (
                job.target_specification.resource_name != resource
                or (
                    job.target_specification.resource_name == resource
                    and job.owner.identity in userids
                )
            )
        )
    )

    return filter_queued_if_offline_and_fetch(quantum_db, jobs)


@db_session
def fetch_all_pending_hamiltonian_jobs() -> list["HamiltonianJob"]:  # type: ignore
    """Return pending Hamiltonian jobs after marking them as waiting."""

    quantum_db = open_database()

    jobs = list(quantum_db.HamiltonianJob.select(status="PENDING"))

    for job in jobs:
        job.timestamp_scheduled = datetime.now()
        job.status = "WAITING"

    return jobs


@db_session
def fetch_all_waiting_jobs() -> list["CircuitJob"]: # type: ignore
    """Return all circuit jobs currently in waiting state."""

    quantum_db = open_database()

    return list(quantum_db.CircuitJob.select(status="WAITING"))


@db_session
def fetch_all_waiting_hamiltonian_jobs() -> list["HamiltonianJob"]: # type: ignore
    """Return all Hamiltonian jobs currently in waiting state."""

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
    """Mark a circuit job as completed and store its execution result fields."""

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
    """Update stored optimization fields for a Hamiltonian job."""
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
    """Mark a Hamiltonian job as completed and store its result fields."""

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
    """Cancel a circuit job, or requeue it when offline retry conditions match."""

    quantum_db = open_database()

    job = quantum_db.CircuitJob.get(id=job_id)

    job.note = note
    job.timestamp_cancelled = datetime.now()

    # If the job is queued and the resource is offline, maintenance or down
    # and the job has been submitted less than an hour ago, then set the job as pending
    if (
        job.queued
        and (
            note.find("offline") != -1
            or note.find("maintenance") != -1
            or note.find("down") != -1
        )
        and (datetime.now() - job.timestamp_submitted).total_seconds()
        < MAX_QUEUING_TIME
    ):
        job.status = "PENDING"
    else:
        job.status = "CANCELLED"


@db_session
def cancel_hamiltonian_job(job_id: int, note: str) -> None:
    """Cancel a Hamiltonian job and record cancellation metadata."""
    quantum_db = open_database()

    job = quantum_db.HamiltonianJob.get(id=job_id)

    job.note = note
    job.timestamp_cancelled = datetime.now()
    job.status = "CANCELLED"
