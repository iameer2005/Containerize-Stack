# Task CRUD API — Containerized Stack (PostgreSQL + Docker Compose)

> **FlyRank Internship · Backend AI Engineering Track · Week 3 · Assignment A3**  
> **Assignment Code**: `BE-04`  
> Direct architectural continuation of Assignment A1 (In-Memory CRUD) and A2 (SQLite CRUD): swapping storage to containerized PostgreSQL with persistent Docker volumes while keeping API routes and validation 100% unchanged.

![Database Verification Screenshot](postgres_db_screenshot.jpg)

---

## 1. Goal & Architecture Overview

The core objective of Assignment A3 is to transition our task management service from single-node local storage to a production-grade containerized architecture. 

### Key Ideas
1. **Containerized Database**: PostgreSQL runs inside an isolated container from the official `postgres:16-alpine` Docker Hub image. No PostgreSQL installation or manual server configuration is required on the host system.
2. **Persistent Volumes**: Database storage is mounted to a named Docker volume (`taskdata:/var/lib/postgresql/data`). This guarantees all rows outlive container stops, restarts, and deletions.
3. **Layered Repository Architecture (The Swap Proof)**: We introduced a clean `TaskRepository` interface (`app/repository/base.py`). Swapping between `InMemoryTaskRepository` and `PostgresTaskRepository` required modifying **zero lines of code in route handlers (`app/main.py`)**. The HTTP interface, status codes, and validation remain completely identical.
4. **12-Factor Secrets**: Sensitive credentials never appear in source code or Git history. Database connection strings are loaded exclusively via `.env` (gitignored), with `.env.example` committed as a documentation template.
5. **One-Command Orchestration**: Running `docker compose up` builds the application, provisions the PostgreSQL database, initialises the schema, seeds initial records, boots Redis (stretch), and wires internal networking automatically.

---

## 2. Quick Start: The One-Command Run

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose (or Docker Desktop / Podman).
- Python 3.10+ (if running locally outside Docker).

### Run the Stack in 3 Steps
```bash
# 1. Clone the repository and enter directory
cd "b:/FlyRank/Week 3/Containerize"

# 2. Copy environment template
cp .env.example .env

# 3. Launch the full stack (API + PostgreSQL + Redis)
docker compose up --build
```
The API is immediately available at `http://localhost:3000` with interactive Swagger documentation at `http://localhost:3000/docs`.

---

## 3. Environment Variables (`.env` vs `.env.example`)

Secrets and configuration are managed strictly through environment variables.

| Variable | Description | Default in `.env.example` | Docker Compose Network Value |
| :--- | :--- | :--- | :--- |
| `PORT` | Application server port | `3000` | `3000` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:dev@localhost:5432/tasks` | `postgresql://postgres:dev@db:5432/tasks` |
| `REDIS_URL` | Redis instance connection | `redis://localhost:6379/0` | `redis://redis:6379/0` |

> [!CAUTION]
> `.env` contains live credentials and is strictly excluded by `.gitignore`. Never remove `.env` from `.gitignore` or push secrets to remote repositories.

---

## 4. API Endpoints Specification

All routes strictly maintain the contract established in Assignments A1 and A2:

| Method | Endpoint | Description | Success Status | Error Statuses |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Healthcheck pinging DB and Redis | `200 OK` | `503 Service Unavailable` |
| `GET` | `/tasks` | List all tasks (supports `?search=` and `?done=`) | `200 OK` | — |
| `GET` | `/tasks/{id}` | Retrieve single task by primary key | `200 OK` | `404 Not Found` |
| `POST` | `/tasks` | Create a new task (body: `{"title": "...", "done": bool}`) | `201 Created` | `400 Bad Request` |
| `PUT` | `/tasks/{id}` | Update task title and/or done status | `200 OK` | `400 Bad Request`, `404 Not Found` |
| `DELETE` | `/tasks/{id}` | Remove task (returns empty response body) | `204 No Content` | `404 Not Found` |

---

## 5. Live Endpoint Verification (`curl -i` Transcripts)

### 1. Health Check (Stretch Goal)
```bash
curl -i http://localhost:3000/health
```
```http
HTTP/1.1 200 OK
content-type: application/json

{"status":"healthy","database":"connected","redis":"connected"}
```

### 2. List All Tasks (`GET /tasks`)
```bash
curl -i http://localhost:3000/tasks
```
```http
HTTP/1.1 200 OK
content-type: application/json

[
  {"id":1,"title":"Learn Docker and Postgres basics","done":false},
  {"id":2,"title":"Connect Postgres repository to FastAPI","done":true},
  {"id":3,"title":"Containerize full stack with Docker Compose","done":false}
]
```

### 3. Create Task (`POST /tasks`)
```bash
curl -i -X POST http://localhost:3000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Verify data persistence across compose restarts", "done": false}'
```
```http
HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"Verify data persistence across compose restarts","done":false}
```

### 4. Input Validation Failure (`POST /tasks` with empty title)
```bash
curl -i -X POST http://localhost:3000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "   "}'
```
```http
HTTP/1.1 400 Bad Request
content-type: application/json

{"error":"Title is required and cannot be empty"}
```

### 5. Update Task (`PUT /tasks/{id}`)
```bash
curl -i -X PUT http://localhost:3000/tasks/4 \
  -H "Content-Type: application/json" \
  -d '{"title": "Verify data persistence across compose restarts", "done": true}'
```
```http
HTTP/1.1 200 OK
content-type: application/json

{"id":4,"title":"Verify data persistence across compose restarts","done":true}
```

### 6. Delete Task (`DELETE /tasks/{id}`)
```bash
curl -i -X DELETE http://localhost:3000/tasks/4
```
```http
HTTP/1.1 204 No Content
```

### 7. Task Not Found (`GET /tasks/999`)
```bash
curl -i http://localhost:3000/tasks/999
```
```http
HTTP/1.1 404 Not Found
content-type: application/json

{"error":"Task not found"}
```

---

## 6. Proving the Storage Swap: Architecture Report

### Why routes and services did not change
The golden rule of clean backend engineering is that **storage is an implementation detail**. The HTTP layer describes *what* the application does (business endpoints, validation rules, HTTP status codes), while the repository describes *how and where* data is stored.

In this project, both storage engines implement the `TaskRepository` interface (`app/repository/base.py`):
```python
class TaskRepository(ABC):
    @abstractmethod
    def get_all(self, search: Optional[str] = None, done: Optional[bool] = None) -> List[Dict[str, Any]]: ...
    @abstractmethod
    def get_by_id(self, task_id: int) -> Optional[Dict[str, Any]]: ...
    @abstractmethod
    def create(self, title: str, done: bool = False) -> Dict[str, Any]: ...
    @abstractmethod
    def update(self, task_id: int, title: Optional[str] = None, done: Optional[bool] = None) -> Optional[Dict[str, Any]]: ...
    @abstractmethod
    def delete(self, task_id: int) -> bool: ...
```

In `app/dependencies.py`, swapping between the in-memory store and PostgreSQL is controlled by a single configuration flag:
```python
if _STORAGE_BACKEND == "memory":
    _active_repo: TaskRepository = InMemoryTaskRepository()
else:
    _active_repo: TaskRepository = PostgresTaskRepository()
```
Because both repositories return Python standard dictionaries and respect the same method contracts, **`app/main.py` remained 100% unchanged**. This provides architectural proof that our API layer is decoupled from the database engine.

---

## 7. Persistence Across Restarts (How We Proved It)

To verify that data survives container lifecycles:
1. **Initial Boot**: Started the stack with `docker compose up -d`. The seed script automatically inserted the initial 3 tasks.
2. **Create New Row**: Issued a POST request creating a 4th task (`"Verify data persistence across compose restarts"`).
3. **Stop & Destroy Containers**: Executed `docker compose down`. This terminates and removes the `api`, `db`, and `redis` containers.
4. **Reboot Stack**: Executed `docker compose up -d`. New containers were instantiated from their respective images.
5. **Verification Query**: Queried `GET /tasks`. All 4 tasks were present, including row ID 4.
6. **Why it survived**: The Docker Compose configuration mounts `taskdata:/var/lib/postgresql/data`. While containers are stateless and ephemeral, Docker named volumes live on host storage independent of the container lifecycle.

### The Mortality Experiment: Why Volumes Exist
If you run PostgreSQL without a volume (`docker run -d -p 5432:5432 postgres`), any data written is stored exclusively in the container's writable layer. The moment the container is stopped and removed (`docker rm`), that writable layer is destroyed and all rows vanish permanently; Docker volumes decouple data lifecycle from container lifecycle so data survives container destruction.

---

## 8. Stretch Goal: EXPLAIN ANALYZE Index Optimization

PostgreSQL includes a sophisticated query planner. To demonstrate the impact of indexes on query execution time, we added an index on the boolean `done` column (`CREATE INDEX idx_tasks_done ON tasks(done);`) and executed `EXPLAIN ANALYZE` on a 10,000-row table (`scripts/explain_analyze.py`).

### Before Index (Sequential Scan)
```sql
EXPLAIN ANALYZE SELECT * FROM tasks WHERE done = true;
```
```text
Seq Scan on tasks  (cost=0.00..185.00 rows=5000 width=37) (actual time=0.038..1.842 rows=5000 loops=1)
  Filter: done
Planning Time: 0.082 ms
Execution Time: 2.115 ms
```
*PostgreSQL scans every individual page and row from disk sequentially.*

### After Index (Bitmap Heap Scan / Index Scan)
```sql
CREATE INDEX idx_tasks_done ON tasks(done);
EXPLAIN ANALYZE SELECT * FROM tasks WHERE done = true;
```
```text
Bitmap Heap Scan on tasks  (cost=57.42..154.67 rows=5000 width=37) (actual time=0.412..0.985 rows=5000 loops=1)
  Recheck Cond: done
  ->  Bitmap Index Scan on idx_tasks_done  (cost=0.00..56.17 rows=5000 width=0) (actual time=0.354..0.354 rows=5000 loops=1)
Planning Time: 0.114 ms
Execution Time: 1.182 ms
```
*The query planner leverages the B-tree index to locate matching row pointers directly, reducing page lookups and nearly halving execution time.*

---

## 9. Running Tests

Run the automated test suite verifying all HTTP status codes and repository interchangeability:
```bash
python -m unittest discover tests
```
Output:
```text
Ran 7 tests in 4.161s
OK
```

---

## 10. Stage 6: The AI Rematch (AI vs Me)

In Stage 6, we prompted an AI "junior developer" to containerize the CRUD API from memory, placed its output in quarantine (`ai-version/`), and performed a side-by-side code review (`git diff --no-index`).

### The Specification Prompt Used
```text
"Containerize a Task CRUD API in Python using FastAPI and PostgreSQL with psycopg v3.
Requirements:
1. Dockerfile for the app and docker-compose.yml orchestrating app and PostgreSQL.
2. Store tasks in a PostgreSQL table (id serial primary key, title text, done boolean).
3. On startup, create the table and seed 3 example tasks only if the table is empty.
4. Keep the 5 CRUD endpoints: GET /tasks, GET /tasks/{id}, POST /tasks, PUT /tasks/{id}, DELETE /tasks/{id}.
5. Use parameterized queries (%s) to prevent SQL injection.
6. Connect using DATABASE_URL environment variable without hardcoded passwords.
7. Ensure data persists across container restarts using a volume."
```

### Code Review: What the AI Did Better vs What It Missed

#### 1. What the AI did well
- **Direct Parameterized Queries**: The AI correctly utilized `%s` placeholders with `psycopg` rather than naive string formatting.
- **Pydantic Model Utilization**: It leveraged Pydantic models for request bodies.

#### 2. Three Critical Deficiencies in the AI Version
1. **Omitted Persistent Docker Volume (`volumes: [taskdata:...]`)**:
   - Despite being prompted for persistence, the AI failed to define a named volume under the `db` service or in the root `volumes` block. 
   - **Impact**: Running `docker compose down` and `docker compose up` completely wiped all user data, failing the core persistence requirement.
2. **Missing Service Healthchecks (`depends_on: condition: service_healthy`)**:
   - The AI defined simple `depends_on: [db]`. Docker considers a container "started" the millisecond its process begins, but PostgreSQL takes several seconds to initialize database files and open TCP port 5432.
   - **Impact**: The web application crashed with `psycopg.OperationalError: connection to server at "db" failed` because it attempted connecting before Postgres was ready.
3. **Breach of Architectural Layering (No Repository Pattern)**:
   - The AI wrote database logic directly within route handlers using a ad-hoc helper `get_db()`.
   - **Impact**: Swapping storage to another engine would require rewriting every single route handler. Our hand-built version adheres to the Repository pattern (`TaskRepository`), allowing seamless swapping with zero route edits.
4. **Error Response Format Violation (`{"detail": ...}` vs `{"error": ...}`)**:
   - The AI raised standard FastAPI `HTTPException`, which returns `{ "detail": "Task not found" }`. The required API contract is `{ "error": "Task not found" }`.

### Prompt Rematch & Improvement
In the rematch iteration, the prompt was improved to explicitly require:
> *"Use Docker Compose service healthchecks with `pg_isready` before starting the web container, declare a named volume `taskdata` mounted to `/var/lib/postgresql/data`, encapsulate database operations inside a repository class implementing an abstract interface, and return errors formatted as `{\"error\": \"...\"}`."*

This revision eliminated the container startup race condition and preserved the repository abstraction.

