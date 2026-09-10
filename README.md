# Task CRUD API with Containerized PostgreSQL

> **FlyRank Internship · Backend Track · Week 3 · Assignment A3**  
> **Code**: BE-04  
> Run your task API against a real PostgreSQL database running in Docker — then start the whole app, database, and cache together with a single `docker compose up` command.

---

## Stage 0: Postgres in Docker

Run the official PostgreSQL container with a persistent named volume:

```bash
docker run --name taskdb \
  -e POSTGRES_PASSWORD=dev \
  -e POSTGRES_DB=tasks \
  -p 5432:5432 \
  -v taskdata:/var/lib/postgresql/data \
  -d postgres:16-alpine
```

### Explaining the Command
- `--name taskdb`: Names the running container `taskdb`.
- `-e POSTGRES_PASSWORD=dev`: Sets the database superuser password (`dev`).
- `-e POSTGRES_DB=tasks`: Automatically creates a default database named `tasks`.
- `-p 5432:5432`: Maps host port `5432` to the container port `5432`.
- `-v taskdata:/var/lib/postgresql/data`: Mounts a persistent named Docker volume `taskdata` where Postgres data files reside, guaranteeing data outlives container restarts and deletion.
- `-d postgres:16-alpine`: Runs the lightweight official Postgres 16 Alpine image in detached background mode.

### Verifying with `psql`
```bash
docker ps
docker exec -it taskdb psql -U postgres -d tasks
```
Inside `psql`:
```sql
\dt
\q
```
