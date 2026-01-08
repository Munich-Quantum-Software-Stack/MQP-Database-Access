import bqp_database_access as db_access
from pony.orm import db_session
import tests.utils as utils
import os

def test_create_security_level() -> None:
    with db_session:
        level = db_access.users.fetch_user_security_level("BASIC")
        if level is None:
            db_access.users.create_new_security_level(
                name="BASIC",
                token_max_live_count=1,
                token_max_lifetime=7,
                token_min_creation_interval=0,
                token_max_jobs=1,
                token_max_budget=500,
                token_max_rate=1000,
                login_max_interval=365,
            )
            level = db_access.users.fetch_user_security_level("BASIC")

        assert level is not None
