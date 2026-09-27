import unittest

from src.database.database import Database
from src.reminder.reminder_manager import (
    ReminderManager,
)
from web.app import create_app


class FakeCloudSyncClient:

    def __init__(self):
        self.cancel_calls = []

    def cancel_reminder(
        self,
        local_reminder_id,
    ):
        self.cancel_calls.append(
            local_reminder_id
        )

        return True


class WebCloudCancellationTests(
    unittest.TestCase
):

    def setUp(self):

        self.database = Database(
            ":memory:"
        )

        self.cloud_client = (
            FakeCloudSyncClient()
        )

        self.reminder_manager = (
            ReminderManager(
                database=self.database,
                cloud_sync_client=(
                    self.cloud_client
                ),
            )
        )

        self.app = create_app(
            database=self.database,
            embedding_service=object(),
            retrieval_service=object(),
            reminder_manager=(
                self.reminder_manager
            ),
            memory_manager=object(),
        )

        self.app.config[
            "TESTING"
        ] = True

        self.client = (
            self.app.test_client()
        )

    def tearDown(self):
        self.database.close()

    def _create_memory_with_reminder(
        self,
        title,
    ):
        memory = {
            "category":
                "Event",

            "title":
                title,

            "content":
                "Cloud cancellation test.",

            "date":
                "2099-01-01",

            "time":
                "10:00",

            "notification":
                True,
        }

        memory_id = (
            self.database
            .insert_memory(
                memory
            )
        )

        reminder_id = (
            self.database
            .create_reminder(
                memory_id,
                "2099-01-01 09:30:00",
            )
        )

        return (
            memory_id,
            reminder_id,
        )

    def test_delete_memory_cancels_cloud_reminder(
        self,
    ):
        (
            memory_id,
            reminder_id,
        ) = (
            self._create_memory_with_reminder(
                "Delete test"
            )
        )

        response = (
            self.client.delete(
                f"/api/memories/{memory_id}"
            )
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
            self.cloud_client.cancel_calls,
            [
                reminder_id
            ],
        )

    def test_clear_memories_cancels_all_cloud_reminders(
        self,
    ):
        (
            _memory_one,
            reminder_one,
        ) = (
            self._create_memory_with_reminder(
                "First reminder"
            )
        )

        (
            _memory_two,
            reminder_two,
        ) = (
            self._create_memory_with_reminder(
                "Second reminder"
            )
        )

        response = (
            self.client.delete(
                "/api/memories"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            self.database
            .get_active_memories(),
            [],
        )

        self.assertCountEqual(
            self.cloud_client.cancel_calls,
            [
                reminder_one,
                reminder_two,
            ],
        )


if __name__ == "__main__":
    unittest.main()