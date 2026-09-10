import logging
from contextlib import asynccontextmanager
from typing import Optional

import redis
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import PORT, REDIS_URL
from app.dependencies import get_repository
from app.repository.base import TaskRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("task_api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup & shutdown lifespan context.
    Initializes database schema and ensures idempotent seed data on startup.
    """
    repo = get_repository()
    try:
        repo.init_db()
        logger.info("Database schema initialized and verified.")
    except Exception as exc:
        logger.warning(
            "Could not connect to database on startup: %s. "
            "Will attempt connection on subsequent requests (e.g. when database container finishes booting).",
            exc
        )
    yield

app = FastAPI(
    title="FlyRank Containerized Task API",
    description="Week 3 Assignment A3: Containerize your stack with PostgreSQL, Docker Compose, and Redis",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Error Handlers: Enforce exact {"error": "..."} JSON contract
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Ensure validation errors return HTTP 400 with clear JSON error message."""
    errors = exc.errors()
    msg = "Invalid request payload"
    if errors:
        loc = errors[0].get("loc", [])
        field_name = loc[-1] if loc else "field"
        msg = f"Field '{field_name}' is invalid or missing"
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": msg},
    )

# ---------------------------------------------------------------------------
# Root & Health Check Endpoints (Stretch Goal)
# ---------------------------------------------------------------------------

@app.get("/")
def get_root():
    return {
        "service": "FlyRank Task API",
        "assignment": "A3 - Containerize your stack",
        "documentation": "/docs",
        "health": "/health",
        "tasks": "/tasks"
    }

@app.get("/health")
def health_check(repo: TaskRepository = Depends(get_repository)):
    """
    Health check endpoint for container orchestrators and load balancers.
    Pings both PostgreSQL ('SELECT 1') and Redis ('PING').
    """
    # 1. Check PostgreSQL
    db_ok = repo.ping()

    # 2. Check Redis (Stretch goal)
    redis_ok = False
    try:
        r = redis.Redis.from_url(REDIS_URL, socket_timeout=1.0)
        redis_ok = bool(r.ping())
    except Exception:
        redis_ok = False

    all_healthy = db_ok
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if all_healthy else "degraded",
            "database": "connected" if db_ok else "disconnected",
            "redis": "connected" if redis_ok else "unavailable",
        }
    )

# ---------------------------------------------------------------------------
# CRUD Endpoints: Identical routes across In-Memory, SQLite, and Postgres
# ---------------------------------------------------------------------------

@app.get("/tasks", status_code=status.HTTP_200_OK)
def list_tasks(
    search: Optional[str] = None,
    done: Optional[bool] = None,
    repo: TaskRepository = Depends(get_repository)
):
    """Stage 2: Fetch all tasks from storage with optional filtering."""
    return repo.get_all(search=search, done=done)

@app.get("/tasks/{id}", status_code=status.HTTP_200_OK)
def get_task(id: int, repo: TaskRepository = Depends(get_repository)):
    """Stage 2: Fetch single task by ID using parameterized query."""
    task = repo.get_by_id(id)
    if not task:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Task not found"},
        )
    return task

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(request: Request, repo: TaskRepository = Depends(get_repository)):
    """Stage 3: Create and persist a new task."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid JSON body"},
        )

    if not isinstance(body, dict):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Request body must be a JSON object"},
        )

    title = body.get("title")
    if title is None or not isinstance(title, str) or not title.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Title is required and cannot be empty"},
        )

    done_val = bool(body.get("done", False))
    created = repo.create(title=title.strip(), done=done_val)
    return created

@app.put("/tasks/{id}", status_code=status.HTTP_200_OK)
async def update_task(id: int, request: Request, repo: TaskRepository = Depends(get_repository)):
    """Stage 3: Update an existing task."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid JSON body"},
        )

    if not isinstance(body, dict) or len(body) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "At least one field (title, done) is required"},
        )

    title = None
    if "title" in body:
        title_val = body["title"]
        if not isinstance(title_val, str) or not title_val.strip():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Title cannot be empty"},
            )
        title = title_val.strip()

    done = None
    if "done" in body:
        done_val = body["done"]
        if not isinstance(done_val, bool) and done_val not in (0, 1):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Field 'done' must be a boolean"},
            )
        done = bool(done_val)

    if title is None and done is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "At least one field (title, done) is required"},
        )

    updated = repo.update(task_id=id, title=title, done=done)
    if not updated:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Task not found"},
        )
    return updated

@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int, repo: TaskRepository = Depends(get_repository)):
    """Stage 3: Delete a task by ID. Returns 204 No Content with empty body on success."""
    deleted = repo.delete(id)
    if not deleted:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Task not found"},
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=False)
