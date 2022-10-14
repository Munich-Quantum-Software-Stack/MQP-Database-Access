""""""

from uuid import UUID

from ._database import open_database


def fetch_by_identity(identity: str) -> list["Job"]:
    quantum_db = open_database()

    user = quantum_db.User.get(email=identity)
    assert user is not None

    return list(user.jobs)


def create_job(shots: int, circuit: str, user: "User", token: "Token") -> UUID:
    quantum_db = open_database()

    job = quantum_db.Job(shots=shots, circuit=circuit, owner=user, token=token)

    return str(job.id)
