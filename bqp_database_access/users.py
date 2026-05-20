"""This module contains all helpers for the users handling."""

from datetime import datetime

import bcrypt

from ._constants import PEPPER
from ._database import open_database


class IdentityError(Exception):
    """Base exception for identity-related failures."""


class UnknownIdentityError(IdentityError):
    """Raised when an identity is not present in the database."""


class BlockedIdentityError(IdentityError):
    """Raised when an identity is blocked from access."""


class IncorrectSecretError(IdentityError):
    """Raised when a provided secret does not authenticate."""


def create_new_user_with_secret(
    identity: str,
    secret: str,
    security_level: str,
    email: str,
    affiliation: str,
    association: str,
    force_secret_reset: bool = False,
) -> None:
    """Create a new user with a salted, peppered, and hashed secret."""
    quantum_db = open_database()

    peppered_password = secret.encode() + PEPPER
    passhash = bcrypt.hashpw(peppered_password, bcrypt.gensalt())

    quantum_db.User(
        identity=identity,
        secret_hash=passhash.decode(),
        force_secret_reset=force_secret_reset,
        email=email,
        affiliation=affiliation,
        association=association,
        security_level=security_level,
    )

    quantum_db.commit()


def create_new_ldap_user(
    identity: str, security_level: str, email: str, affiliation: str, association: str
) -> None:
    """Create a new user record without storing a local secret hash."""
    quantum_db = open_database()

    quantum_db.User(
        identity=identity,
        email=email,
        affiliation=affiliation,
        association=association,
        security_level=security_level,
    )

    quantum_db.commit()


def create_new_security_level(
    name: str,
    token_max_live_count: int,
    token_max_lifetime: int,
    token_min_creation_interval: int,
    token_max_jobs: int,
    token_max_budget: int,
    token_max_rate: int,
    login_max_interval: int,
) -> None:
    """Create a new user security level configuration."""
    quantum_db = open_database()

    quantum_db.UserSecurityLevel(
        name=name,
        token_max_live_count=token_max_live_count,
        token_max_lifetime=token_max_lifetime,
        token_min_creation_interval=token_min_creation_interval,
        token_max_jobs=token_max_jobs,
        token_max_budget=token_max_budget,
        token_max_rate=token_max_rate,
        login_max_interval=login_max_interval,
    )

    quantum_db.commit()


def fetch_user_security_level(name: str):
    """Fetch a user security level by name."""
    quantum_db = open_database()

    return quantum_db.UserSecurityLevel.get(name=name)


def set_new_secret_for_identity(
    identity: str, new_secret: str, forced: bool = False
) -> None:
    """Set a new password (salted and peppered) for a given identity."""

    quantum_db = open_database()

    user = quantum_db.User.get(identity=identity)

    if user is None:
        raise UnknownIdentityError

    peppered_password = new_secret.encode() + PEPPER

    user.secret_hash = bcrypt.hashpw(peppered_password, bcrypt.gensalt()).decode()
    user.last_secret_change = datetime.now()
    user.force_secret_reset = forced


def authenticate(identity: str, password: str) -> None:
    """Authenticate the identity against the database identities."""

    # TODO this is used for both logging in and password reset as old password verify

    quantum_db = open_database()

    user = quantum_db.User.get(identity=identity)
    if user is None:
        raise UnknownIdentityError

    peppered_password = password.encode() + PEPPER

    authenticated = bcrypt.checkpw(peppered_password, user.secret_hash.encode())

    if authenticated:
        # TODO this should exclude the password reset
        user.last_login = datetime.now()

    else:
        raise IncorrectSecretError


def fetch_user_by_identity(identity: str) -> "User":  # type: ignore
    """Fetch database user data through identity."""

    quantum_db = open_database()

    user = quantum_db.User.get(identity=identity)

    if user is None:
        raise UnknownIdentityError

    return user
