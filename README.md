# MQP-Database-Access (Unfinished)

`MQP-Database-Access` is the database access component of the Munich Quantum Portal (MQP) Dashboard and part of the Munich Quantum Software Stack (MQSS).

This repository provides a Python package (`bqp_database_access`) for working with MQP data models and database operations. It is a database access library (not a Flask backend service).

## Features

- Database schema and entity definitions built with Pony ORM.
- Data-access modules for users, budgets, jobs, tokens, resources, time slots, feedback, and status handling.
- Support for test/local SQLite and PostgreSQL-backed operation.
- Utility scripts for CSV import/export and SQL-based time-slot inserts.
- Automated tests with `pytest` and coverage reporting via `pytest-cov`.

## Tech stack

- Python (>=3.10, <3.12)
- [PDM](https://pdm-project.org/) for dependency and environment management
- Pony ORM
- PostgreSQL / SQLite
- pytest + pytest-cov
- Developer tooling: black, isort, mypy, pylint, pre-commit

## Repository structure

```text
bqp_database_access/      # Main package
tests/                    # Pytest test suite
scripts/                  # CSV import/export and SQL helper scripts
pyproject.toml            # Project/dependency/test/tool configuration
.gitlab-ci.yml            # Current GitLab CI lint/type-check pipeline
README.md                 # Project documentation
```

## Installation (PDM)

From the repository root:

```bash
pdm install
```

For development dependencies explicitly:

```bash
pdm install -G dev
```

## Environment variables

The package and tests rely on environment variables for database configuration and security-related values.

Important variables:

- `QUANTUM_DB_TESTING`
- `QUANTUM_DB_FILENAME`
- `QUANTUM_DB_USER`
- `QUANTUM_DB_PASS`
- `QUANTUM_DB_HOST`
- `QUANTUM_DB_PEPPER`
- `QUANTUM_DB_TOKEN_PEPPER`

Current test defaults are configured in `pyproject.toml` via `pytest-env` (for example `QUANTUM_DB_TESTING=TRUE` and `QUANTUM_DB_FILENAME=test_db.sqlite`).

> Note: `.env.example` is not currently present in this repository. Add one before public release to document required runtime variables.

## Usage

Install dependencies and run Python code against the package modules, for example:

```python
import bqp_database_access as db_access

# access functional modules
# db_access.users
# db_access.jobs
# db_access.resources
```

The package also exposes `create_app()` only as a compatibility symbol for integrations; this repository itself is focused on database access logic.

## Testing

Run tests from the project root:

```bash
pdm run pytest
```

## Coverage

Coverage is already configured in `pyproject.toml` and enabled in `pytest` addopts.

Running:

```bash
pdm run pytest
```

produces:

- terminal coverage output (`term-missing`)
- `coverage.xml`

Coverage is scoped to `bqp_database_access` and omits underscore-prefixed/internal modules configured under `[tool.coverage.run]`.

## Utility scripts

Available helper scripts:

- `scripts/import_from_csv.py` – imports CSV files into PostgreSQL tables.
- `scripts/export_to_csv.py` – exports PostgreSQL tables to CSV files.
- `scripts/insert_time_slot.sql` – SQL helper for time-slot data insertion.

These scripts currently contain environment-specific paths and connection defaults; review and adapt them for your deployment setup before use.

## Security notes

- Never commit real database credentials, peppers, or token-pepper values.
- Keep secrets in local environment configuration (for example a local `.env` file that is gitignored).
- Treat `QUANTUM_DB_PEPPER` and `QUANTUM_DB_TOKEN_PEPPER` as sensitive cryptographic secrets.
- Ensure production secrets differ from development/testing values.

## Development workflow

Common local workflow:

1. Install dependencies with `pdm install -G dev`.
2. Run tests: `pdm run pytest`.
3. Run type checks and linting used in CI:
   - `pdm run mypy bqp_database_access/`
   - `pdm run pylint bqp_database_access/`

Current CI configuration is present in `.gitlab-ci.yml` and runs mypy + pylint.

## Public-release TODO

Before public release, add or verify the following repository-level documents:

- `LICENSE` (currently missing in repository root)
- `CONTRIBUTING.md` (currently missing)
- `CODE_OF_CONDUCT.md` (currently missing)
- `.env.example` (currently missing, recommended)