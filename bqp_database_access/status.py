import random
from datetime import datetime

from ._database import open_database


def _weighted_sample_without_replacement(population, weights, k, rng=random):
    v = [rng.random() ** (1 / w) for w in weights]
    order = sorted(range(len(population)), key=lambda i: v[i])
    return [population[i] for i in order[-k:]]


def fetch_current_announcements() -> tuple["Announcement"]:  # type: ignore
    """Fetch all mandatory announcements."""

    quantum_db = open_database()

    announcements = quantum_db.Announcement.select(
        lambda a: a.start_time < datetime.now() and a.end_time > datetime.now()
    )

    return tuple(announcements)


def get_random_pointers(count: int) -> list["Pointer"]:  # type: ignore
    """Return a weighted random selection of currently active pointers."""

    quantum_db = open_database()

    pointers = list(
        quantum_db.Pointer.select(
            lambda p: p.start_time < datetime.now() and p.end_time > datetime.now()
        )
    )

    weights = [pointer.weight for pointer in pointers]

    return _weighted_sample_without_replacement(pointers, weights, count)
