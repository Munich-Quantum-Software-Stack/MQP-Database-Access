import bqp_database_access as db_access
from pony.orm import db_session

def test_create_security_level(seeded_db) -> None:
    """
    Use seeded fixture to ensure full schema exists before user-level checks.
    """
    
    with db_session:
        level = db_access.users.fetch_user_security_level("BASIC")
    assert level is not None


def test_display_user_by_pages(seeded_db):
    """
    Verify paging over seeded sqlite jobs without postgres-only helpers.
    """

    jobs_per_page = 2

    with db_session:
        result = db_access.jobs.fetch_by_identity_pages(
            identity="test_user",
            page=0,
            jobs_per_page=jobs_per_page,
            order="ASC",
            order_by="id",
            filter_query="",
        )

        assert result["totaljob_nr"] == 3
        assert len(result["jobs"]) == jobs_per_page