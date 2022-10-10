"""This module contains all helpers for the users handling."""


import bcrypt


from ._database import open_database
from ._constants import PEPPER


class IdentityError(Exception):
    pass


class UnknownIdentityError(IdentityError):
    pass


def set_new_secret_for_identity(
    identity: str, new_secret: str, forced: bool = False
) -> None:
    """Set a new password (salted and peppered) for a given identity."""

    quantum_db = open_database()

    user = quantum_db.User.get(email=identity)

    if user is None:
        raise UnknownIdentityError

    peppered_password = new_secret.encode() + PEPPER

    user.secret_hash = bcrypt.hashpw(peppered_password, bcrypt.gensalt()).decode()

    if forced:
        user.force_password_reset = False


def authenticate(identity: str, password: str) -> bool:
    """Authenticate the identity against the database identities."""

    quantum_db = open_database()

    user = quantum_db.User.get(email=identity)
    if user is None:
        raise UnknownIdentityError

    peppered_password = password.encode() + PEPPER

    return bcrypt.checkpw(peppered_password, user.secret_hash.encode())


def fetch_user_by_identity(identity: str) -> "User":
    """Fetch database user data through identity."""

    quantum_db = open_database()

    user = quantum_db.User.get(email=identity)

    if user is None:
        raise UnknownIdentityError

    return user
