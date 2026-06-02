# MQP-Database-Access

[![CI](https://github.com/Munich-Quantum-Software-Stack/MQP-Database-Access/actions/workflows/ci.yml/badge.svg)](https://github.com/Munich-Quantum-Software-Stack/MQP-Database-Access/actions/workflows/ci.yml)

## Overview

`MQP-Database-Access` is the Python database access package for the Munich Quantum Portal (MQP) Dashboard and part of the Munich Quantum Software Stack (MQSS).

It provides ORM-backed data access modules for domain entities such as users, jobs, resources, budgets, tokens, time slots, feedback, and status handling.

## Features

- Python package: `bqp_database_access`
- Database access logic built on Pony ORM
- Support for testing/local SQLite and PostgreSQL-backed usage
- Utility scripts for CSV import/export and SQL time-slot insertion

## Getting Started

1. Install [PDM](https://pdm-project.org/).
2. Clone this repository.
3. Install dependencies and developer tools:

```bash
git clone https://github.com/Munich-Quantum-Software-Stack/MQP-Database-Access.git
cd MQP-Database-Access
pdm install

```

## Environment Variables

The package and test setup rely on the following environment variables:

- `QUANTUM_DB_TESTING`
- `QUANTUM_DB_FILENAME`
- `QUANTUM_DB_USER`
- `QUANTUM_DB_PASS`
- `QUANTUM_DB_HOST`
- `QUANTUM_DB_PEPPER`
- `QUANTUM_DB_TOKEN_PEPPER`

Use `.env.example` as a template for local configuration, then set environment-specific secret values before running tests or integrations.

## Running Tests

```bash
pdm run pytest
```

## Type Checking and Linting

```bash
pdm run mypy bqp_database_access/
pdm run pylint bqp_database_access/
```

## Building the Package

```bash
pdm build
```

## Utility Scripts

- `scripts/import_from_csv.py`
- `scripts/export_to_csv.py`
- `scripts/insert_time_slot.sql`

Review and adapt script configuration (for paths, credentials, and hosts) before use in your environment.

## Security Notes

- Never commit `.env` files, database passwords, peppers, tokens, or private keys.
- Treat `QUANTUM_DB_PASS`, `QUANTUM_DB_PEPPER`, and `QUANTUM_DB_TOKEN_PEPPER` as secrets.
- Use different secret values for local testing and production.
- Rotate credentials and tokens according to your organization’s security policy.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md).

## Code of Conduct

Please review [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

This project is licensed under the terms in [LICENSE](LICENSE).