from pytest import fixture
import os


from bqp_database_access._database import open_database


def delete_local_database() -> None:
    db = open_database()
    path = db.provider.pool.filename
    db.disconnect()
    os.remove(path)


@fixture
def empty_db():
    db = open_database(create_tables=True)
    db.disconnect()

    yield

    delete_local_database()
