"""
This module provides the basic database structure and helpers.
"""

import os
from datetime import datetime
from pony.orm import Database, Optional, PrimaryKey, Required, Set  # type: ignore


# if os.getenv("QUANTUM_DB_TESTING") is not None:
#     db_config.set_test_env()


# pylint: disable=unused-variable
# pylint: disable=too-many-locals
def _define_entities(database: Database):  # pylint: disable=too-many-statements
    class User(database.Entity):
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
        _table_ = "user_group"

        name = PrimaryKey(str, auto=False)
        note = Optional(str)
        users = Set("User", table="users_in_user_groups", reverse="user_groups")
        budgets = Set("Budget", table="user_groups_in_budgets")
        time_slots = Set("TimeSlots", table="user_groups_in_time_slots")
        owner = Required("User")
        cost_modifier = Required(float)

    class Token(database.Entity):
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
        _table_ = "token_usage"

        job = Required("CircuitJob")
        token = Required("Token")

    class CircuitJob(database.Entity):
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

        timestamp_data = Optional("TimestampData", reverse="circuit_job")

    class TimestampData(database.Entity):
        """Table for storing job metrics.
        For each metric, there are two corresponding columns in the table reffering to start and finist times as timestamps.
        Coloumns:
            api_entry: timestamp when the job entered the MQP API
            api_exit: timestamp when the job exited the MQP API
            qdb_entry: timestamp when the job entered the QuantumDB
            qdb_exit: timestamp when the job exited the QuantumDB
            qjr_entry: timestamp when the job entered the MQSS Quantum Job Runner
            qjr_exit: timestamp when the job exited the MQSS Quantum Job Runner
            isv_jr_entry: timestamp when the job entered the ISV Job Runner
            isv_jr_exit: timestamp when the job exited the ISV Job Runner
            quantum_daemon_jr_entry: timestamp when the job entered the Quantum Daemon Job Runner
            quantum_daemon_jr_exit: timestamp when the job exited the Quantum Daemon Job Runner
            generator_entry: timestamp when the job entered the circuit generator
            generator_exit: timestamp when the job exited the circuit generator
            scheduler_entry: timestamp when the job entered the scheduler
            scheduler_exit: timestamp when the job exited the scheduler
            pass_runner_entry: timestamp when the job entered the pass runner
            pass_runner_exit: timestamp when the job exited the pass runner
            passes_applied: dictionary listing entry and exit-times for each pass applied
            transpiler_entry: timestamp when the job entered the transpiler
            transpiler_exit: timestamp when the job exited the transpiler
            submitter_entry: timestamp when the job entered the submitter
            submitter_exit: timestamp when the job exited the submitter
            pass_selection_entry: timestamp when the job entered the pass selection
            pass_selection_exit: timestamp when the job exited the pass selection
            knitter_entry: timestamp when the job entered the knitter
            knitter_exit: timestamp when the job exited the knitter
            job_execution_start: timestamp when the job started execution on the quantum hardware
            job_execution_end: timestamp when the job finished execution on the quantum hardware
        """

        _table_ = "timestamp_data"
        circuit_job = Required(CircuitJob, reverse="timestamp_data")

        api_entry = Required(datetime)
        api_exit = Required(datetime)

        qdb_entry = Optional(datetime)
        qdb_exit = Optional(datetime)

        qjr_entry = Optional(datetime)
        qjr_exit = Optional(datetime)

        isv_jr_entry = Optional(datetime)
        isv_jr_exit = Optional(datetime)

        quantum_daemon_jr_entry = Optional(datetime)
        quantum_daemon_jr_exit = Optional(datetime)

        generator_entry = Optional(datetime)
        generator_exit = Optional(datetime)

        scheduler_entry = Optional(datetime)
        scheduler_exit = Optional(datetime)

        pass_runner_entry = Optional(datetime)
        pass_runner_exit = Optional(datetime)

        passes_applied = Optional(
            datetime
        )  # This is a dictionary listing entry and exit-times for passes

        transpiler_entry = Optional(datetime)
        transpiler_exit = Optional(datetime)

        submitter_entry = Optional(datetime)
        submitter_exit = Optional(datetime)

        pass_selection_entry = Optional(datetime)
        pass_selection_exit = Optional(datetime)

        knitter_entry = Optional(datetime)
        knitter_exit = Optional(datetime)

        job_execution_start = Optional(datetime)
        job_execution_end = Optional(datetime)

    class HamiltonianJob(database.Entity):
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
        _table_ = "resource_security_level"

        name = PrimaryKey(str, auto=False)
        note = Optional(str)

        job_min_interval = Required(int)
        budget_max_per_job = Required(int)
        unique_token_required = Required(bool)
        token_max_lifetime = Required(int)

        resources = Set("Resource")

    class Announcement(database.Entity):
        _table_ = "admin_announcements"

        id = PrimaryKey(int, auto=True)
        start_time = Required(datetime)
        end_time = Required(datetime)
        note = Required(str)
        title = Required(str)
        color = Optional(str, default="status_A1")

    class Pointer(database.Entity):
        _table_ = "pane_pointers"

        id = PrimaryKey(int, auto=True)
        start_time = Required(datetime)
        end_time = Required(datetime)
        title = Required(str)
        note = Required(str)
        weight = Required(int)
        color = Optional(str, default="status_B1")

    class Feedback(database.Entity):
        _table_ = "feedback"

        id = PrimaryKey(int, auto=True)
        owner = Required("User")
        rating = Optional(int)
        category = Required(str)
        date = Required(datetime)
        note = Required(str)

    class TimeSlots(database.Entity):
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


def _define_database(create_tables: bool = False, **db_params) -> Database:

    db = Database(**db_params)

    _define_entities(db)

    try:
        db.generate_mapping(create_tables=create_tables)
    except Exception as e:
        print(e)

    return db


def open_database(create_tables: bool = False) -> Database:
    if os.getenv("QUANTUM_DB_TESTING") is not None and [
        os.getenv("USER_TESTING") == "" or os.getenv("USER_TESTING") is None
    ]:
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
