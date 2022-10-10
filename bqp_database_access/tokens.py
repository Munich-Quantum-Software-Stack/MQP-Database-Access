"""This module contains all helpers related to tokens in the database."""

from datetime import datetime

import pony.orm as pony
from bcrypt import hashpw

from ._constants import PEPPER
from ._database import _open_database


class TokenError(Exception):
    """The TokenError is a base class for all token related errors."""


class TooManyTokensError(TokenError):
    """This exception occurs when a user attempts to create too many tokens."""

    def __init__(self, count: int, user: str):
        self.count = count
        self.user = user

        super().__init__(f"Users are not allowed to have more than {count} tokens.")


class TokenExistsError(TokenError):
    """This exception occurs when a user attempts to create a token with the same name."""

    def __init__(self, token_name: str):
        super().__init__(f"Token '{token_name}' already exists.")


class TokenExpirationBeforeNow(TokenError):
    """This exception occurs when a token is created with an expiration that is before the current time."""

    def __init__(self, name: str):
        super().__init__(f"Token {name} being created with expiration before now.")


class TokenNotFound(TokenError):
    """This exception occurs when a user attempts to find a token which doesn't exist."""

    def __init__(self, name: str, owner: str):
        super().__init__(f"Token {name} not found of user {owner}.")


def add_new_token(name: str, owner: str, token: str, expiration: datetime) -> None:
    """Add a new token for a given user to the database with an expiration."""

    # check if expiration is too soon
    if datetime.now() >= expiration:
        raise TokenExpirationBeforeNow(name)

    quantum_db = _open_database()

    # TODO add as configuration
    token_count_limit = 100

    if (
        pony.count(token for token in quantum_db.Token if token.revoked == False)
        >= token_count_limit
    ):
        raise TooManyTokensError(token_count_limit, owner)

    peppered_token_hash = hashpw(token.encode(), PEPPER).decode()

    if quantum_db.Token.exists(remember_name=name, owner=owner, revoked=False):
        raise TokenExistsError(name)

    quantum_db.Token(
        creation=datetime.now(),
        expiration=expiration,
        owner=owner,
        remember_name=name,
        peppered_token_hash=peppered_token_hash,
    )

    quantum_db.commit()


def revoke_token_by_name_and_user(name: str, owner: str) -> None:
    """Revoke a given token by name and user."""

    quantum_db = _open_database()

    token = quantum_db.Token.get(owner=owner, remember_name=name, revoked=False)

    if token is None:
        raise TokenNotFound(name, owner)

    token.revoked = True
    token.revoke_reason = f"User revoked token {datetime.now()}"

    quantum_db.commit()


def fetch_active_tokens_of_user(owner: str) -> tuple[str, ...]:
    """Fetch all tokens"""

    quantum_db = _open_database()

    return tuple(
        token.remember_name
        for token in quantum_db.Token.select(owner=owner, revoked=False)
    )
