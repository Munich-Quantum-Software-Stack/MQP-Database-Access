"""This module contains all helpers related to tokens in the database."""

from datetime import datetime
from typing import Optional
import hashlib

import pony.orm as pony

from ._constants import TOKEN_PEPPER
from ._database import open_database


class TokenError(Exception):
    """The TokenError is a base class for all token related errors."""


class TooManyTokensError(TokenError):
    """This exception occurs when a identity attempts to create too many tokens."""

    def __init__(self, count: int, identity: str):
        self.count = count
        self.identity = identity

        super().__init__(f"Users are not allowed to have more than {count} tokens.")


class TokenExistsError(TokenError):
    """This exception occurs when a identity attempts to create a token with the same name."""

    def __init__(self, token_name: str):
        super().__init__(f"Token '{token_name}' already exists.")


class TokenExpirationBeforeNow(TokenError):
    """This exception occurs when a token is created with an expiration that is before now."""

    def __init__(self, name: str):
        super().__init__(f"Token {name} being created with expiration before now.")


class TokenNotFound(TokenError):
    """This exception occurs when a identity attempts to find a token which doesn't exist."""

    def __init__(self, name: str, owner: str):
        super().__init__(f"Token {name} not found of identity {owner}.")


def add_new_token(name: str, owner: str, token: str, expiration: datetime) -> None:
    """Add a new token for a given identity to the database with an expiration."""

    # check if expiration is too soon
    if datetime.now() >= expiration:
        raise TokenExpirationBeforeNow(name)

    quantum_db = open_database()

    # TODO add as configuration
    token_count_limit = 100

    if (
        pony.count(token for token in quantum_db.Token if token.revoked == False)
        >= token_count_limit
    ):
        raise TooManyTokensError(token_count_limit, owner)

    token_hash = hashlib.sha256(token.encode() + TOKEN_PEPPER).hexdigest()

    if quantum_db.Token.exists(remember_name=name, owner=owner, revoked=False):
        raise TokenExistsError(name)

    quantum_db.Token(
        creation=datetime.now(),
        expiration=expiration,
        owner=owner,
        remember_name=name,
        token_hash=token_hash,
    )

    quantum_db.commit()


def revoke_token_by_name_and_identity(name: str, owner: str) -> None:
    """Revoke a given token by name and identity."""

    quantum_db = open_database()

    token = quantum_db.Token.get(owner=owner, remember_name=name, revoked=False)

    if token is None:
        raise TokenNotFound(name, owner)

    token.revoked = True
    token.revoke_reason = f"User revoked token {datetime.now()}"

    quantum_db.commit()


def fetch_active_tokens_of_identity(owner: str) -> list["Token"]:
    """Fetch all tokens"""

    quantum_db = open_database()

    return quantum_db.Token.select(owner=owner, revoked=False)


def verify_token(token: str) -> Optional["Token"]:
    """
    This function verifies that a received token exists in the database
    and then returns the related user.
    """

    # make sure token exists in database, then return user object

    quantum_db = open_database()

    token_hash = hashlib.sha256(token.encode() + TOKEN_PEPPER).hexdigest()

    return quantum_db.Token.get(token_hash=token_hash)
