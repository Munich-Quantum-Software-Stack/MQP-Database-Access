# database_population_functions.py

from bqp_database_access._database import open_database

def populate_test_database():
    quantum_db = open_database()
    quantum_db.User(
        identity="testuser1",
        email="test1@example.com",
        note="seed",
        affiliation="test-affiliation",  # required
        association="test-association",
        security_level="test-security_level",
        superuser_level="test-superuser_level",
        owner="",
        blocked=False,
    )

    print("Seeded users") # temporary