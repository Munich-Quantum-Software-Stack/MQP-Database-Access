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

"""MQP-Database-Access Database module"""

import os
from datetime import datetime
from pony.orm import Database, Optional, PrimaryKey, Required, Set  # type: ignore

# if os.getenv("QUANTUM_DB_TESTING") is not None:
#     db_config.set_test_env()


# pylint: disable=unused-variable
# pylint: disable=too-many-locals
def _define_entities(database: Database):  # pylint: disable=too-many-statements
    class User(database.Entity):
        """User account and profile entity."""
        _table_ = "user"

        identity = PrimaryKey(str, auto=False)
        note = Optional(str)
        email = Required(str)
        affiliation = Required(str)
        association = Required(str)

        security_level = Required("UserSecurityLevel")
        superuser_level = Optional("SuperUserLevel")

        owner = Optional("User", reverse="owned")
        owned = Set("User", reverse="owner")

        blocked = Required(bool, default=False)
        block_reason = Optional(str)

        secret_hash = Optional(str)
        force_secret_reset = Required(bool, default=True)

        last_login = Optional(datetime)
        last_secret_change = Optional(datetime)

        user_groups = Set("UserGroup", table="users_in_user_groups")
        owned_user_groups = Set("UserGroup", reverse="owner")

        tokens_owned = Set("Token")
        budgets_owned = Set("Budget")
        circuit_jobs = Set("CircuitJob")
        hamiltonian_jobs = Set("HamiltonianJob")
        feedbacks = Set("Feedback")

        time_slots = Set("TimeSlots", table="users_in_time_slots")

    class UserSecurityLevel(database.Entity):
        """User security policy limits entity."""
        _table_ = "user_security_level"

        name = PrimaryKey(str, auto=False)
        note = Optional(str)

        users = Set("User", reverse="security_level")

        token_max_live_count = Required(int)
        token_max_lifetime = Required(int)
        token_min_creation_interval = Required(int)
        token_max_jobs = Required(int)
        token_max_budget = Required(int)
        token_max_rate = Required(int)
        login_max_interval = Required(int)

    class SuperUserLevel(database.Entity):
        """Superuser permission set entity."""
        _table_ = "super_user_level"

        name = PrimaryKey(str, auto=False)
        note = Optional(str)

        users = Set("User", reverse="superuser_level")

        permission_user_creation = Required(bool)
        permission_user_blocking = Required(bool)
        permission_user_group_budget_assignment = Required(bool)
        permission_user_group_create = Required(bool)
        permission_user_group_user_add = Required(bool)
        permission_user_group_user_remove = Required(bool)
        permission_budget_create = Required(bool)
        permission_budget_split = Required(bool)

    class UserGroup(database.Entity):
        """User grouping and shared budget entity."""
        _table_ = "user_group"

        name = PrimaryKey(str, auto=False)
        note = Optional(str)
        users = Set("User", table="users_in_user_groups",
                    reverse="user_groups")
        budgets = Set("Budget", table="user_groups_in_budgets")
        time_slots = Set("TimeSlots", table="user_groups_in_time_slots")
        owner = Required("User")
        cost_modifier = Required(float)

    class Token(database.Entity):
        """Authentication token entity."""
        _table_ = "token"

        token_hash = PrimaryKey(str, auto=False)

        owner = Required("User")
        remember_name = Required(str, unique=True)

        creation = Required(datetime)
        expiration = Required(datetime)

        revoked = Required(bool, default=False)
        revoke_reason = Optional(str)
        revoke_timestamp = Optional(datetime)

        last_used = Optional(datetime)

        max_budget_usage = Required(int)
        max_jobs = Required(int)

        token_usage = Set("TokenUsage")

    class TokenUsage(database.Entity):
        """Mapping of token use to circuit jobs."""
        _table_ = "token_usage"

        job = Required("CircuitJob")
        token = Required("Token")

    class CircuitJob(database.Entity):
        """Circuit execution job entity."""
        _table_ = "circuit_job"

        id = PrimaryKey(int, auto=True)
        note = Optional(str)

        status = Required(str, default="PENDING")
        shots = Required(int)
        circuit = Required(str)
        circuit_format = Required(str)
        no_modify = Required(bool, default=False)
        timestamp_submitted = Required(datetime, default=datetime.now)
        timestamp_scheduled = Optional(datetime)
        timestamp_completed = Optional(datetime)
        timestamp_cancelled = Optional(datetime)

        cost = Optional(int)
        result = Optional(str)

        owner = Required("User")
        budget = Required("Budget")
        executed_resource = Optional("Resource")
        target_specification = Required("TargetSpecification")

        token_usage = Optional("TokenUsage")

        executed_circuit = Optional(str)

        queued = Required(bool, default=False)

    class HamiltonianJob(database.Entity):
        """Hamiltonian execution job entity."""
        _table_ = "hamiltonian_job"

        id = PrimaryKey(int, auto=True)
        note = Optional(str)
        status = Required(str, default="PENDING")
        interaction_str = Required(str)
        coefficients_str = Required(str)
        no_modify = Required(bool, default=False)
        timestamp_submitted = Required(datetime, default=datetime.now)
        timestamp_scheduled = Optional(datetime)
        timestamp_completed = Optional(datetime)
        timestamp_cancelled = Optional(datetime)

        cost = Optional(int)
        result = Optional(str)
        budget = Required("Budget")
        owner = Required("User")
        executed_resource = Optional("Resource")
        target_specification = Required("TargetSpecification")

    class Budget(database.Entity):
        """Budget allocation entity."""
        _table_ = "budget"

        name = PrimaryKey(str, auto=False)
        note = Optional(str)

        owner = Required("User")
        credits = Required(int)
        resources = Set("Resource", table="budget_resource")

        user_groups = Set("UserGroup", table="user_groups_in_budgets")
        circuit_jobs = Set("CircuitJob")
        hamiltonian_jobs = Set("HamiltonianJob")

    class TargetSpecification(database.Entity):
        """Execution target specification entity."""
        _table_ = "target_specification"

        name = PrimaryKey(str, auto=False)
        note = Optional(str)

        specification_type = Required(str)

        minimum_qubits = Optional(str)
        quantum_technology = Optional(str)
        resource_name = Optional(str)

        circuit_jobs = Set("CircuitJob")
        hamiltonian_jobs = Set("HamiltonianJob")

    class Resource(database.Entity):
        """Quantum resource entity."""
        _table_ = "resource"

        name = PrimaryKey(str, auto=False)
        note = Optional(str)

        maintenance = Required(bool, default=False)

        qubits = Required(int)
        connectivity = Required(str)
        instructions = Required(str)

        budgets = Set("Budget")
        quantum_technology = Required(str)

        resource_cost_modifier = Required(float)

        security_level = Required("ResourceSecurityLevel")
        circuit_jobs = Set("CircuitJob")
        hamiltonian_jobs = Set("HamiltonianJob")

        num_queued_jobs = Required(int, default=0)

        time_slots = Set("TimeSlots")

    class ResourceSecurityLevel(database.Entity):
        """Resource security policy limits entity."""
        _table_ = "resource_security_level"

        name = PrimaryKey(str, auto=False)
        note = Optional(str)

        job_min_interval = Required(int)
        budget_max_per_job = Required(int)
        unique_token_required = Required(bool)
        token_max_lifetime = Required(int)

        resources = Set("Resource")

    class Announcement(database.Entity):
        """Administrative announcement entity."""
        _table_ = "admin_announcements"

        id = PrimaryKey(int, auto=True)
        start_time = Required(datetime)
        end_time = Required(datetime)
        note = Required(str)
        title = Required(str)
        color = Optional(str, default="status_A1")

    class Pointer(database.Entity):
        """Homepage pointer/banner entity."""
        _table_ = "pane_pointers"

        id = PrimaryKey(int, auto=True)
        start_time = Required(datetime)
        end_time = Required(datetime)
        title = Required(str)
        note = Required(str)
        weight = Required(int)
        color = Optional(str, default="status_B1")

    class Feedback(database.Entity):
        """User feedback submission entity."""
        _table_ = "feedback"

        id = PrimaryKey(int, auto=True)
        owner = Required("User")
        rating = Optional(int)
        category = Required(str)
        date = Required(datetime)
        note = Required(str)

    class TimeSlots(database.Entity):
        """Resource availability time slot entity."""
        _table_ = "time_slots"

        id = PrimaryKey(int, auto=True)
        start_time = Required(datetime)
        end_time = Required(datetime)
        resource_name = Required("Resource")
        users = Set("User", table="users_in_time_slots")
        user_groups = Set("UserGroup", table="user_groups_in_time_slots")
        note = Optional(str)


# pylint: enable=too-many-locals
# pylint: enable=unused-variable


def _define_database(create_tables: bool = False, **db_params):
    db = Database(**db_params)

    _define_entities(db)

    db.generate_mapping(create_tables=create_tables)

    return db


def open_database(create_tables: bool = False):
    """Create and return a database connection configured from environment variables."""

    if os.getenv("QUANTUM_DB_TESTING") is not None and [os.getenv("USER_TESTING") == ""
    or os.getenv("USER_TESTING") is None]:
        return _define_database(
            create_tables=create_tables,
            provider="sqlite",
            filename=os.getcwd() + "/" + str(os.getenv("QUANTUM_DB_FILENAME")),
            create_db=True,
        )

    return _define_database(
        provider="postgres",
        user=os.getenv("QUANTUM_DB_USER"),
        password=os.getenv("QUANTUM_DB_PASS"),
        host=os.getenv("QUANTUM_DB_HOST"),
        database="quantumdb",
    )
