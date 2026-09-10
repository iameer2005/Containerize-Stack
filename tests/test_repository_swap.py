import unittest
from app.repository.base import TaskRepository
from app.repository.memory import InMemoryTaskRepository
from app.repository.postgres import PostgresTaskRepository

class TestRepositoryContract(unittest.TestCase):
    """
    Validates that both InMemoryTaskRepository and PostgresTaskRepository
    conform to the identical TaskRepository abstract interface.
    """

    def test_in_memory_repository_implements_interface(self):
        repo = InMemoryTaskRepository()
        self.assertIsInstance(repo, TaskRepository)

        # Test seeding
        tasks = repo.get_all()
        self.assertEqual(len(tasks), 3)

        # Test create
        created = repo.create("Architecture verification task", done=False)
        self.assertIn("id", created)
        self.assertEqual(created["title"], "Architecture verification task")
        self.assertFalse(created["done"])

        # Test read by id
        fetched = repo.get_by_id(created["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["title"], "Architecture verification task")

        # Test update
        updated = repo.update(created["id"], title="Updated task", done=True)
        self.assertIsNotNone(updated)
        self.assertEqual(updated["title"], "Updated task")
        self.assertTrue(updated["done"])

        # Test delete
        deleted = repo.delete(created["id"])
        self.assertTrue(deleted)
        self.assertIsNone(repo.get_by_id(created["id"]))

        # Test ping
        self.assertTrue(repo.ping())

    def test_postgres_repository_subclasses_interface(self):
        self.assertTrue(issubclass(PostgresTaskRepository, TaskRepository))
        # Ensure all abstract methods are implemented
        abstract_methods = TaskRepository.__abstractmethods__
        for method in abstract_methods:
            self.assertTrue(
                hasattr(PostgresTaskRepository, method),
                f"PostgresTaskRepository missing implementation for {method}"
            )

if __name__ == "__main__":
    unittest.main()
