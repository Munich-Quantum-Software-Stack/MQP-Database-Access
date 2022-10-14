""""""

from uuid import UUID

from ._database import open_database


def fetch_all_jobs_by_user(user: "User") -> list["Job"]:
    quantum_db = open_database()

    return quantum_db.Job.select(owner=user)


def create_job(shots: int, circuit: str, user: "User", token: "Token") -> UUID:
    quantum_db = open_database()

    job = quantum_db.Job(shots=shots, circuit=circuit, owner=user, token=token)

    return str(job.id)
