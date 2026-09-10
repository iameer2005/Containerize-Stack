import os
from app.repository.base import TaskRepository
from app.repository.postgres import PostgresTaskRepository
from app.repository.memory import InMemoryTaskRepository

# Active repository instance:
# This single wiring point proves the architectural promise:
# Swapping storage (in-memory -> SQLite -> PostgreSQL) touches ONLY this file or configuration,
# leaving all API routes, schemas, and validation completely unchanged.

_STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "postgres").lower()

if _STORAGE_BACKEND == "memory":
    _active_repo: TaskRepository = InMemoryTaskRepository()
else:
    _active_repo: TaskRepository = PostgresTaskRepository()

def get_repository() -> TaskRepository:
    """Dependency provider for FastAPI routes."""
    return _active_repo

def set_repository(repo: TaskRepository) -> None:
    """Allows runtime swapping of repositories during unit/integration tests."""
    global _active_repo
    _active_repo = repo
