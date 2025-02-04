"""This module contains all helpers for the feedback handling."""

from datetime import datetime

from ._database import open_database


def create_feedback_for_identity(
    owner: str, rating: int, category: str, note: str
) -> None:

    quantum_db = open_database()

    quantum_db.Feedback(
        owner=owner, rating=rating, category=category, date=datetime.now(), note=note
    )

    quantum_db.commit()
