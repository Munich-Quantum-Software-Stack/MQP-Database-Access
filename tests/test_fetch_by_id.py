import bqp_database_access as db_access
from pony.orm import db_session
import tests.utils as utils
import os


@db_session
def test_display_user_by_pages():

    # os.environ["QUANTUM_DB_TESTING"] = "True"
    db_access.db_config.set_test_env()

    """
    tests if the users are displayed by given page numbers and jobs per page
    """

    utils.insert_random_data("user", 1000)
    utils.insert_random_data("circuit_job", 1000)
    jobs_per_page = 20
    result = db_access.jobs.fetch_by_identity_pages(
        identity="testuser1", page=2, jobs_per_page=jobs_per_page
    )
    db_access.db_config.reset_test_env()

    assert len(result["jobs"]) == jobs_per_page
