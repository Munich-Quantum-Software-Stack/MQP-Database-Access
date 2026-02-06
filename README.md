# Documentation

## Unit testing with pytest

Tests are implemented using pytest and can be run via PDM.

In order for the unit-tests to run, get inside the docker environment quantum_db via:
```
docker exec -it <CONTAINER-ID> /bin/bash # you can find the ID from docker ps
```

then, to initialize pyproject.toml from the project root (where pyproject.toml is located)
```
pdm init
```

## Database configuration for running tests in Docker

Inside the docker environment, run

```
pdm run install
```

When running the tests inside a Docker container, you must export the following environment variables inside that container (i.e. in the same shell where you run pdm run pytest).

These variables configure the connection to the Postgres service on the Docker network.

```
export QUANTUM_DB_HOST=quantum_db   # DB service/container name on the Docker network
export QUANTUM_DB_PORT=5432
export QUANTUM_DB_USER=postgres
export QUANTUM_DB_PASSWORD=example
export QUANTUM_DB_NAME=postgres
```

Lastly, change the directory of file to /bqp-database-access#, and run:
```
pdm run pytest
```


