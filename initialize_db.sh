#!/bin/bash
set -e
set -x  # **print every command** before running it
echo "🏗️  Running container initialization..."

# Wait a bit for PostgreSQL to start
sleep 2

# go into docker of qdb with docker exec -it name-of-docker-container /bin/bash
apt update
apt install -y git vim python3.11 pipx python3-pip sudo net-tools postgresql postgresql-contrib systemctl
export QUANTUM_DB_USER="postgres" # set different user, if needed
export QUANTUM_DB_PASS="example" # set different password, if needed
export QUANTUM_DB_HOST="localhost" # change accordingly, if needed
systemctl start postgresql.service # -> or service postgresql start /// If it is running can be checked with systemctl status postgresql.service
cd bqp-database-access/
pipx install pdm
pipx ensurepath
PYTHONPATH=$PWD # add local repository to pythonpath such that the repo with our development-features is used
cd ..
mkdir bqp-project
cd bqp-project
python3 -m venv bqp-project
source bqp-project/bin/activate
cd ../bqp-database-access/
pip uninstall bqp_database_access # otherwise python uses the pypi-version of bqp_database_access and we want it to use the local repository
pip install . # install dependencies specified in .toml
sed -i 's/^port = .*/port = 5432/' /etc/postgresql/*/main/postgresql.conf
# Create database
echo "Creating database quantumdb..."
psql -p 5432 -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE quantumdb OWNER $POSTGRES_USER;
EOSQL


# Optional: initialize via Python
python3 - <<'EOF'
import os, sys
sys.path.append('/bqp-database-access')
import bqp_database_access as db

db._database._define_database(
    create_tables=True,
    provider="postgres",
    user=os.getenv("QUANTUM_DB_USER", "postgres"),
    password=os.getenv("QUANTUM_DB_PASS", "example"),
    host=os.getenv("QUANTUM_DB_HOST", "localhost"),
    database="quantumdb"
)
EOF

echo "✅ Initialization complete!"
# Run your SQL files
echo "Running SQL initialization scripts..."
psql -U "$POSTGRES_USER" -d quantumdb -f /bqp-database-access/insert_resource.sql
psql -U "$POSTGRES_USER" -d quantumdb -f /bqp-database-access/prepare_test_db.sql
