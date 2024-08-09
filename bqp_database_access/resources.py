"""This module contains all helpers related to resources in the database."""

from ._database import open_database

from pony.orm import db_session  # type: ignore


@db_session
def fetch_all_resources() -> tuple["Resource", ...]:
    """Fetch all resources."""

    quantum_db = open_database()

    resources = quantum_db.Resource.select()
    all_resources = {resource for resource in resources}

    return all_resources


@db_session
def fetch_all_target_specification_names() -> list[str]:
    """Fetch all target specification names."""

    quantum_db = open_database()

    target_specifications = quantum_db.TargetSpecification.select()
    target_specification_names = [target.name for target in target_specifications]

    return target_specification_names


@db_session
def fetch_resources_available_to_identity(identity: str) -> tuple["Resource", ...]:
    """Fetch all budgets."""

    _restricted_resource_names = fetch_resource_names_restricted_to_identity(identity)
    quantum_db = open_database()

    resources = quantum_db.Resource.select()
    user_resources = {
        resource
        for resource in resources
        if resource.name not in _restricted_resource_names
    }

    return user_resources
    # TODO reactivate after budgeting is implemented
    # quantum_db = open_database()

    # user = quantum_db.User.get(identity=identity)

    # user_group_budget_resources = {
    #    resource
    #    for user_group in user.user_groups
    #    for budget in user_group.budgets
    #    for resource in budget.resources
    # }

    # return user_group_budget_resources


@db_session
def fetch_resource_names_restricted_to_identity(identity: str) -> list[str]:
    """Restrict users access to resources."""

    quantum_db = open_database()

    user = quantum_db.User.get(identity=identity)
    _user_group_names = [user_group.name.upper() for user_group in user.user_groups]

    restricted_resource_names = []

    # Hardcode any restrictions here
    # TODO after budgeting, replace implement restrictions through budget allocation.
    if "IQM" in _user_group_names:
        restricted_resource_names.append("WMI3")
        restricted_resource_names.append("AQT20")

    return restricted_resource_names


@db_session
def fetch_resources_restricted_to_identity(identity: str) -> tuple["Resource", ...]:
    """Restrict users access to resources."""

    restricted_resource_names = fetch_resource_names_restricted_to_identity(identity)
    resources = fetch_all_resources()
    restricted_resources = {
        resource for resource in resources if resource.name in restricted_resource_names
    }

    return restricted_resources


@db_session
def fetch_resource_names_available_to_identity(identity: str) -> list[str]:
    """Fetch all resource names that a user can access/have budget."""

    _restricted_resource_names = fetch_resource_names_restricted_to_identity(identity)
    quantum_db = open_database()

    available_resource_names = [
        _resource.name
        for _resource in quantum_db.Resource.select()
        if _resource.maintenance is False
    ]

    for _restricted_resource in _restricted_resource_names:
        if _restricted_resource in available_resource_names:
            available_resource_names.remove(_restricted_resource)

    return available_resource_names


@db_session
def set_maintenance(name: str, value: bool) -> bool:
    """Sets the maintenance entry of a given resource"""

    quantum_db = open_database()

    resource = quantum_db.Resource.get(name=name)

    if resource is not None:
        resource.maintenance = value
        return True
    # Resource not found
    return False


@db_session
def fetch_resource_attributes_for_transpilation(name: str) -> tuple[int, str, str]:
    """Fetch qubits, connectivity and instructions for the specified resource"""

    quantum_db = open_database()

    resource = quantum_db.Resource.get(name=name)

    if resource is None:
        return None

    return (resource.qubits, resource.connectivity, resource.instructions)
