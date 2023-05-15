"""
This module provides the basic database structure and helpers.
"""


import os
import time
import smtplib

from datetime import datetime
from pony.orm import Database, PrimaryKey, Required, Optional, Set
from pony.orm.dbapiprovider import OperationalError

from loguru import logger  # type: ignore

def _define_entities(database: Database):
    class User(database.Entity):
        _table_ = "user"

        email = PrimaryKey(str, auto=False)
        secret_hash = Required(str)
        blocked = Required(bool, default=False)
        block_reason = Optional(str)
        force_secret_reset = Required(bool, default=True)
        tokens = Set("Token")
        budgets = Set("Budget")
        admin = Required(bool, default=False)
        user_groups = Set("UserGroup", table="user_group_user")
        last_login = Optional(datetime)
        last_secret_change = Optional(datetime)

    class UserGroup(database.Entity):
        _table_ = "user_group"

        name = PrimaryKey(str, auto=False)
        users = Set("User", table="user_group_user")
        budgets = Set("Budget", table="budget_user_group")

    class Token(database.Entity):
        _table_ = "token"

        revoke_reason = Optional(str)
        creation = Required(datetime)
        expiration = Required(datetime)
        owner = Required("User")
        remember_name = Required(str, unique=True)
        revoked = Required(bool, default=False)
        token_hash = PrimaryKey(str, auto=False)
        jobs = Set("Job")
        last_used = Optional(datetime)

    class Job(database.Entity):
        _table_ = "job"

        shots = Required(int)
        circuit = Required(str)
        result = Optional(str)
        token = Required("Token")
        status = Required(str, default="PENDING")
        cancel_reason = Optional(str)
        id = PrimaryKey(int, auto=True)
        shots_complete = Required(int, default=0)
        submitted = Required(datetime, default=datetime.now)

    class Budget(database.Entity):
        _table_ = "budget"

        name = PrimaryKey(str, auto=False)
        remaining = Required(int)
        users = Set("User")
        user_groups = Set("UserGroup", table="budget_user_group")
        resources = Set("Resource")
        box_note = Optional(str)
        allocation = Required(int)

    class Resource(database.Entity):
        _table_ = "resource"

        name = PrimaryKey(str, auto=False)
        qubits = Required(int)
        budgets = Set("Budget")
        maintenance = Required(bool, default=False)
        box_note = Optional(str)
        quantum_technology = Required(str)

    class Announcement(database.Entity):
        _table_ = "admin_announcements"

        id = PrimaryKey(int, auto=True)
        start_time = Required(datetime)
        end_time = Required(datetime)
        note = Required(str)
        title = Required(str)
        color = Optional(str, default="status_A1")

    class Pointer(database.Entity):
        _table_ = "pointers"

        id = PrimaryKey(int, auto=True)
        start_time = Required(datetime)
        end_time = Required(datetime)
        title = Required(str)
        note = Required(str)
        weight = Required(int)
        color = Optional(str, default="status_B1")


def open_database(create_tables=False):
    sleep_time = 5
    attempt    = 1
    success    = False
    database   = Database()

    _define_entities(database)

    # for attempt in range(no_tries):
    while success == False:
        try:
            database.bind(
                provider = "postgres",
                user     = os.getenv("QUANTUM_DB_USER"),
                password = os.getenv("QUANTUM_DB_PASS"),
                host     = os.getenv("QUANTUM_DB_HOST"),
                database = "quantumdb",
            )

            success = True
        except Exception as e:
            if attempt == 1 or not attempt % 10:
                try:
                    SERVER  = "mailout.lrz.de"
                    FROM    = "jorge.echavarria@lrz.de"
                    TO      = ["jorge.echavarria@lrz.de", "farooqi@lrz.de"]
                    SUBJECT = "Database Exception!"
                    TEXT    = f"{str(e)}\nAttempt number:{attempt}"

                    message = """
                    From: %s
                    To: %s
                    Subject: %s

                    %s
                    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)

                    server = smtplib.SMTP(SERVER)

                    try:
                        server.sendmail(FROM, TO, message)
                    finally:
                        server.quit()
                except:
                    logger.warning(f"Couldn't send email with Database exception to {TO}")
                    pass

            logger.warning(f"Unsuccessful binding with Database, attempt number {attempt} trying again in {sleep_time} seconds")

            attempt += 1

            time.sleep(sleep_time)

    database.generate_mapping(create_tables=create_tables)

    return database
