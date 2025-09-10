import bqp_database_access as db_access
from pony.orm import db_session
import tests.utils as utils
import os
import datetime

def is_sorted_loop(timestamps):
    for i in range(len(timestamps) - 1):
        if timestamps[i] < timestamps[i+1]:
            return False
    return True

@db_session
def test_display_user_by_pages():
    """
    tests if the users are displayed by given page numbers and jobs per page
    """
    db_access.db_config.set_test_env()

    utils.insert_random_data("user", 1000)
    utils.insert_random_data("circuit_job", 1000)
    jobs_per_page = 20
    result = db_access.jobs.fetch_by_identity_pages(
        identity="testuser1", page=2, jobs_per_page=jobs_per_page
    )
    
    db_access.db_config.reset_test_env()
    assert len(result) == jobs_per_page
    
@db_session
def test_timestamp_retrievaal():
    """
    tests if timestamps dictionary can be fetched correctly
    """
    db_access.db_config.set_test_env()

    utils.insert_random_data("user", 1000)
    utils.insert_random_data("circuit_job", 1000)
    num_recent_timestamps = 20
    result = db_access.jobs.retrieve_timestamps(num_recent_timestamps, True, True)
    
    db_access.db_config.reset_test_env()
    assert is_sorted_loop(result["timestamp_submitted"])
