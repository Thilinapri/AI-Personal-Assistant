import unittest

from src.database.database import Database
from web.app import create_app


class FakeRetrievalService:
    """Small test replacement for semantic retrieval."""

    def search(self, query, limit=5):
        return [
            {
                "id": 1,
                "title": "Project meeting",
                "content": "Project meeting is on Friday.",
                "score": 0.91,
            }
        ]


class FakeMemoryManager:
    """Small test replacement for dashboard memory editing."""

    def __init__(self, database):
        self.database = database

    def update_memory(self, memory_id, memory):
        return self.database.update_memory(
            memory_id,
            memory,
        )


class WebApiTests(unittest.TestCase):

    def setUp(self):
        self.database = Database(":memory:")

        self.retrieval_service = (
            FakeRetrievalService()
        )

        self.memory_manager = FakeMemoryManager(
            self.database
        )

        self.app = create_app(
            database=self.database,
            embedding_service=object(),
            retrieval_service=self.retrieval_service,
            reminder_manager=object(),
            memory_manager=self.memory_manager,
        )

        self.app.config["TESTING"] = True

        self.client = self.app.test_client()

    def tearDown(self):
        self.database.close()

    def create_test_memory(
        self,
        title="Test memory",
        notification=False,
    ):
        memory = {
            "category": "Task",
            "title": title,
            "content": "Test memory content.",
            "date": "2099-01-01",
            "time": "10:00",
            "notification": notification,
        }

        return self.database.insert_memory(
            memory
        )

    def test_status_endpoint(self):
        response = self.client.get(
            "/api/status"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.get_json()

        self.assertEqual(
            data["application"],
            "EchoMind",
        )

        self.assertEqual(
            data["web"],
            "running",
        )

        self.assertEqual(
            data["database"],
            "connected",
        )

        self.assertEqual(
            data["listening"],
            "active",
        )

    def test_listening_can_be_paused_and_resumed(
        self
    ):
        response = self.client.post(
            "/api/listening",
            json={
                "enabled": False,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.get_json()["listening"],
            "paused",
        )

        self.assertFalse(
            self.database.get_listening_enabled()
        )

        response = self.client.post(
            "/api/listening",
            json={
                "enabled": True,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.get_json()["listening"],
            "active",
        )

        self.assertTrue(
            self.database.get_listening_enabled()
        )

    def test_invalid_listening_value_is_rejected(
        self
    ):
        response = self.client.post(
            "/api/listening",
            json={
                "enabled": "false",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_memories_endpoint(self):
        memory_id = self.create_test_memory(
            title="API memory"
        )

        response = self.client.get(
            "/api/memories"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        memories = response.get_json()

        self.assertEqual(
            len(memories),
            1,
        )

        self.assertEqual(
            memories[0]["id"],
            memory_id,
        )

        self.assertEqual(
            memories[0]["title"],
            "API memory",
        )

        self.assertEqual(
            memories[0]["status"],
            "active",
        )

    def test_reminders_endpoint(self):
        memory_id = self.create_test_memory(
            title="API reminder"
        )

        reminder_id = (
            self.database.create_reminder(
                memory_id,
                "2099-01-01 09:30:00",
            )
        )

        response = self.client.get(
            "/api/reminders"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        reminders = response.get_json()

        self.assertEqual(
            len(reminders),
            1,
        )

        self.assertEqual(
            reminders[0]["id"],
            reminder_id,
        )

        self.assertEqual(
            reminders[0]["title"],
            "API reminder",
        )

        self.assertEqual(
            reminders[0]["status"],
            "pending",
        )

    def test_delete_memory_endpoint(self):
        memory_id = self.create_test_memory(
            title="Delete test"
        )

        self.database.create_reminder(
            memory_id,
            "2099-01-01 09:30:00",
        )

        response = self.client.delete(
            f"/api/memories/{memory_id}"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIsNone(
            self.database.get_memory(
                memory_id
            )
        )

        self.assertEqual(
            self.database.get_all_reminders(),
            [],
        )

    def test_clear_all_memories_endpoint(self):
        self.create_test_memory(
            title="First memory"
        )

        self.create_test_memory(
            title="Second memory"
        )

        response = self.client.delete(
            "/api/memories"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            self.database.get_active_memories(),
            [],
        )

    def test_update_memory_endpoint(self):
        memory_id = self.create_test_memory(
            title="Old title"
        )

        updated_memory = {
            "category": "Event",
            "title": "Updated title",
            "content": "Updated content.",
            "date": "2099-02-01",
            "time": "15:00",
            "notification": True,
        }

        response = self.client.put(
            f"/api/memories/{memory_id}",
            json=updated_memory,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        memory = self.database.get_memory(
            memory_id
        )

        self.assertEqual(
            memory[2],
            "Updated title",
        )

        self.assertEqual(
            memory[3],
            "Updated content.",
        )

        self.assertEqual(
            memory[5],
            "15:00",
        )

    def test_search_endpoint(self):
        response = self.client.get(
            "/api/memories/search"
            "?q=project+meeting"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.get_json()

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0]["title"],
            "Project meeting",
        )

        self.assertAlmostEqual(
            results[0]["score"],
            0.91,
        )


if __name__ == "__main__":
    unittest.main()