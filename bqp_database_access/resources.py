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

"""MQP-Database-Access Resource module"""

import os
import json
from pathlib import Path
from typing import Optional
from warnings import warn
from pony.orm import db_session  # type: ignore
from ._database import open_database

ROOT_PATH = Path(os.path.dirname(os.path.abspath(__file__))).parent
JSON_FILE_PATH = "scripts/restricted_resources_to_usergroup.json"
RESTRICTED_RESOURCE_FILE = os.path.join(ROOT_PATH, JSON_FILE_PATH)
# Read json file
with open(RESTRICTED_RESOURCE_FILE, "r", encoding="utf-8") as f:
    RESTRICTED_RESOURCE_CONFIG = json.load(f)

@db_session
def fetch_all_resources() -> set["Resource", ...]:  # type: ignore  # noqa: F821
    """Fetch all resources."""

    quantum_db = open_database()

    resources = quantum_db.Resource.select()
    all_resources = {resource for resource in resources}  # pylint: disable=R1721

    return all_resources


@db_session
def fetch_all_resource_names() -> list[str]:
    """Fetch all resource names."""

    quantum_db = open_database()

    resources = quantum_db.Resource.select()
    all_resource_names = [resource.name for resource in resources]

    return all_resource_names


@db_session
def fetch_all_target_specification_names() -> list[str]:
    """Fetch all target specification names."""

    quantum_db = open_database()

    target_specifications = quantum_db.TargetSpecification.select()
    target_specification_names = [target.name for target in target_specifications]

    return target_specification_names


@db_session
def fetch_resources_available_to_identity(
    identity: str,
) -> set["Resource", ...]:  # type: ignore  # noqa: F821
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
def get_all_restricted_usergroups() -> list[str]:
    return list(RESTRICTED_RESOURCE_CONFIG.keys())

@db_session
def get_group_rule(usergroup: str, is_member: bool) -> dict | None:
    group = RESTRICTED_RESOURCE_CONFIG.get(usergroup)
    if not group:
        return None
    key = "member" if is_member else "non_member"
    return group.get(key)

@db_session
def get_excluded_restricted_resources(usergroup: str, is_member: bool) -> list[str]:
    rule = get_group_rule(usergroup, is_member)
    exclusive_resources_list = rule.get("exclusive_resources", []) if rule else []
    return exclusive_resources_list

@db_session
def get_inclusive_restricted_resources(usergroup: str, is_member: bool) -> list[str]:
    rule = get_group_rule(usergroup, is_member)
    inclusive_resources_list = rule.get("inclusive_resources", []) if rule else []
    return inclusive_resources_list

@db_session
def fetch_resource_names_restricted_to_identity(identity: str) -> list[str]:
    """Restrict users access to resources."""
    quantum_db = open_database()
    user = quantum_db.User.get(identity=identity)
    restricted_resource_names = []
    _user_group_names = [user_group.name.upper() for user_group in user.user_groups]
    _restricted_usergroups = get_all_restricted_usergroups()
    for r_usergroup in _restricted_usergroups:
        is_member = r_usergroup in _user_group_names

        exclusive_resources = get_excluded_restricted_resources(r_usergroup, is_member)
        if exclusive_resources:
            restricted_resource_names = fetch_all_resource_names()
            for r in exclusive_resources:
                if r in restricted_resource_names:
                    restricted_resource_names.remove(r)
        else:
            inclusive_resources = get_inclusive_restricted_resources(r_usergroup, is_member)
            if inclusive_resources:
                restricted_resource_names.extend(inclusive_resources)

    return restricted_resource_names


@db_session
def fetch_resources_restricted_to_identity(
    identity: str,
) -> set["Resource", ...]:  # type: ignore  # noqa: F821
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

    warn(
        "set_maintenance is deprecated, use update_resource_status instead",
        DeprecationWarning,
        stacklevel=2,
    )

    quantum_db = open_database()

    resource = quantum_db.Resource.get(name=name)

    if resource is not None:
        resource.maintenance = value
        return True
    # Resource not found
    return False


def fetch_resource_attributes_for_transpilation(name: str) -> tuple[int, str, str]:
    """Fetch qubits, connectivity and instructions for the specified resource"""

    return fetch_resource_info(name)


@db_session
def update_resource_status(
    name: str, maintenance: bool, num_queued_jobs: int = 0
) -> bool:
    """Update the maintenance flag and number of queued jobs of a resource"""

    quantum_db = open_database()

    resource = quantum_db.Resource.get(name=name)

    if resource is not None:
        resource.maintenance = maintenance
        resource.num_queued_jobs = num_queued_jobs
        return True
    # Resource not found
    return False


@db_session
def update_resource_info(
    name: str, num_qubits: int, connectivity: str, instructions: str
) -> bool:
    """Update the qubits, connectivity and instructions of a resource"""

    quantum_db = open_database()

    resource = quantum_db.Resource.get(name=name)

    if resource is not None:
        resource.qubits = num_qubits
        resource.connectivity = connectivity
        resource.instructions = instructions
        return True
    # Resource not found
    return False


@db_session
def fetch_resource_info(name: str) -> Optional[tuple[int, str, str]]:
    """Fetch the qubits, connectivity and instructions of a resource"""

    quantum_db = open_database()

    resource = quantum_db.Resource.get(name=name)

    if resource is None:
        return None

    return (resource.qubits, resource.connectivity, resource.instructions)


@db_session
def fetch_resource_num_queued_jobs(name: str) -> Optional[int]:
    """Fetch the number of queued jobs for a resource"""

    quantum_db = open_database()

    resource = quantum_db.Resource.get(name=name)

    if resource is None:
        # Resource not found
        return None

    return resource.num_queued_jobs
