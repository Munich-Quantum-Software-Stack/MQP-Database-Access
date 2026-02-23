import os


DEFAULT_TEST_ENV = {
    "QUANTUM_DB_TESTING": "TRUE",
    "QUANTUM_DB_FILENAME": "test_db.sqlite",
    "QUANTUM_DB_USER": "postgres",
    "QUANTUM_DB_PASS": "example",
    "QUANTUM_DB_HOST": "localhost:5432",
    "QUANTUM_DS_HOST": "ldaps:localhost",
    "USER_TESTING": "",
}


def set_test_env() -> None:
    """Set environment variables required for test execution."""

    for key, value in DEFAULT_TEST_ENV.items():
        os.environ[key] = value


def reset_test_env() -> None:
    """Unset test-specific environment variables."""

    for key in DEFAULT_TEST_ENV:
        os.environ.pop(key, None)