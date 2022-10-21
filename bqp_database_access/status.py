from datetime import datetime
from random import choice

from ._database import open_database


def fetch_current_announcements() -> tuple["Announcement"]:
    """Fetch all mandatory announcements."""

    quantum_db = open_database()

    announcements = quantum_db.Announcement.select(
        lambda a: a.start_time < datetime.now() and a.end_time > datetime.now()
    )

    return tuple(announcements)


def get_random_pointers(count: int) -> list["Pointer"]:

    quantum_db = open_database()

    pointers = quantum_db.Pointer.select(
        lambda p: p.start_time < datetime.now() and p.end_time > datetime.now()
    )

    weights = [pointer.weight for pointer in pointers]

    return choice(pointers, weights, k=count)
