from datetime import datetime, timedelta


class ReminderManager:
    """Creates, checks, cancels, and triggers reminders."""

    def __init__(
        self,
        database,
        notifier=None,
        default_lead_minutes=30,
        cloud_sync_client=None,
    ):
        self.database = database

        self.notifier = (
            notifier
            or self._default_notifier
        )

        self.default_lead_minutes = (
            default_lead_minutes
        )

        self.cloud_sync_client = (
            cloud_sync_client
        )

    def create_for_memory(
        self,
        memory_id,
        memory,
    ):
        """
        Create a reminder for a memory.

        Smart reminder timing is used when Gemini provides
        reminder_before_hours.

        The existing default lead time remains as a fallback.

        SQLite is written first.

        Cloud synchronization is optional and must never
        prevent local storage.
        """

        if not memory.get(
            "notification"
        ):
            return None

        date_value = memory.get(
            "date"
        )

        time_value = memory.get(
            "time"
        )

        if (
            not date_value
            or not time_value
        ):
            return None

        try:
            event_time = datetime.strptime(
                f"{date_value} {time_value}",
                "%Y-%m-%d %H:%M",
            )

        except ValueError:
            return None

        reminder_time = (
            self._calculate_reminder_time(
                event_time=event_time,
                memory=memory,
            )
        )

        reminder_time_text = (
            reminder_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        # ---------------------------------
        # Store locally first
        # ---------------------------------

        reminder_id = (
            self.database.create_reminder(
                memory_id,
                reminder_time_text,
            )
        )

        # ---------------------------------
        # Optional cloud copy
        # ---------------------------------

        self._sync_created_reminder(
            reminder_id=reminder_id,
            memory_id=memory_id,
            memory=memory,
            event_time=event_time,
            reminder_time=reminder_time,
        )

        return reminder_id

    def _calculate_reminder_time(
        self,
        event_time,
        memory,
    ):
        """
        Calculate reminder time.

        Prefer Gemini's smart reminder lead time when valid.

        Fall back to the existing 30-minute/default lead
        when the field is missing, zero, negative, or invalid.
        """

        reminder_before_hours = (
            memory.get(
                "reminder_before_hours"
            )
        )

        if (
            reminder_before_hours
            is not None
        ):
            try:
                lead_hours = float(
                    reminder_before_hours
                )

                if lead_hours > 0:
                    return (
                        event_time
                        - timedelta(
                            hours=lead_hours
                        )
                    )

            except (
                TypeError,
                ValueError,
            ):
                pass

        # Existing fallback behavior.
        return (
            event_time
            - timedelta(
                minutes=(
                    self.default_lead_minutes
                )
            )
        )

    def _sync_created_reminder(
        self,
        reminder_id,
        memory_id,
        memory,
        event_time,
        reminder_time,
    ):
        """Synchronize a reminder without affecting local storage."""

        if (
            self.cloud_sync_client
            is None
        ):
            return False

        try:
            reason = (
                memory.get(
                    "reminder_reason"
                )
                or memory.get(
                    "reason"
                )
            )

            return (
                self.cloud_sync_client
                .sync_reminder(
                    local_reminder_id=(
                        reminder_id
                    ),
                    local_memory_id=(
                        memory_id
                    ),
                    title=memory.get(
                        "title",
                        "EchoMind Reminder",
                    ),
                    details=memory.get(
                        "content",
                        "",
                    ),
                    event_time=(
                        event_time
                    ),
                    reminder_time=(
                        reminder_time
                    ),
                    reason=reason,
                )
            )

        except Exception as error:
            print(
                "⚠️ Cloud reminder sync "
                "failed after local storage: "
                f"{error}"
            )

            return False

    def cancel_reminder(
        self,
        reminder_id,
    ):
        """
        Cancel one reminder.

        Local cancellation happens first.
        Cloud cancellation is best-effort.
        """

        cancelled = (
            self.database.cancel_reminder(
                reminder_id
            )
        )

        if not cancelled:
            return False

        self._sync_cancelled_reminder(
            reminder_id
        )

        return True

    def cancel_for_memory(
        self,
        memory_id,
    ):
        """
        Cancel every pending reminder belonging
        to an outdated or updated memory.
        """

        reminder_ids = (
            self.database
            .get_pending_reminder_ids_for_memory(
                memory_id
            )
        )

        self.database.cancel_pending_reminders_for_memory(
            memory_id
        )

        for reminder_id in reminder_ids:
            self._sync_cancelled_reminder(
                reminder_id
            )

        return reminder_ids

    def cancel_all_pending(
        self,
    ):
        """
        Cancel every pending reminder locally
        and synchronize the cancellations.

        Used before clearing all memories.
        """

        reminders = (
            self.database
            .get_all_reminders()
        )

        reminder_ids = [
            reminder[0]
            for reminder in reminders
            if reminder[3] == "pending"
        ]

        for reminder_id in reminder_ids:
            self.cancel_reminder(
                reminder_id
            )

        return reminder_ids

    def _sync_cancelled_reminder(
        self,
        reminder_id,
    ):
        """Best-effort cancellation of one cloud reminder."""

        if (
            self.cloud_sync_client
            is None
        ):
            return False

        try:
            return (
                self.cloud_sync_client
                .cancel_reminder(
                    local_reminder_id=(
                        reminder_id
                    )
                )
            )

        except Exception as error:
            print(
                "⚠️ Cloud reminder cancellation "
                "failed after local cancellation: "
                f"{error}"
            )

            return False

    def check_due_reminders(
        self,
        current_time=None,
    ):
        """Trigger pending local reminders whose time has arrived."""

        if current_time is None:
            current_time = (
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

        due_reminders = (
            self.database.get_due_reminders(
                current_time
            )
        )

        triggered = []

        for reminder in due_reminders:

            reminder_id = reminder[0]
            memory_id = reminder[1]
            reminder_time = reminder[2]
            title = reminder[4]
            content = reminder[5]

            self.notifier(
                title,
                content,
                reminder_time,
            )

            self.database.mark_reminder_triggered(
                reminder_id,
                current_time,
            )

            triggered.append({
                "reminder_id":
                    reminder_id,

                "memory_id":
                    memory_id,

                "title":
                    title,

                "content":
                    content,

                "reminder_time":
                    reminder_time,
            })

        return triggered

    def _default_notifier(
        self,
        title,
        content,
        reminder_time,
    ):
        """Simple terminal notification for the prototype."""

        print()
        print("=" * 40)
        print("REMINDER")
        print("=" * 40)
        print(
            f"Title: {title}"
        )
        print(
            f"Details: {content}"
        )
        print(
            f"Scheduled: {reminder_time}"
        )
        print("=" * 40)