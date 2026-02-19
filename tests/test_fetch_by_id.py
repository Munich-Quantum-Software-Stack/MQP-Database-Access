import bqp_database_access as db_access
from pony.orm import db_session
import tests.utils as utils

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


@db_session
def test_display_user_by_pages():
    """
    tests if the users are displayed by given page numbers and jobs per page
    """

    utils.insert_random_data("user", 1000)
    utils.insert_random_data("circuit_job", 1000)
    jobs_per_page = 20
    result = db_access.jobs.fetch_by_identity_pages(
        identity="testuser1",
        page=2,
        jobs_per_page=jobs_per_page,
        order="",          # or "ASC"
        order_by="",       # no ORDER BY column
        filter_query="",   # no filter
        )

    assert len(result["jobs"]) == jobs_per_page