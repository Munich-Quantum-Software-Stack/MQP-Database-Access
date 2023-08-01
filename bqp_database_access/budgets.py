"""This module contains all helpers related to budgets in the database."""

from ._database import open_database


def fetch_budgets_of_identity(identity: str) -> tuple["Budget"]:
    """Fetch all budgets."""

    quantum_db = open_database()

    user = quantum_db.User.get(identity=identity)

    user_group_budgets = {
        budget for user_group in user.user_groups for budget in user_group.budgets
    }

    return user_group_budgets
