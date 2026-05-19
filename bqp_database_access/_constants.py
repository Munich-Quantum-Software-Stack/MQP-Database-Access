"""This module contains various database access constants."""

import os

PEPPER = os.environ["QUANTUM_DB_PEPPER"].encode()

TOKEN_PEPPER = os.environ["QUANTUM_DB_TOKEN_PEPPER"].encode()
