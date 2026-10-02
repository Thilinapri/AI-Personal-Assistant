import unittest

from src.database.database import Database
from src.reminder.reminder_manager import (
    ReminderManager,
)


class FakeCloudSyncClient:

    def __init__(
        self,
        should_fail=False,
    ):
        self.should_fail = (
            should_fail
        )

        self.sync_calls = []
        self.cancel_calls = []

    def sync_reminder(
        self,
        **kwargs,
    ):
        if self.should_fail:
            raise RuntimeError(
                "Simulated cloud failure"
            )

        self.sync_calls.append(
            kwargs
        )

        return True

    def cancel_reminder(
        self,
        local_reminder_id,
    ):
        if self.should_fail:
            raise RuntimeError(
                "Simulated cloud cancellation failure"
            )

        self.cancel_calls.append(
            local_reminder_id
        )

        return True


class ReminderCloudSyncTests(
    unittest.TestCase
):

    def setUp(self):
        self.database = Database(
            ":memory:"
        )

    def tearDown(self):
        self.database.close()

    def _create_memory(
        self,
        reminder_before_hours=None,
    ):
        memory = {
            "category":
                "Event",

            "title":
                "Project meeting",

            "content":
                "Discuss EchoMind project.",

            "date":
                "2099-01-01",

            "time":
                "15:00",

            "notification":
                True,
        }

        if (
            reminder_before_hours
            is not None
        ):
            memory[
                "reminder_before_hours"
            ] = reminder_before_hours

        memory_id = (
            self.database.insert_memory(
                memory
            )
        )

        return (
            memory_id,
            memory,
        )

    def test_smart_reminder_hours_control_schedule(
        self,
    ):
        cloud_client = (
            FakeCloudSyncClient()
        )

        reminder_manager = (
            ReminderManager(
                database=self.database,
                cloud_sync_client=(
                    cloud_client
                ),
            )
        )

        (
            memory_id,
            memory,
        ) = self._create_memory(
            reminder_before_hours=2
        )

        reminder_manager.create_for_memory(
            memory_id,
            memory,
        )

        reminders = (
            self.database
            .get_all_reminders()
        )

        self.assertEqual(
            reminders[0][2],
            "2099-01-01 13:00:00",
        )

        payload = (
            cloud_client
            .sync_calls[0]
        )

        self.assertEqual(
            payload[
                "reminder_time"
            ].strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "2099-01-01 13:00:00",
        )

    def test_missing_smart_reminder_uses_default_fallback(
        self,
    ):
        reminder_manager = (
            ReminderManager(
                database=self.database,
            )
        )

        (
            memory_id,
            memory,
        ) = self._create_memory()

        reminder_manager.create_for_memory(
            memory_id,
            memory,
        )

        reminders = (
            self.database
            .get_all_reminders()
        )

        self.assertEqual(
            reminders[0][2],
            "2099-01-01 14:30:00",
        )

    def test_invalid_smart_reminder_uses_default_fallback(
        self,
    ):
        reminder_manager = (
            ReminderManager(
                database=self.database,
            )
        )

        (
            memory_id,
            memory,
        ) = self._create_memory(
            reminder_before_hours="invalid"
        )

        reminder_manager.create_for_memory(
            memory_id,
            memory,
        )

        reminders = (
            self.database
            .get_all_reminders()
        )

        self.assertEqual(
            reminders[0][2],
            "2099-01-01 14:30:00",
        )

    def test_created_reminder_is_synced_to_cloud(
        self,
    ):
        cloud_client = (
            FakeCloudSyncClient()
        )

        reminder_manager = (
            ReminderManager(
                database=self.database,
                cloud_sync_client=(
                    cloud_client
                ),
            )
        )

        (
            memory_id,
            memory,
        ) = self._create_memory()

        reminder_id = (
            reminder_manager
            .create_for_memory(
                memory_id,
                memory,
            )
        )

        self.assertIsNotNone(
            reminder_id
        )

        self.assertEqual(
            len(
                self.database
                .get_all_reminders()
            ),
            1,
        )

        self.assertEqual(
            len(
                cloud_client
                .sync_calls
            ),
            1,
        )

        payload = (
            cloud_client
            .sync_calls[0]
        )

        self.assertEqual(
            payload[
                "local_reminder_id"
            ],
            reminder_id,
        )

        self.assertEqual(
            payload[
                "local_memory_id"
            ],
            memory_id,
        )

    def test_cloud_failure_keeps_local_reminder(
        self,
    ):
        cloud_client = (
            FakeCloudSyncClient(
                should_fail=True
            )
        )

        reminder_manager = (
            ReminderManager(
                database=self.database,
                cloud_sync_client=(
                    cloud_client
                ),
            )
        )

        (
            memory_id,
            memory,
        ) = self._create_memory()

        reminder_id = (
            reminder_manager
            .create_for_memory(
                memory_id,
                memory,
            )
        )

        self.assertIsNotNone(
            reminder_id
        )

        reminders = (
            self.database
            .get_all_reminders()
        )

        self.assertEqual(
            reminders[0][3],
            "pending",
        )

    def test_cancel_reminder_cancels_cloud_copy(
        self,
    ):
        cloud_client = (
            FakeCloudSyncClient()
        )

        reminder_manager = (
            ReminderManager(
                database=self.database,
                cloud_sync_client=(
                    cloud_client
                ),
            )
        )

        (
            memory_id,
            memory,
        ) = self._create_memory()

        reminder_id = (
            reminder_manager
            .create_for_memory(
                memory_id,
                memory,
            )
        )

        cancelled = (
            reminder_manager
            .cancel_reminder(
                reminder_id
            )
        )

        self.assertTrue(
            cancelled
        )

        reminder = (
            self.database
            .get_all_reminders()[0]
        )

        self.assertEqual(
            reminder[3],
            "cancelled",
        )

        self.assertEqual(
            cloud_client
            .cancel_calls,
            [
                reminder_id
            ],
        )

    def test_cancel_for_memory_cancels_cloud_copy(
        self,
    ):
        cloud_client = (
            FakeCloudSyncClient()
        )

        reminder_manager = (
            ReminderManager(
                database=self.database,
                cloud_sync_client=(
                    cloud_client
                ),
            )
        )

        (
            memory_id,
            memory,
        ) = self._create_memory()

        reminder_id = (
            reminder_manager
            .create_for_memory(
                memory_id,
                memory,
            )
        )

        cancelled_ids = (
            reminder_manager
            .cancel_for_memory(
                memory_id
            )
        )

        self.assertEqual(
            cancelled_ids,
            [
                reminder_id
            ],
        )

        reminder = (
            self.database
            .get_all_reminders()[0]
        )

        self.assertEqual(
            reminder[3],
            "cancelled",
        )

        self.assertEqual(
            cloud_client
            .cancel_calls,
            [
                reminder_id
            ],
        )


if __name__ == "__main__":
    unittest.main()