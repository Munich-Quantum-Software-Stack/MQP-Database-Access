#!/usr/bin/env python3
import psycopg2
import os

# --- Configuration ---
# DB_NAME = 'quantumdb'
# DB_USER = os.getenv('QUANTUM_DB_USER')
# DB_PASSWORD = os.getenv('QUANTUM_DB_PASS')
# DB_HOST = os.getenv('QUANTUM_DB_HOST')
# DB_PORT = '5432'
# EXPORT_DIR = '/workspaces/bqp-database-access/qdb-csv'

DB_NAME = 'quantumdb'
DB_USER = 'postgres'
DB_PASSWORD = 'postgres'
DB_HOST = 'db'
DB_PORT = '5432'
EXPORT_DIR = '/workspaces/bqp-database-access/qdb-csv'

# Create export directory if it doesn't exist
os.makedirs(EXPORT_DIR, exist_ok=True)

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
)
cur = conn.cursor()

# Get list of tables from the public schema
cur.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';")
tables = cur.fetchall()

for table in tables:
    table_name = table[0]
    csv_file = os.path.join(EXPORT_DIR, f"{table_name}.csv")
    with open(csv_file, 'w') as f:
        if table_name == 'user':
            copy_sql = f"COPY \"{table_name}\" TO STDOUT WITH CSV HEADER"
        else:
            copy_sql = f"COPY {table_name} TO STDOUT WITH CSV HEADER"
        cur.copy_expert(copy_sql, f)
    print(f"Exported table '{table_name}' to {csv_file}")

cur.close()
conn.close()
