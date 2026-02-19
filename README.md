# MQP-Database-Access Development & Test Setup

This repository can be used in two ways:

1. **Integrated MQP stack setup (recommended for most contributors)** using the
   `MQSS-Hackathon` repository.
2. **Repository-only work** for code changes that do not require running the full
   containerized environment.

## Do I need to clone `MQSS-Hackathon` first?

**If you want to run the DB container and follow the official MQP dev workflow,
yes.** Clone `MQSS-Hackathon` first, then clone this repository inside it as a
sibling of the other MQP repositories.

Expected structure:

```text
<parent>
├── MQSS-Hackathon
├── MQP-API
├── MQP-Database-Access
└── Quantum-Job-Runner
```

> In some setups, `MQSS-Hackathon` also provides helper files/folders (for
> example, `put_these_inside_DB_Repo`) that must be copied into
> `MQP-Database-Access` before running the DB container.

## Integrated setup (via `MQSS-Hackathon`)

From the parent folder (where `docker-compose-db.yml` is located), run:

```bash
docker compose -f docker-compose-db.yml build qdb
docker compose -f docker-compose-db.yml up -d qdb
docker ps
```

Enter the running DB container:

```bash
docker exec -it <CONTAINER-ID> /bin/bash
```

Inside the container:

```bash
chmod +x /bqp-database-access/initialize_db.sh
/bqp-database-access/initialize_db.sh
```

Then run tests from the database-access repo:

```bash
pdm run install
pdm run pytest
```

## Notes on test environment variables

Test DB environment variables are configured automatically in
`tests/conftest.py` for pytest. You do not need to manually export
`QUANTUM_DB_*` when running tests through the documented flow.
