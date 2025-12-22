import bqp_database_access as db_access
from pony.orm import db_session, commit
# import tests.utils as utils
import os

from bqp_database_access import users, budgets, jobs

"""
@db_session
def test_display_user_by_pages(empty_db):
    # os.environ["QUANTUM_DB_TESTING"] = "True"

    ### tests if the users are displayed by given page numbers and jobs per page
    
    utils.insert_random_data("user", 1000)
    utils.insert_random_data("circuit_job", 1000)
    jobs_per_page = 20
    result = db_access.jobs.fetch_by_identity_pages(
        identity="testuser1", page=2, jobs_per_page=jobs_per_page
    )


    assert len(result) == jobs_per_page
"""

def test_display_user_by_pages(empty_db):
    qdb = db_access._database.open_database()

    with db_session:
        # prerequisites
        if qdb.UserSecurityLevel.get(name="BASIC") is None:
            qdb.UserSecurityLevel(
                name="BASIC",
                token_max_live_count=999,
                token_max_lifetime=999999,
                token_min_creation_interval=0,
                token_max_jobs=999999,
                token_max_budget=999999,
                token_max_rate=999999,
                login_max_interval=999999,
            )

        if qdb.TargetSpecification.get(name="default") is None:
            qdb.TargetSpecification(name="default", specification_type="default")

        # user (fill required fields)
        user = qdb.User.get(identity="testuser1")
        if user is None:
            user = qdb.User(
                identity="testuser1",
                email="testuser1@example.com",
                affiliation="test_affiliation",
                association="test_association",
                security_level="BASIC",
                secret_hash="x",              # required? set something
                force_secret_reset=False,      # required? set it
            )

        # budget (required by job creation logic)
        if qdb.Budget.get(name="testbudget") is None:
            qdb.Budget(name="testbudget", owner=user, credits=10_000)

        # jobs: create only what you need
        for i in range(60):
            qdb.CircuitJob(
                shots=1,
                circuit="{}",
                circuit_format="QASM",
                timestamp_submitted=db_access.users.datetime.now() if hasattr(db_access, "users") else None,
                cost=0,
                owner=user,                         # relation, not string
                budget=qdb.Budget.get(name="testbudget"),
                target_specification=qdb.TargetSpecification.get(name="default"),
                no_modify=False,
                queued=False,
            )

    # now the function under test (wrap read in db_session)
    with db_session:
        result = db_access.jobs.fetch_by_identity_pages(
        identity="testuser1",
        page=2,
        jobs_per_page=20,
        order="desc",            # or "asc" — must match implementation
        order_by="timestamp_submitted",
        filter_query=None        # or "" if code assumes string
    )

    assert len(result["jobs"]) == 20
    assert result["totaljob_nr"] == 60
