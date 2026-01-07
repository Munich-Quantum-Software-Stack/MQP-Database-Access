# Documentation

## Unit testing with pytest

Tests are implemented using pytest and can be run via PDM.

In order for the unit-tests to run, get inside the docker environment quantum_db via:
```
docker exec -it <CONTAINER-ID> /bin/bash # you can find the ID from docker ps
```
then, change the directory of file to /bqp-database-access#.

Write the following codes on from the project root (where pyproject.toml is located):
```
pdm install
pdm init # to initialize pyproject.toml
pdm run pytest
```

