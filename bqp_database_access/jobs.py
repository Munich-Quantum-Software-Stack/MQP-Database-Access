""""""

from uuid import uuid4, UUID

from ._database import open_database


def fetch_all_jobs_by_user(user: "User") -> list["Job"]:
    quantum_db = open_database()

    return quantum_db.Job.select(owner=user)


def create_job(shots: int, circuit: str, user: "User", token: "Token") -> UUID:
    quantum_db = open_database()

    uuid = uuid4()

    quantum_db.Job(id=uuid, shots=shots, circuit=circuit, owner=user, token=token)

    return str(uuid)
