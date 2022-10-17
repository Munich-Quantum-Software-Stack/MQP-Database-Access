"""This module contains all helpers related to resources in the database."""

from ._database import open_database


def fetch_resource_names_available_to_identity(identity: str) -> tuple[str]:
    """Fetch all budgets."""

    quantum_db = open_database()

    return tuple(
        set(
            resource.name
            for budget in quantum_db.User.get(email=identity).budgets
            for resource in budget.resources
        )
    )
