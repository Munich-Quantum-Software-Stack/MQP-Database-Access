#!/usr/bin/env python3
import psycopg2
import os

# --- Configuration ---
DB_NAME = 'quantumdb'
DB_USER = 'postgres'
DB_PASSWORD = 'postgres'
DB_HOST = 'db'
DB_PORT = '5432'
IMPORT_DIR = '/workspaces/bqp-database-access/qdb-csv'

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
)
cur = conn.cursor()

# Iterate over CSV files in the import directory and import data into corresponding tables
for filename in os.listdir(IMPORT_DIR):
    if filename.endswith(".csv"):
        table_name = filename[:-4]  # Remove the .csv extension to get the table name
        csv_file = os.path.join(IMPORT_DIR, filename)
        with open(csv_file, 'r') as f:
            if table_name == 'user':
                copy_sql = f"COPY \"{table_name}\" FROM STDIN WITH CSV HEADER"
            else:
                copy_sql = f"COPY {table_name} FROM STDIN WITH CSV HEADER"
            cur.copy_expert(copy_sql, f)
        print(f"Imported data from {csv_file} into table '{table_name}'")

conn.commit()
cur.close()
conn.close()
