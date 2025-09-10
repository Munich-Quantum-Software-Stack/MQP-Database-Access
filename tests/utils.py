#!/usr/bin/env python3
import psycopg2
import os
import numpy as np
from datetime import datetime, timedelta
import bqp_database_access as db_access

"""
Following queries are used to populate data to test specific features
"""

sql_queries = {
    "user": """INSERT INTO public.user (
            identity,   note,                  email,          affiliation,     association,        security_level,                     superuser_level, \
            owner,      blocked,               block_reason,   secret_hash,     force_secret_reset, last_login,                         last_secret_change \
        ) VALUES (
            %s::text,   'The test user'::text, %s::text,       'LRZ QCT'::text, 'LDAP'::text,       'BASIC'::text,                      Null::text, \
            Null::text, false::boolean,        'Naught'::text, 'Naught'::text,  false::boolean,      Null::timestamp without time zone, Null::timestamp without time zone \
        ) returning identity;""",
    "circuit_job": """INSERT INTO public.circuit_job (
            id,         note,                 status,               shots,               circuit,              circuit_format, \
            no_modify,  timestamp_submitted,  timestamp_scheduled,  timestamp_completed, timestamp_cancelled,  cost, \
            result,     owner,                budget,               executed_resource,   target_specification, executed_circuit, \
            queued
        ) VALUES (
            %s,        %s,           %s::text,    10000,               'OPENQASM 2.0'::text, 'circuit format', \
            false::boolean , %s::timestamp,   %s::timestamp,        %s::timestamp,       %s::timestamp,         %s, \
            'PASS',     'testuser1'::text,                'temp_budget1',          Null::text,         'qubits sim',         'done', 
            true::boolean )  \
            ; """,
    "budget": """INSERT INTO public.budget (name, note, owner, credits) VALUES \
            (%s::text, 'temporary budget'::text, %s::text, 10) returning name;""",
    "target_specification": """INSERT INTO public.target_specification (
                name ,       note,          specification_type , minimum_qubits, quantum_technology, resource_name \
            ) VALUES (
                'qubits sim', 'qubit sim',  'spec'             , '1000'::text,   'ion trap',         'resource 1'); """,
    "admin" : """INSERT INTO public.admin_announcements (
                    id,     start_time,      end_time,           note,   title,              color)
              VALUES (
                  %s, %s::timestamp,   %s::timestamp,     'admin', 'title',         'status_A1'
                  )"""
}


def clear_all_data():
    """
    Making sure DB is empty before populating new data
    """
    connection = psycopg2.connect(
        dbname="quantumdb",
        user=os.getenv("QUANTUM_DB_USER"),
        password=os.getenv("QUANTUM_DB_PASS"),
        host=os.getenv("QUANTUM_DB_HOST"),
        port=5432,
    )
    cur = connection.cursor()

    for table_name in ["user", "circuit_job"]:
        clear_table_sql = """TRUNCATE public.""" + table_name + """ CASCADE;"""
        cur.execute(clear_table_sql)


def insert_random_data(table_name, n_entries=10, clear_table=True):
    """
    insertion of dummy data for testing purpose
    """
    connection = psycopg2.connect(
        dbname="quantumdb",
        user=os.getenv("QUANTUM_DB_USER"),
        password=os.getenv("QUANTUM_DB_PASS"),
        host=os.getenv("QUANTUM_DB_HOST"),
        port=5432,
    )

    cur = connection.cursor()
    if clear_table:
        clear_table_sql = """TRUNCATE public.""" + table_name + """ CASCADE;"""
        cur.execute(clear_table_sql)

    if table_name == "user":
        for i in range(0, n_entries):
            identity = "testuser" + str(i)
            email = identity + "@lrz.de"
            values = (identity, email)
            cur.execute(sql_queries["user"], values)

    if table_name == "circuit_job":
        start_date = datetime(2024, 1, 1, 0, 0, 0)
        end_date = datetime(2025, 12, 31, 23, 59, 59)
        cur.execute("""TRUNCATE public.budget CASCADE;""")
        cur.execute("""TRUNCATE public.admin_announcements CASCADE;""")
        cur.execute("""TRUNCATE public.target_specification CASCADE;""")
        cur.execute(sql_queries["target_specification"])
        for i in range(0, n_entries):
            id = i
            identity = "testuser" + str(id)
            name = "temp_budget" + str(id)
            cur.execute(
                sql_queries["budget"],
                (
                    name,
                    identity,
                ),
            )

        for i in range(0, n_entries):
            id = i
            time_difference = end_date - start_date
            total_seconds = int(time_difference.total_seconds())
            random_seconds = np.random.randint(0, total_seconds)
            random_timestamp = start_date + timedelta(seconds=random_seconds)

            random_cost = np.random.randint(10, 100)
            if i%2 == 0:
                values = (
                    id,
                    'COMPLETED',
                    'COMPLETED',
                    random_timestamp,
                    random_timestamp + timedelta(hours=1),
                    random_timestamp + timedelta(hours=2),
                    None,
                    random_cost,
                )
            else:
                values = (
                    id,
                    'CANCELLED',
                    'CANCELLED',
                    random_timestamp,
                    random_timestamp + timedelta(hours=1),
                    None,
                    random_timestamp + timedelta(hours=2),
                    random_cost,
                )
            cur.execute(sql_queries["circuit_job"], values)
            
            values = (id, random_timestamp, random_timestamp + timedelta(hours=2))
            cur.execute(sql_queries["admin"], values)

    connection.commit()
    cur.close()
    connection.close()