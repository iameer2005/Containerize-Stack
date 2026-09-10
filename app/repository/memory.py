import threading
from typing import Any, Dict, List, Optional
from app.repository.base import TaskRepository

class InMemoryTaskRepository(TaskRepository):
    """
    In-memory task storage implementation (Assignment A1 baseline).
    Stores tasks in a thread-safe list in memory.
    Data is lost upon process restart.
    """

    def __init__(self) -> None:
        self._tasks: List[Dict[str, Any]] = []
        self._next_id: int = 1
        self._lock = threading.Lock()
        self.init_db()

    def init_db(self) -> None:
        with self._lock:
            if not self._tasks:
                # Seed 3 example tasks
                self._tasks = [
                    {"id": 1, "title": "Learn Docker and Postgres basics", "done": False},
                    {"id": 2, "title": "Connect Postgres repository to FastAPI", "done": True},
                    {"id": 3, "title": "Containerize full stack with Docker Compose", "done": False},
                ]
                self._next_id = 4

    def get_all(self, search: Optional[str] = None, done: Optional[bool] = None) -> List[Dict[str, Any]]:
        with self._lock:
            results = [dict(t) for t in self._tasks]
            if search:
                query = search.strip().lower()
                results = [t for t in results if query in t["title"].lower()]
            if done is not None:
                results = [t for t in results if t["done"] is done]
            return results

    def get_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            for t in self._tasks:
                if t["id"] == task_id:
                    return dict(t)
            return None

    def create(self, title: str, done: bool = False) -> Dict[str, Any]:
        with self._lock:
            new_task = {
                "id": self._next_id,
                "title": title.strip(),
                "done": bool(done)
            }
            self._tasks.append(new_task)
            self._next_id += 1
            return dict(new_task)

    def update(
        self,
        task_id: int,
        title: Optional[str] = None,
        done: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            for t in self._tasks:
                if t["id"] == task_id:
                    if title is not None:
                        t["title"] = title.strip()
                    if done is not None:
                        t["done"] = bool(done)
                    return dict(t)
            return None

    def delete(self, task_id: int) -> bool:
        with self._lock:
            for idx, t in enumerate(self._tasks):
                if t["id"] == task_id:
                    del self._tasks[idx]
                    return True
            return False

    def ping(self) -> bool:
        return True
