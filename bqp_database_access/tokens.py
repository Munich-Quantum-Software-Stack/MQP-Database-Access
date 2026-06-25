# ------------------------------------------------------------------------------
# Copyright 2026 Munich Quantum Software Stack Project
#
# Licensed under the Apache License, Version 2.0 with LLVM Exceptions (the
# "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://github.com/Munich-Quantum-Software-Stack/QDMI/blob/develop/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# ------------------------------------------------------------------------------

"""MQP-Database-Access Token module"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional

import pony.orm as pony  # type: ignore

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


class TokenExpirationAfterMaximum(TokenError):
    """This exception occurs when a token is created with an expiration that is before now."""

    def __init__(self, name: str):
        super().__init__(
            f"Token {name} being created with expiration after allowed time range."
        )


class TokenNotFound(TokenError):
    """This exception occurs when a identity attempts to find a token which doesn't exist."""

    def __init__(self, name: str, owner: str):
        super().__init__(f"Token {name} not found of identity {owner}.")


def add_new_token(
    name: str,
    owner: str,
    token: str,
    expiration: datetime,
    max_budget_usage: int,
    max_jobs: int,
) -> None:
    """Add a new token for a given identity to the database with an expiration."""

    # TODO verify token requirements, 64 character no underscore or dash

    # check if expiration is too soon
    if datetime.now() >= expiration:
        raise TokenExpirationBeforeNow(name)

    quantum_db = open_database()

    # check if expiration is past the allowed
    token_max_lifetime = quantum_db.User[owner].security_level.token_max_lifetime
    maximum_time = datetime.combine(
        datetime.now().date() + timedelta(days=token_max_lifetime), datetime.max.time()
    )

    if expiration > maximum_time:
        raise TokenExpirationAfterMaximum(name)

    token_count_limit = quantum_db.User[owner].security_level.token_max_live_count

    if (
        pony.count(
            token
            for token in quantum_db.Token
            if token.owner.identity == owner and token.revoked is False
        )
        >= token_count_limit
    ):
        raise TooManyTokensError(token_count_limit, owner)

    if TOKEN_PEPPER is None:
        raise RuntimeError("TOKEN_PEPPER is not set")
    token_hash = hashlib.sha256(token.encode() + TOKEN_PEPPER.encode()).hexdigest()

    if quantum_db.Token.exists(remember_name=name, owner=owner, revoked=False):
        raise TokenExistsError(name)

    quantum_db.Token(
        creation=datetime.now(),
        expiration=expiration,
        owner=owner,
        remember_name=name,
        token_hash=token_hash,
        max_budget_usage=max_budget_usage,
        max_jobs=max_jobs,
    )

    quantum_db.commit()


def revoke_token_by_name_and_identity(name: str, owner: str) -> None:
    """Revoke a given token by name and identity."""

    quantum_db = open_database()

    token = quantum_db.Token.get(owner=owner, remember_name=name, revoked=False)

    if token is None:
        raise TokenNotFound(name, owner)

    token.revoked = True
    token.revoke_reason = "user revoked"
    token.revoke_timestmap = datetime.now()

    quantum_db.commit()


def fetch_active_tokens_of_identity(owner: str) \
    -> list["Token"]:  # type: ignore   # noqa: F821
    """Fetch all tokens"""

    quantum_db = open_database()

    return quantum_db.Token.select(owner=owner, revoked=False)


def verify_token(token: str) -> Optional["Token"]:  # type: ignore  # noqa: F821
    """
    This function verifies that a received token exists in the database
    and then returns the related user.
    """

    # make sure token exists in database, then return user object

    quantum_db = open_database()

    if TOKEN_PEPPER is None:
        raise RuntimeError("TOKEN_PEPPER is not set")
    token_hash = hashlib.sha256(token.encode() + TOKEN_PEPPER.encode()).hexdigest()

    return quantum_db.Token.get(token_hash=token_hash, revoked=False)
