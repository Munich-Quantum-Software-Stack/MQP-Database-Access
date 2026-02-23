# Documentation

## Unit testing with pytest

Tests are implemented using `pytest` and are intended to run in a lightweight local test setup (same idea as `dashboard-backend`) without bootstrapping the full Hackathons environment.

### Run unit tests
The tests are executed inside the docker environment called quantum_db. One can see its container-id using

```bash
docker ps
```

and then run:

```bash
docker exec -it [CONTAINER ID] /bin/bash
```

Inside the docker environment, one needs to change the directory to the project root (where pyproject.toml is located) using:

```bash
cd bqp-database-access/
```

Lastly, install the necessary dependencies using:

```bash
pdm install
```

and finally, we are ready to run pytest:

```bash
pdm run pytest
```

That's all that is required for unit tests.