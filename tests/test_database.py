from bqp_database_access._database import close_database, open_database


def test_open_database_reuses_process_database():
    first_database = open_database(create_tables=True)
    second_database = open_database()

    assert second_database is first_database

    close_database()