import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import set_repository
from app.repository.memory import InMemoryTaskRepository

class TestTaskAPICRUD(unittest.TestCase):
    """
    Comprehensive verification suite for Task CRUD API:
    - 200: GET /tasks, GET /tasks/{id}, PUT /tasks/{id}
    - 201: POST /tasks
    - 204: DELETE /tasks/{id} (empty body)
    - 400: POST /tasks and PUT /tasks/{id} with invalid body or empty title
    - 404: GET, PUT, DELETE with unknown ID
    """

    def setUp(self):
        # Use fresh in-memory repository for predictable testing
        self.repo = InMemoryTaskRepository()
        set_repository(self.repo)
        self.client = TestClient(app)

    def test_01_read_endpoints(self):
        # GET /tasks (returns seeded tasks)
        res = self.client.get("/tasks")
        self.assertEqual(res.status_code, 200)
        tasks = res.json()
        self.assertEqual(len(tasks), 3)

        # GET /tasks/{id} (existing)
        first_id = tasks[0]["id"]
        res_single = self.client.get(f"/tasks/{first_id}")
        self.assertEqual(res_single.status_code, 200)
        self.assertEqual(res_single.json()["title"], tasks[0]["title"])

        # GET /tasks/{id} (unknown -> 404)
        res_404 = self.client.get("/tasks/99999")
        self.assertEqual(res_404.status_code, 404)
        self.assertEqual(res_404.json(), {"error": "Task not found"})

    def test_02_create_task(self):
        # POST /tasks (valid -> 201 Created)
        payload = {"title": "Deploy stack with Docker Compose", "done": False}
        res = self.client.post("/tasks", json=payload)
        self.assertEqual(res.status_code, 201)
        created = res.json()
        self.assertEqual(created["title"], "Deploy stack with Docker Compose")
        self.assertFalse(created["done"])
        self.assertIn("id", created)

        # Validation: missing title -> 400
        res_missing = self.client.post("/tasks", json={})
        self.assertEqual(res_missing.status_code, 400)
        self.assertIn("error", res_missing.json())

        # Validation: empty/whitespace title -> 400
        res_empty = self.client.post("/tasks", json={"title": "   "})
        self.assertEqual(res_empty.status_code, 400)
        self.assertEqual(res_empty.json(), {"error": "Title is required and cannot be empty"})

    def test_03_update_task(self):
        # PUT /tasks/{id} (valid -> 200 OK)
        update_payload = {"title": "Mastered Docker and Postgres", "done": True}
        res = self.client.put("/tasks/1", json=update_payload)
        self.assertEqual(res.status_code, 200)
        updated = res.json()
        self.assertEqual(updated["title"], "Mastered Docker and Postgres")
        self.assertTrue(updated["done"])

        # PUT unknown ID -> 404
        res_404 = self.client.put("/tasks/99999", json=update_payload)
        self.assertEqual(res_404.status_code, 404)
        self.assertEqual(res_404.json(), {"error": "Task not found"})

        # PUT empty title -> 400
        res_bad = self.client.put("/tasks/1", json={"title": ""})
        self.assertEqual(res_bad.status_code, 400)
        self.assertEqual(res_bad.json(), {"error": "Title cannot be empty"})

        # PUT empty body -> 400
        res_empty = self.client.put("/tasks/1", json={})
        self.assertEqual(res_empty.status_code, 400)
        self.assertEqual(res_empty.json(), {"error": "At least one field (title, done) is required"})

    def test_04_delete_task(self):
        # DELETE /tasks/{id} (valid -> 204 No Content with empty body)
        res = self.client.delete("/tasks/2")
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.text, "")

        # Verify deletion -> GET returns 404
        res_get = self.client.get("/tasks/2")
        self.assertEqual(res_get.status_code, 404)

        # DELETE unknown ID -> 404
        res_404 = self.client.delete("/tasks/99999")
        self.assertEqual(res_404.status_code, 404)
        self.assertEqual(res_404.json(), {"error": "Task not found"})

    def test_05_health_check(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("status", data)
        self.assertIn("database", data)
        self.assertEqual(data["database"], "connected")

if __name__ == "__main__":
    unittest.main()
