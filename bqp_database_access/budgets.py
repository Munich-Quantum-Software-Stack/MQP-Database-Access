"""This module contains all helpers related to budgets in the database."""

from ._database import open_database


def fetch_budget_names_of_identity(identity: str) -> tuple[str]:
    """Fetch all budgets."""

    quantum_db = open_database()

    user = quantum_db.User.get(email=identity)

    direct_budgets = {budget.name for budget in user.budgets}

    user_group_budgets = {
        budget.name for user_group in user.user_groups for budget in user_group.budgets
    }

    return tuple(direct_budgets.union(user_group_budgets))
