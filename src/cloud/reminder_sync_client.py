import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv


# ============================================================
# Load .env from the EchoMind project root
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

ENV_FILE = (
    PROJECT_ROOT
    / ".env"
)

load_dotenv(
    dotenv_path=ENV_FILE
)


class CloudReminderSyncClient:
    """
    Lightweight client used by EchoMind
    to synchronize local reminders with
    the Next.js cloud API.

    Flow:

    EchoMind / Raspberry Pi
        -> Next.js secure API
        -> Supabase
    """

    def __init__(
        self,
        endpoint=None,
        device_id=None,
        device_token=None,
        timezone_name=None,
        timeout_seconds=5,
    ):
        self.endpoint = (
            endpoint
            or os.getenv(
                "ECHOMIND_CLOUD_SYNC_URL",
                (
                    "http://127.0.0.1:3000"
                    "/api/device/reminders"
                ),
            )
        )

        self.device_id = (
            device_id
            or os.getenv(
                "ECHOMIND_DEVICE_ID",
                "echomind-test-laptop",
            )
        )

        self.device_token = (
            device_token
            or os.getenv(
                "ECHOMIND_DEVICE_SYNC_TOKEN"
            )
        )

        self.timezone_name = (
            timezone_name
            or os.getenv(
                "ECHOMIND_TIMEZONE",
                "Asia/Colombo",
            )
        )

        self.timeout_seconds = (
            timeout_seconds
        )

        if not self.device_token:
            raise ValueError(
                "ECHOMIND_DEVICE_SYNC_TOKEN "
                "not found in environment."
            )

        self.timezone = ZoneInfo(
            self.timezone_name
        )

    def sync_reminder(
        self,
        local_reminder_id,
        local_memory_id,
        title,
        details,
        reminder_time,
        event_time=None,
        reason=None,
    ):
        """
        Create or update one cloud reminder.

        The server upserts using:

            device_id + local_reminder_id

        so retries do not create duplicates.
        """

        payload = {
            "deviceId":
                self.device_id,

            "localReminderId":
                int(
                    local_reminder_id
                ),

            "localMemoryId":
                (
                    int(
                        local_memory_id
                    )
                    if local_memory_id
                    is not None
                    else None
                ),

            "title":
                str(
                    title
                ).strip(),

            "details":
                (
                    str(
                        details
                    ).strip()
                    if details
                    else None
                ),

            "eventTime":
                (
                    self._to_iso8601(
                        event_time
                    )
                    if event_time
                    else None
                ),

            "reminderTime":
                self._to_iso8601(
                    reminder_time
                ),

            "reason":
                (
                    str(
                        reason
                    ).strip()
                    if reason
                    else None
                ),

            "timezone":
                self.timezone_name,
        }

        try:
            response = requests.post(
                self.endpoint,

                headers=(
                    self._headers()
                ),

                json=payload,

                timeout=(
                    self.timeout_seconds
                ),
            )

            response.raise_for_status()

            result = (
                response.json()
            )

            if (
                result.get("ok")
                is not True
            ):
                print(
                    "☁️ Cloud reminder sync "
                    "was rejected."
                )

                return False

            print(
                "☁️ Reminder synced to cloud: "
                f"{local_reminder_id}"
            )

            return True

        except requests.RequestException as error:
            print(
                "⚠️ Cloud reminder sync failed: "
                f"{error}"
            )

            return False

        except ValueError as error:
            print(
                "⚠️ Invalid cloud reminder response: "
                f"{error}"
            )

            return False

    def cancel_reminder(
        self,
        local_reminder_id,
    ):
        """
        Mark a cloud reminder as cancelled.

        The server only changes reminders that
        are still pending.

        Calling this repeatedly is safe.
        """

        payload = {
            "deviceId":
                self.device_id,

            "localReminderId":
                int(
                    local_reminder_id
                ),
        }

        try:
            response = requests.patch(
                self.endpoint,

                headers=(
                    self._headers()
                ),

                json=payload,

                timeout=(
                    self.timeout_seconds
                ),
            )

            response.raise_for_status()

            result = (
                response.json()
            )

            if (
                result.get("ok")
                is not True
            ):
                print(
                    "☁️ Cloud reminder "
                    "cancellation was rejected."
                )

                return False

            print(
                "☁️ Cloud reminder cancelled: "
                f"{local_reminder_id}"
            )

            return True

        except requests.RequestException as error:
            print(
                "⚠️ Cloud reminder cancellation "
                f"failed: {error}"
            )

            return False

        except ValueError as error:
            print(
                "⚠️ Invalid cloud cancellation "
                f"response: {error}"
            )

            return False

    def _headers(
        self,
    ):
        return {
            "x-echomind-device-token":
                self.device_token,

            "Content-Type":
                "application/json",
        }

    def _to_iso8601(
        self,
        value,
    ):
        """
        Convert EchoMind local time into a
        timezone-aware ISO-8601 value.

        Example:

        2026-09-28 14:30:00

        becomes:

        2026-09-28T14:30:00+05:30
        """

        if isinstance(
            value,
            datetime,
        ):
            parsed = value

        elif isinstance(
            value,
            str,
        ):
            text = (
                value.strip()
            )

            if not text:
                raise ValueError(
                    "Datetime value "
                    "cannot be empty."
                )

            try:
                parsed = (
                    datetime
                    .fromisoformat(
                        text
                    )
                )

            except ValueError as error:
                raise ValueError(
                    "Invalid datetime: "
                    f"{value}"
                ) from error

        else:
            raise ValueError(
                "Datetime must be a "
                "string or datetime object."
            )

        if parsed.tzinfo is None:
            parsed = (
                parsed.replace(
                    tzinfo=(
                        self.timezone
                    )
                )
            )

        return (
            parsed.isoformat()
        )