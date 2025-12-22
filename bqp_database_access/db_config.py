# db_config.py
import os


def set_test_env(filename: str = "test_db.db"): # ChatGPT
    """
    Set all environment variables required for the test environment.

    This function sets the necessary environment variables to configure
    the database connection for testing purposes.
    """

    # ChatGPT: Make sure Postgres settings don't get used in tests
    os.environ["QUANTUM_DB_HOST"] = ""
    os.environ["QUANTUM_DB_USER"] = ""
    os.environ["QUANTUM_DB_PASS"] = ""
    # os.environ["QUANTUM_DS_HOST"] = "ldaps:localhost"
    # os.environ["USER_TESTING"] = "true"

    # ChatGPT: extra two lines
    os.environ["QUANTUM_DB_TESTING"] = "TRUE"
    os.environ["QUANTUM_DB_FILENAME"] = filename


def reset_test_env():
    # os.environ["QUANTUM_DB_TESTING"] = "TRUE"

    os.environ.pop("QUANTUM_DB_TESTING", None) # ChatGPT
    os.environ.pop("QUANTUM_DB_FILENAME", None) # ChatGPT

    os.environ["QUANTUM_DB_USER"] = ""
    os.environ["QUANTUM_DB_PASS"] = ""
    os.environ["QUANTUM_DB_HOST"] = ""
    os.environ["USER_TESTING"] = ""
