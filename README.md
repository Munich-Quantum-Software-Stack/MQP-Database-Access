# Documentation

## Unit testing with pytest

Tests are implemented using `pytest` and are intended to run in a lightweight local test setup.

### Run unit tests

The tests are executed inside the docker environment called `quantum_db`. One can see its container-id using

```bash
docker ps
```

and then run:

```bash
docker exec -it [CONTAINER ID] /bin/bash
```

Inside the docker environment, one needs to change the directory to the project root (where `pyproject.toml` is located) using:

```bash
cd bqp-database-access/
```

Lastly, install the necessary dependencies using:

```bash
pdm install
```

and finally, it is ready to run pytest:

```bash
pdm run pytest
```

That's all that is required for unit tests.

### Test coverage with pytest-cov

`pytest-cov` is configured in `pyproject.toml` and automatically runs whenever you execute `pytest`.

Coverage is restricted to the `bqp_database_access` package and excludes files starting with `_` (for example `_database.py` and `__init__.py`).

Run:
```
pdm run pytest
```

You will get:
- a terminal coverage summary with missing lines
- a `coverage.xml` report file for CI integrations