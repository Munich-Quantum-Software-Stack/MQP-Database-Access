""""""

from ._database import open_database

from pony.orm import db_session

@db_session
def fetch_by_identity(identity: str) -> list["Job"]:
    quantum_db = open_database()

    user = quantum_db.User.get(email=identity)

    if user is None:
        return []

    return [job for token in user.tokens for job in token.jobs]

@db_session
def create_job(shots: int, circuit: str, token: "Token") -> "Job":
    quantum_db = open_database()

    job = quantum_db.Job(shots=shots, circuit=circuit, token=token.token_hash)

    quantum_db.commit()

    return job
