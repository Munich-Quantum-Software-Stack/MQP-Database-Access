"""This module contains all helpers related to budgets in the database."""

from ._database import open_database


def fetch_budget_names_of_identity(identity: str) -> tuple[str]:
    """Fetch all budgets."""

    quantum_db = open_database()

    return tuple(
        budget.name
        for budget in quantum_db.User.get(email="identity").budgets.select()[:]
    )
