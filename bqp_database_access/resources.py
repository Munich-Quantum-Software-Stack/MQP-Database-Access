"""This module contains all helpers related to resources in the database."""

from ._database import open_database


def fetch_resources_available_to_identity(identity: str) -> tuple["Resource"]:
    """Fetch all budgets."""

    quantum_db = open_database()

    return tuple(
        set(
            resource
            for budget in quantum_db.User.get(email=identity).budgets
            for resource in budget.resources
        )
    )
