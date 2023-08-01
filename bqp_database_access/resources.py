"""This module contains all helpers related to resources in the database."""

from ._database import open_database

from pony.orm import db_session


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
def set_maintenance(name: str, value: bool) -> None:
    """Sets the maintenance entry of a given resource"""

    quantum_db = open_database()

    match name:
        case "QLM":
            resource = quantum_db.Resource.get(name = "QLM Noisy-shot")
            resource.maintenance = value
        case "IQM5":
            resource = quantum_db.Resource.get(name = "Test Q5")
            resource.maintenance = value
        case "Q20":
            resource = quantum_db.Resource.get(name = "Test Q20")
            resource.maintenance = value
        case "SVS":
            resource = quantum_db.Resource.get(name = "Statevector Simulator")
            resource.maintenance = value
