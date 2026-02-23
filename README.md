# Documentation

## Unit testing with pytest

Tests are implemented using `pytest` and are intended to run in a lightweight local test setup (same idea as `dashboard-backend`) without bootstrapping the full Hackathons environment.

### Run unit tests

From the project root (where `pyproject.toml` is located), install dependencies:

```bash
pdm install
```

Then run:

```bash
pdm run pytest
```

That's all that is required for unit tests.