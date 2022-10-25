"""This module contains all helpers for the users handling."""


import bcrypt
from datetime import datetime


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
    user.last_secret_change = datetime.now()

    if forced:
        user.force_password_reset = False


def authenticate(identity: str, password: str) -> bool:
    """Authenticate the identity against the database identities."""

    # TODO this is used for both logging in and password reset as old password verify

    quantum_db = open_database()

    user = quantum_db.User.get(email=identity)
    if user is None:
        raise UnknownIdentityError

    peppered_password = password.encode() + PEPPER

    authenticated = bcrypt.checkpw(peppered_password, user.secret_hash.encode())

    if authenticated:
        # TODO this should exclude the password reset
        user.last_login = datetime.now()

    return authenticated


def fetch_user_by_identity(identity: str) -> "User":
    """Fetch database user data through identity."""

    quantum_db = open_database()

    user = quantum_db.User.get(email=identity)

    if user is None:
        raise UnknownIdentityError

    return user


def is_admin(identity: str) -> bool:
    """Check whether user is an admin."""

    quantum_db = open_database()

    return quantum_db.User.get(email=identity).admin
