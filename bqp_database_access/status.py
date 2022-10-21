from datetime import datetime

from ._database import open_database


def fetch_current_announcements() -> tuple[str]:
    """Fetch all mandatory announcements."""

    quantum_db = open_database()

    announcements = quantum_db.Announcement.select(
        lambda a: a.start_time < datetime.now() and a.end_time > datetime.now()
    )

    return tuple(announcements)
