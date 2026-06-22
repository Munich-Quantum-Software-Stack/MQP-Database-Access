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
def fetch_all_resources() -> set["Resource", ...]:  # type: ignore
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
) -> set["Resource", ...]:  # type: ignore
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
    return RESTRICTED_RESOURCE_CONFIG.get("restricted_usergroup", [])

@db_session
def get_restricted_usergroup(usergroup):
    return RESTRICTED_RESOURCE_CONFIG.get(restricted_usergroup=usergroup)

@db_session
def get_excluded_restricted_resources(usergroup: str) -> list[str]:
    restricted_usergroup = get_restricted_usergroup(usergroup)
    exclusive_resources_list = restricted_usergroup.get("exclusive_resources", [])
    return exclusive_resources_list

@db_session
def get_inclusive_restricted_resources(usergroup: str) -> list[str]:
    restricted_usergroup = get_restricted_usergroup(usergroup)
    inclusive_resources_list = restricted_usergroup.get("inclusive_resources", [])
    return inclusive_resources_list

@db_session
def fetch_resource_names_restricted_to_identity(identity: str) -> list[str]:
    """Restrict users access to resources."""
    quantum_db = open_database()
    user = quantum_db.User.get(identity=identity)
    _user_group_names = [user_group.name.upper() for user_group in user.user_groups]
    _restricted_usergroups = get_all_restricted_usergroups()
    for r_usergroup in _restricted_usergroups:
        config_restricted_usergroup = get_restricted_usergroup(r_usergroup)
        if r_usergroup in _user_group_names and \
            config_restricted_usergroup.get("in_usergroup") is True:
            # The exclusive_resources is not None \
            # then inclusive_resources must be None and vice versa
            exclusive_resources = get_excluded_restricted_resources(r_usergroup)
            if exclusive_resources is not None:
                restricted_resource_names = fetch_all_resource_names()
                restricted_resource_names.remove(r for r in exclusive_resources)
            else:
                inclusive_resources = get_inclusive_restricted_resources(r_usergroup)
                restricted_resource_names.append(r for r in inclusive_resources)
        elif r_usergroup not in _user_group_names \
            and config_restricted_usergroup.get("in_usergroup") is False:
            inclusive_resources = get_inclusive_restricted_resources(r_usergroup)
            if inclusive_resources is not None:
                restricted_resource_names.append(r for r in inclusive_resources)
        else:
            exclusive_resources = get_excluded_restricted_resources(r_usergroup)
            if exclusive_resources is not None:
                restricted_resource_names = fetch_all_resource_names()
                restricted_resource_names.remove(r for r in exclusive_resources)

    restricted_resource_names = []
    return restricted_resource_names


@db_session
def fetch_resources_restricted_to_identity(
    identity: str,
) -> set["Resource", ...]:  # type: ignore
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
