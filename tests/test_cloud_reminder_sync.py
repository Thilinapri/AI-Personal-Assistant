import unittest
from unittest.mock import patch

from src.cloud.reminder_sync_client import (
    CloudReminderSyncClient,
)


class FakeResponse:

    def __init__(
        self,
        result=None,
    ):
        self.result = (
            result
            if result is not None
            else {
                "ok": True,
                "reminder": [],
            }
        )

    def raise_for_status(
        self,
    ):
        pass

    def json(
        self,
    ):
        return self.result


class CloudReminderSyncClientTests(
    unittest.TestCase
):

    def setUp(
        self,
    ):
        self.client = (
            CloudReminderSyncClient(
                endpoint=(
                    "http://localhost:3000/"
                    "api/device/reminders"
                ),
                device_id=(
                    "echomind-test-laptop"
                ),
                device_token=(
                    "test-device-token"
                ),
                timezone_name=(
                    "Asia/Colombo"
                ),
            )
        )

    @patch(
        "src.cloud.reminder_sync_client."
        "requests.post"
    )
    def test_sync_reminder_sends_expected_payload(
        self,
        mock_post,
    ):
        mock_post.return_value = (
            FakeResponse()
        )

        result = (
            self.client
            .sync_reminder(
                local_reminder_id=2,
                local_memory_id=2,
                title=(
                    "Project meeting"
                ),
                details=(
                    "Discuss EchoMind."
                ),
                event_time=(
                    "2026-09-28 "
                    "15:00:00"
                ),
                reminder_time=(
                    "2026-09-28 "
                    "14:30:00"
                ),
                reason=(
                    "Prepare before meeting"
                ),
            )
        )

        self.assertTrue(
            result
        )

        mock_post.assert_called_once()

        call = (
            mock_post.call_args
        )

        payload = (
            call.kwargs[
                "json"
            ]
        )

        self.assertEqual(
            payload["deviceId"],
            "echomind-test-laptop",
        )

        self.assertEqual(
            payload[
                "localReminderId"
            ],
            2,
        )

        self.assertEqual(
            payload[
                "localMemoryId"
            ],
            2,
        )

        self.assertEqual(
            payload["title"],
            "Project meeting",
        )

        self.assertEqual(
            payload[
                "reminderTime"
            ],
            (
                "2026-09-28T"
                "14:30:00+05:30"
            ),
        )

        self.assertEqual(
            payload[
                "eventTime"
            ],
            (
                "2026-09-28T"
                "15:00:00+05:30"
            ),
        )

        self.assertEqual(
            payload["timezone"],
            "Asia/Colombo",
        )

        headers = (
            call.kwargs[
                "headers"
            ]
        )

        self.assertEqual(
            headers[
                "x-echomind-device-token"
            ],
            "test-device-token",
        )

    @patch(
        "src.cloud.reminder_sync_client."
        "requests.patch"
    )
    def test_cancel_reminder_sends_expected_payload(
        self,
        mock_patch,
    ):
        mock_patch.return_value = (
            FakeResponse({
                "ok": True,
                "updated": True,
                "reminder": [],
            })
        )

        result = (
            self.client
            .cancel_reminder(
                local_reminder_id=3
            )
        )

        self.assertTrue(
            result
        )

        mock_patch.assert_called_once()

        call = (
            mock_patch.call_args
        )

        payload = (
            call.kwargs[
                "json"
            ]
        )

        self.assertEqual(
            payload,
            {
                "deviceId":
                    "echomind-test-laptop",

                "localReminderId":
                    3,
            },
        )

        headers = (
            call.kwargs[
                "headers"
            ]
        )

        self.assertEqual(
            headers[
                "x-echomind-device-token"
            ],
            "test-device-token",
        )

    def test_datetime_conversion_adds_timezone(
        self,
    ):
        result = (
            self.client
            ._to_iso8601(
                "2026-09-28 "
                "10:00:00"
            )
        )

        self.assertEqual(
            result,
            (
                "2026-09-28T"
                "10:00:00+05:30"
            ),
        )


if __name__ == "__main__":
    unittest.main()