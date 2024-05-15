"""This module contains all helpers related to resources in the database."""

from ._database import open_database

from pony.orm import db_session  # type: ignore


def fetch_resources_available_to_identity(identity: str) -> tuple["Resource", ...]:
    """Fetch all budgets."""

    quantum_db = open_database()

    user = quantum_db.User.get(identity=identity)

    user_group_budget_resources = {
        resource
        for user_group in user.user_groups
        for budget in user_group.budgets
        for resource in budget.resources
    }

    return user_group_budget_resources


@db_session
def set_maintenance(name: str, value: bool) -> bool:
    """Sets the maintenance entry of a given resource"""

    quantum_db = open_database()

    resource = quantum_db.Resource.get(name=name)

    if resource is not None:
        resource.maintenance = value
        return True
    # Resource not found
    return False
