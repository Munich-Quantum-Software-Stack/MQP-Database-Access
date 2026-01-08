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

Lastly, change the directory of file to /bqp-database-access#.
```
pdm run pytest
```

