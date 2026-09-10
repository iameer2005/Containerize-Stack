from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class TaskRepository(ABC):
    """
    Abstract interface for task storage operations.
    Guarantees storage portability: switching between in-memory, SQLite,
    or containerized PostgreSQL requires changing only the repository implementation.
    """

    @abstractmethod
    def init_db(self) -> None:
        """Initialize database schema and seed initial records if empty."""
        pass

    @abstractmethod
    def get_all(self, search: Optional[str] = None, done: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Retrieve all tasks with optional search or status filter."""
        pass

    @abstractmethod
    def get_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single task by its unique identifier."""
        pass

    @abstractmethod
    def create(self, title: str, done: bool = False) -> Dict[str, Any]:
        """Create and persist a new task record."""
        pass

    @abstractmethod
    def update(
        self,
        task_id: int,
        title: Optional[str] = None,
        done: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing task's title and/or completion status."""
        pass

    @abstractmethod
    def delete(self, task_id: int) -> bool:
        """Delete a task by its ID. Returns True if deleted, False if not found."""
        pass

    @abstractmethod
    def ping(self) -> bool:
        """Test database connection liveness (e.g. SELECT 1)."""
        pass
