from datetime import datetime

from pony.orm import count
from bcrypt import hashpw

from . import _open_database, PEPPER


class TokenError(Exception):
    def __init__(self):
        super().__init__()


class TooManyTokensError(TokenError):
    def __init__(self, count: int, user: str):
        self.count = count
        self.user = user

        super().__init__(f"Users are not allowed to have more than {count} tokens.")


class TokenExistsError(TokenError):
    def __init__(self, token_name: str):
        super().__init__(f"Token '{token_name}' already exists.")


class TokenNotFound(TokenError):
    def __init__(self, name: str, owner: str):
        super().__init__(f"Token {name} not found of user {owner}.")


def add_new_token(name: str, owner: str, token: str, expiration: datetime) -> None:
    # TODO check expiration is past datetime.now()

    quantum_db = _open_database()

    # TODO add as configuration
    token_count_limit = 100

    if (
        count(token for token in quantum_db.Token if token.revoked == False)
        >= token_count_limit
    ):
        raise TooManyTokensError(token_count_limit, owner)

    peppered_token_hash = hashpw(token.encode() + PEPPER).decode()

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
    quantum_db = _open_database()

    token = quantum_db.Token.get(owner=owner, remember_name=name, revoked=False)

    if token is None:
        raise TokenNotFound(name, owner)

    token.revoked = True
    token.revoke_reason = f"User revoked token {datetime.now()}"

    quantum_db.commit()


def fetch_active_tokens_of_user(owner: str) -> list["Token"]:
    quantum_db = _open_database()

    return list(quantum_db.Token.select(owner=owner, revoked=False))
