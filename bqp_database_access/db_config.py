import os


def set_test_env():
    """
    Set all environment variables required for the test environment.

    This function sets the necessary environment variables to configure
    the database connection for testing purposes.
    """

    os.environ["QUANTUM_DB_HOST"] = "localhost"
    os.environ["QUANTUM_DB_PASS"] = "example"
    os.environ["QUANTUM_DB_USER"] = "postgres"
    os.environ["QUANTUM_DS_HOST"] = "ldaps:localhost"
    os.environ["USER_TESTING"] = "true"


def reset_test_env():
    os.environ["QUANTUM_DB_TESTING"] = "TRUE"
    os.environ["QUANTUM_DB_USER"] = ""
    os.environ["QUANTUM_DB_PASS"] = ""
    os.environ["QUANTUM_DB_HOST"] = ""
    os.environ["USER_TESTING"] = ""
