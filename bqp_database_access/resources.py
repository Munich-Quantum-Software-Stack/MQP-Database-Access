"""This module contains all helpers related to resources in the database."""

from ._database import open_database


def fetch_resources_available_to_identity(identity: str) -> tuple["Resource", ...]:
    """Fetch all budgets."""

    quantum_db = open_database()

    user = quantum_db.User.get(email=identity)

    direct_resources = {
        resource for budget in user.budgets for resource in budget.resources
    }

    user_group_budget_resources = {
        resource
        for user_group in user.user_groups
        for budget in user_group.budgets
        for resource in budget.resources
    }

    return tuple(direct_resources.union(user_group_budget_resources))
