from pony.orm import db_session

from bqp_database_access._database import open_database
from bqp_database_access.jobs import fetch_by_identity


def test_fetch_by_identity_returns_jobs_for_existing_user(empty_db, tmp_path):
    db = open_database()

    identity = f"user-{tmp_path.name}@example.com"
    budget_name = f"budget-{tmp_path.name}"

    with db_session:
        # --- security level (required relation) ---
        level = db.ResourceSecurityLevel.select().first()
        if level is None:
            level = db.ResourceSecurityLevel(
                name=f"level-{tmp_path.name}",
                job_min_interval=0,
                budget_max_per_job=10**9,
                unique_token_required=False,
                token_max_lifetime=10**9,
            )

        # --- user ---
        user = db.User(
            identity=identity,
            security_level=level,
            email=identity,
            affiliation="test",
            association="test",
        )

        # --- budget (required relation) ---
        budget = db.Budget(
            name=budget_name,
            owner=user,
            credits=100,
        )

        # --- two jobs for this user ---
        db.CircuitJob(
            shots=1,
            circuit="circuit-1",
            circuit_format="qasm",
            target_specification="{}",
            owner=user,
            budget=budget,
        )
        db.CircuitJob(
            shots=2,
            circuit="circuit-2",
            circuit_format="qasm",
            target_specification="{}",
            owner=user,
            budget=budget,
        )

    jobs = fetch_by_identity(identity)

    assert len(jobs) == 2
    assert all(job.owner.identity == identity for job in jobs)
