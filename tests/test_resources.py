from pony.orm import db_session
from bqp_database_access.resources import (
    fetch_resource_names_restricted_to_identity
)
import pytest
pytestmark = pytest.mark.usefixtures("seeded_db")


def test_fetch_resource_names_restricted_to_identity_in_EQE_group(seeded_db):
    #qdb = seeded_db
    identity = "test_eqe_user"
    with db_session:
        restricted_resources = fetch_resource_names_restricted_to_identity(identity=identity)
        assert("EQE1" not in restricted_resources)

def test_fetch_resource_names_restricted_to_identity_not_in_EQE_group(seeded_db):
    identity = "test_user"
    with db_session:
        restricted_resources = fetch_resource_names_restricted_to_identity(identity=identity)
        assert("EQE1" in restricted_resources)