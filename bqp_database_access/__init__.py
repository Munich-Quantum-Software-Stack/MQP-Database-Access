import os
from datetime import datetime
from pony.orm import Database, PrimaryKey, Required, Optional, Set


PEPPER = "UaYRiIq7KU6nbPJz".encode()


def _define_entities(database: Database):
    class User(database.Entity):
        email = PrimaryKey(str, auto=False)
        salted_password_hash = Required(str)
        blocked = Optional(bool, default=False)
        block_reason = Optional(str)
        force_password_reset = Optional(bool, default=True)
        tokens = Set("Token")

    class Token(database.Entity):
        salted_token_hash = PrimaryKey(str, auto=False)
        revoke_reason = Optional(str)
        creation = Required(datetime)
        expiration = Required(datetime)
        owner = Required("User")
        remember_name = Required(str, unique=True)
        revoked = Optional(bool, default=False)


def open():
    database = Database()

    _define_entities(database)

    database.bind(
        provider="postgres",
        user=os.getenv("QUANTUM_DB_USER"),
        password=os.getenv("QUANTUM_DB_PASS"),
        host=os.getenv("QUANTUM_DB_HOST"),
        database="quantumdb",
    )
    database.generate_mapping(create_tables=False)

    return database
