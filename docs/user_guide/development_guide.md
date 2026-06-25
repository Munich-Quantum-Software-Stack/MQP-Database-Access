# Development Guide

## Setting Up the Development Environment

### Clone the Repository

```sh
git clone https://github.com/Munich-Quantum-Software-Stack/MQP-Database-Access.git
cd MQP-Database-Access
```

### Environment Variables

To run the project locally, you need to configure your environment variables:\
1. Locate the .env.example file in the project root
2. Create a copy of this file and rename it to .env
3. Open the .env file and update the configuration values to match your local setup.

### Install dependencies

```sh
pdm install
```

### Unit testing with pytest

In order for the unit-tests running, following environment-variables need to be set (test_db.db can in principle be anything except already existing files):

```sh
export QUANTUM_DB_TESTING=TRUE
export QUANTUM_DB_FILENAME=test_db.sqlite
export QUANTUM_DS_HOST=ldap://localhost:8888
```

To run the tests, use pytest:
```sh
pdm run pytest
```


### Building the Package

```bash
pdm build
```

## Building Documentation

### Prerequisites

- Python 3.9 or newer
- Required Python packages:
```sh
pip install mkdocs mkdocs-material mkdocstrings[python] mkdocs-autorefs
```

### Build Commands

**Install MkDocs and the Material theme:**
```sh
uv sync
```

**Build the documentation:**
```sh
uv run mkdocs build
```

**Local deployment:**

Run the following and browse the documentation locally at: http://localhost:8000
```sh
uv run mkdocs serve
```
