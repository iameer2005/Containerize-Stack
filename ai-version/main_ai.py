"""
Stage 6 Quarantine: AI-Generated Task API
Generated based on AI junior developer prompt.
"""
import os
import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="AI Containerized Task API")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dev@localhost:5432/tasks")

class TaskCreate(BaseModel):
    title: str
    done: Optional[bool] = False

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

def get_db():
    # Note: AI creates a direct raw connection per request without repository abstraction
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

@app.on_event("startup")
def startup():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT,
                done BOOLEAN DEFAULT FALSE
            );
        """)
        cur.execute("SELECT COUNT(*) FROM tasks;")
        if cur.fetchone()["count"] == 0:
            cur.execute("INSERT INTO tasks (title, done) VALUES ('AI Task 1', false), ('AI Task 2', true), ('AI Task 3', false);")
    conn.commit()
    conn.close()

@app.get("/tasks")
def get_tasks():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM tasks;")
        rows = cur.fetchall()
    conn.close()
    return rows

@app.get("/tasks/{id}")
def get_task(id: int):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM tasks WHERE id = %s;", (id,))
        task = cur.fetchone()
    conn.close()
    if not task:
        # Standard FastAPI exception returns {"detail": "Task not found"} instead of {"error": "..."}
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done;",
            (task.title.strip(), bool(task.done))
        )
        new_task = cur.fetchone()
    conn.commit()
    conn.close()
    return new_task

@app.put("/tasks/{id}")
def update_task(id: int, task: TaskUpdate):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM tasks WHERE id = %s;", (id,))
        if not cur.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Task not found")

        cur.execute(
            "UPDATE tasks SET title = COALESCE(%s, title), done = COALESCE(%s, done) WHERE id = %s RETURNING id, title, done;",
            (task.title, task.done, id)
        )
        updated = cur.fetchone()
    conn.commit()
    conn.close()
    return updated

@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id;", (id,))
        deleted = cur.fetchone()
    conn.commit()
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return None
