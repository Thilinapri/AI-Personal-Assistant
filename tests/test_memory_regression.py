import time
import unittest
from datetime import datetime, timedelta

from src.database.database import Database
from src.memory.embedding_service import EmbeddingService
from src.memory.retrieval_service import RetrievalService
from src.memory.memory_manager import MemoryManager
from src.memory.rule_based_relationship_classifier import (
    RuleBasedRelationshipClassifier,
)
from src.reminder.reminder_manager import ReminderManager
from src.worker.reminder_worker import ReminderWorker


class MemoryRegressionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.embedding_service = EmbeddingService()

    def setUp(self):
        self.database = Database(":memory:")

        self.retrieval_service = RetrievalService(
            database=self.database,
            embedding_service=self.embedding_service,
        )

        self.relationship_classifier = RuleBasedRelationshipClassifier()

        self.reminder_manager = ReminderManager(
            database=self.database,
        )

        self.memory_manager = MemoryManager(
            database=self.database,
            embedding_service=self.embedding_service,
            retrieval_service=self.retrieval_service,
            relationship_classifier=self.relationship_classifier,
            reminder_manager=self.reminder_manager,
            candidate_threshold=0.0,
        )

    def tearDown(self):
        self.database.close()

    def test_new_memory(self):
        memory = {
            "category": "Event",
            "title": "Dentist appointment",
            "content": "Dentist appointment tomorrow.",
            "date": "2099-01-01",
            "time": "10:00",
            "notification": False,
        }

        self.memory_manager.store_memory(memory)

        memories = self.database.get_active_memories()

        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0][2], "Dentist appointment")

    def test_duplicate_memory(self):
        memory = {
            "category": "Event",
            "title": "Project meeting",
            "content": "Project meeting is at 2 PM.",
            "date": "2099-01-01",
            "time": "14:00",
            "notification": False,
        }

        self.memory_manager.store_memory(memory)
        self.memory_manager.store_memory(memory)

        rows = self.database.connection.execute(
            """
            SELECT id, status, seen_count
            FROM memories
            """
        ).fetchall()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "active")
        self.assertEqual(rows[0][2], 2)

    def test_update_memory_and_reminder(self):
        old_memory = {
            "category": "Event",
            "title": "Project meeting",
            "content": "Project meeting is at 2 PM.",
            "date": "2099-01-01",
            "time": "14:00",
            "notification": True,
        }

        new_memory = {
            "category": "Event",
            "title": "Project meeting",
            "content": "Project meeting moved to 4 PM.",
            "date": "2099-01-01",
            "time": "16:00",
            "notification": True,
        }

        self.memory_manager.store_memory(old_memory)
        self.memory_manager.store_memory(new_memory)

        memories = self.database.connection.execute(
            """
            SELECT id, time, status, supersedes_id
            FROM memories
            ORDER BY id
            """
        ).fetchall()

        reminders = self.database.connection.execute(
            """
            SELECT memory_id, status
            FROM reminders
            ORDER BY id
            """
        ).fetchall()

        self.assertEqual(memories[0][2], "superseded")
        self.assertEqual(memories[1][2], "active")
        self.assertEqual(memories[1][3], memories[0][0])

        self.assertEqual(reminders[0][1], "cancelled")
        self.assertEqual(reminders[1][1], "pending")

    def test_related_memories_remain_separate(self):
        first = {
            "category": "Event",
            "title": "Project meeting",
            "content": "Project meeting is at 2 PM.",
            "date": "2099-01-01",
            "time": "14:00",
            "notification": False,
        }

        second = {
            "category": "Event",
            "title": "Project meeting slides",
            "content": "Bring the presentation slides to the project meeting.",
            "date": "2099-01-01",
            "time": "",
            "notification": False,
        }

        self.memory_manager.store_memory(first)
        self.memory_manager.store_memory(second)

        active = self.database.get_active_memories()

        self.assertEqual(len(active), 2)

    def test_memory_batch_continues_after_failure(self):

        memories = [
            {
                "category": "Task",
                "title": "First memory",
                "content": "First valid memory.",
                "date": "",
                "time": "",
                "notification": False,
            },
            {
                "category": "Task",
                "title": "Broken memory",
                "content": "This memory will fail.",
                "date": "",
                "time": "",
                "notification": False,
            },
            {
                "category": "Task",
                "title": "Third memory",
                "content": "Third valid memory.",
                "date": "",
                "time": "",
                "notification": False,
            },
        ]

        original_store_memory = self.memory_manager.store_memory

        def controlled_store(memory):

            if memory["title"] == "Broken memory":
                raise RuntimeError(
                    "simulated memory failure"
                )

            return original_store_memory(memory)

        self.memory_manager.store_memory = controlled_store

        stored_ids = self.memory_manager.store_memories(
            memories
        )

        active_memories = self.database.get_active_memories()

        titles = [
            memory[2]
            for memory in active_memories
        ]

        self.assertCountEqual(
            titles,
            [
                "First memory",
                "Third memory",
            ],
        )

        self.assertEqual(
            len(stored_ids),
            2,
        )

    def test_semantic_retrieval(self):
        memories = [
            {
                "category": "Event",
                "title": "Project meeting",
                "content": "Project meeting is on Friday at 10 AM.",
                "date": "",
                "time": "10:00",
                "notification": False,
            },
            {
                "category": "Health",
                "title": "Dentist",
                "content": "Dentist appointment next Monday.",
                "date": "",
                "time": "",
                "notification": False,
            },
            {
                "category": "Task",
                "title": "Buy milk",
                "content": "Remember to buy milk.",
                "date": "",
                "time": "",
                "notification": False,
            },
        ]

        for memory in memories:
            self.memory_manager.store_memory(memory)

        results = self.retrieval_service.search(
            "When is my project meeting?",
            limit=3,
        )

        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["title"], "Project meeting")

    def test_background_reminder_worker(self):
        triggered = []

        def test_notifier(title, content, reminder_time):
            triggered.append(title)

        reminder_manager = ReminderManager(
            database=self.database,
            notifier=test_notifier,
        )

        memory = {
            "category": "Test",
            "title": "Background reminder",
            "content": "Regression reminder test.",
            "date": "",
            "time": "",
            "notification": False,
        }

        memory_id = self.database.insert_memory(memory)

        reminder_time = (
            datetime.now() - timedelta(seconds=1)
        ).strftime("%Y-%m-%d %H:%M:%S")

        self.database.create_reminder(
            memory_id,
            reminder_time,
        )

        worker = ReminderWorker(
            reminder_manager=reminder_manager,
            check_interval=0.1,
        )

        worker.start()
        time.sleep(0.3)
        worker.stop()
        worker.join()

        reminder = self.database.connection.execute(
            """
            SELECT status
            FROM reminders
            WHERE memory_id = ?
            """,
            (memory_id,),
        ).fetchone()

        self.assertEqual(triggered, ["Background reminder"])
        self.assertEqual(reminder[0], "triggered")


if __name__ == "__main__":
    unittest.main()