from uuid import uuid4
from pony.orm import db_session

from bqp_database_access._database import open_database
from bqp_database_access.jobs import fetch_by_identity


def test_fetch_by_identity(empty_db):
    db = open_database()

    identity_a = "test_userA"
    identity_b = "test_userB"

    with db_session:
        level = db.UserSecurityLevel(
            name="BASIC",
            token_max_live_count=1,
            token_max_lifetime=30,
            token_min_creation_interval=1,
            token_max_jobs=100,
            token_max_budget=100,
            token_max_rate=1,
            login_max_interval=365,
        )

        def mk_user(identity: str):
            user = db.User(
                identity=identity,
                security_level=level,
                email=identity,
                affiliation="test",
                association="test",
            )
            budget = db.Budget(name=f"budget-{uuid4()}", owner=user, credits=100)
            return user, budget

        user_a, budget_a = mk_user(identity_a)
        user_b, budget_b = mk_user(identity_b)
        
        def mk_job(user, budget, status: str, tag: str):
            ts = db.TargetSpecification(name=f"ts-{tag}-{uuid4()}", specification_type="test")
            db.CircuitJob(
                status=status,
                shots=1,
                circuit="OPENQASM 2.0",
                circuit_format="qasm",
                owner=user,
                budget=budget,
                target_specification=ts,
            )

        mk_job(user_a, budget_a, "PENDING", "a1")
        mk_job(user_a, budget_a, "PENDING", "a2")
        mk_job(user_a, budget_a, "CANCELLED", "a3")

        mk_job(user_b, budget_b, "PENDING", "b1")
        mk_job(user_b, budget_b, "CANCELLED", "b2")

    jobs = fetch_by_identity(identity_a)

    assert len(jobs) == 3
    assert all(j.owner.identity == identity_a for j in jobs)
    assert {j.status for j in jobs} == {"PENDING", "CANCELLED"}
