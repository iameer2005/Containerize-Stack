import logging
from typing import Any, Dict, List, Optional
import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL
from app.repository.base import TaskRepository

logger = logging.getLogger("task_api.repository.postgres")

class PostgresTaskRepository(TaskRepository):
    """
    PostgreSQL task storage implementation (Assignment A3).
    Talks to a real PostgreSQL database server via psycopg v3 using parameterized queries.
    Persists data reliably across application and container restarts via Docker volumes.
    """

    def __init__(self, database_url: str = DATABASE_URL) -> None:
        self.database_url = database_url

    def _get_connection(self) -> psycopg.Connection:
        """Create and return a new connection to PostgreSQL with dictionary rows."""
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def init_db(self) -> None:
        """
        Creates the 'tasks' table and indexes if they do not exist.
        Seeds three initial example tasks ONLY if the table is empty (seed-once rule).
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        );
        CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done);
        """

        seed_tasks = [
            ("Learn Docker and Postgres basics", False),
            ("Connect Postgres repository to FastAPI", True),
            ("Containerize full stack with Docker Compose", False),
        ]

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # 1. Create table and index
                cur.execute(create_table_sql)

                # 2. Check if table is empty
                cur.execute("SELECT COUNT(*) AS total FROM tasks;")
                row = cur.fetchone()
                count = row["total"] if row else 0

                # 3. Seed only on first run (prevents duplicate rows on restart)
                if count == 0:
                    logger.info("Database is empty. Seeding initial 3 example tasks...")
                    cur.executemany(
                        "INSERT INTO tasks (title, done) VALUES (%s, %s);",
                        seed_tasks,
                    )
            conn.commit()

    def get_all(self, search: Optional[str] = None, done: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Fetch all tasks with optional search or status filtering using parameterized SQL."""
        query = "SELECT id, title, done FROM tasks"
        conditions = []
        params = []

        if search is not None and search.strip():
            conditions.append("title ILIKE %s")
            params.append(f"%{search.strip()}%")

        if done is not None:
            conditions.append("done = %s")
            params.append(done)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY id ASC;"

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def get_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single task by ID using parameterized query to prevent SQL injection."""
        query = "SELECT id, title, done FROM tasks WHERE id = %s;"
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (task_id,))
                row = cur.fetchone()
                return dict(row) if row else None

    def create(self, title: str, done: bool = False) -> Dict[str, Any]:
        """
        Insert a new task into the database.
        Uses the RETURNING clause to immediately receive the auto-generated SERIAL primary key.
        """
        query = "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done;"
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (title.strip(), bool(done)))
                row = cur.fetchone()
            conn.commit()
            return dict(row)

    def update(
        self,
        task_id: int,
        title: Optional[str] = None,
        done: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a task's title and/or done status.
        Returns the updated task object, or None if the task does not exist.
        """
        # First verify the task exists
        existing = self.get_by_id(task_id)
        if not existing:
            return None

        new_title = title.strip() if title is not None else existing["title"]
        new_done = bool(done) if done is not None else existing["done"]

        query = """
        UPDATE tasks
        SET title = %s, done = %s
        WHERE id = %s
        RETURNING id, title, done;
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (new_title, new_done, task_id))
                row = cur.fetchone()
            conn.commit()
            return dict(row) if row else None

    def delete(self, task_id: int) -> bool:
        """
        Delete a task by ID.
        Returns True if a row was deleted, False if no matching task was found.
        """
        query = "DELETE FROM tasks WHERE id = %s RETURNING id;"
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (task_id,))
                row = cur.fetchone()
            conn.commit()
            return row is not None

    def ping(self) -> bool:
        """Execute SELECT 1 to verify database health."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    return True
        except Exception:
            return False
