"""This module contains all helpers related to budgets in the database."""

from ._database import open_database


def create_new_budget(name: str, owner: str, credits: int):  # pylint: disable=W0622
    raise NotImplementedError
    # quantum_db = open_database()
    # budget = quantum_db.Budget(name=name, owner=owner, credits=credits)
    # quantum_db.commit()


def fetch_budgets_of_identity(identity: str) -> set["Budget", ...]:  # type: ignore
    """Fetch all budgets."""

    quantum_db = open_database()

    user = quantum_db.User.get(identity=identity)

    user_group_budgets = {
        budget for user_group in user.user_groups for budget in user_group.budgets
    }

    return user_group_budgets
