"""
This module provides the basic database structure and helpers.
"""


import os

from datetime import datetime
from pony.orm import Database, PrimaryKey, Required, Optional, Set
import uuid


def _define_entities(database: Database):
    class User(database.Entity):
        email = PrimaryKey(str, auto=False)
        secret_hash = Required(str)
        blocked = Optional(bool, default=False)
        block_reason = Optional(str)
        force_secret_reset = Optional(bool, default=True)
        tokens = Set("Token")
        budgets = Set("Budget")

    class Token(database.Entity):
        revoke_reason = Optional(str)
        creation = Required(datetime)
        expiration = Required(datetime)
        owner = Required("User")
        remember_name = Required(str, unique=True)
        revoked = Optional(bool, default=False)
        token_hash = PrimaryKey(str, auto=False)
        jobs = Set("Job")

    class Job(database.Entity):
        id = PrimaryKey(uuid.UUID, default=uuid.uuid4())
        shots = Required(int)
        circuit = Required(str)
        result = Optional(str)
        token = Required("Token")
        cancelled = Optional(bool, default=False)
        cancel_reason = Optional(str)

    class Budget(database.Entity):
        name = PrimaryKey(str, auto=False)
        remaining = Required(int)
        users = Set("User")


def open_database(create_tables=False):
    database = Database()

    _define_entities(database)

    database.bind(
        provider="postgres",
        user=os.getenv("QUANTUM_DB_USER"),
        password=os.getenv("QUANTUM_DB_PASS"),
        host=os.getenv("QUANTUM_DB_HOST"),
        database="quantumdb",
    )
    database.generate_mapping(create_tables=create_tables)

    return database
