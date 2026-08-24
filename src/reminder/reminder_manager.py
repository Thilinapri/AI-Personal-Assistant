from datetime import datetime, timedelta


class ReminderManager:
    """Creates, checks, and triggers reminders for stored memories."""

    def __init__(
        self,
        database,
        notifier=None,
        default_lead_minutes=30,
    ):
        self.database = database
        self.notifier = notifier or self._default_notifier
        self.default_lead_minutes = default_lead_minutes

    def create_for_memory(self, memory_id, memory):
        """Create a reminder automatically when a memory requires one."""

        # No reminder requested.
        if not memory.get("notification"):
            return None

        date_value = memory.get("date")
        time_value = memory.get("time")

        # We need both date and time to schedule a reminder.
        if not date_value or not time_value:
            return None

        try:
            event_time = datetime.strptime(
                f"{date_value} {time_value}",
                "%Y-%m-%d %H:%M",
            )

        except ValueError:
            return None

        reminder_time = event_time - timedelta(
            minutes=self.default_lead_minutes
        )

        reminder_time_text = reminder_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        return self.database.create_reminder(
            memory_id,
            reminder_time_text,
        )

    def cancel_for_memory(self, memory_id):
        """Cancel pending reminders for an outdated memory."""

        self.database.cancel_pending_reminders_for_memory(
            memory_id
        )

    def check_due_reminders(self, current_time=None):
        """Trigger all pending reminders that are now due."""

        if current_time is None:
            current_time = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        due_reminders = self.database.get_due_reminders(
            current_time
        )

        triggered = []

        for reminder in due_reminders:

            reminder_id = reminder[0]
            memory_id = reminder[1]
            reminder_time = reminder[2]
            title = reminder[4]
            content = reminder[5]

            # Send the notification first.
            self.notifier(
                title,
                content,
                reminder_time,
            )

            # Only mark it triggered if notification succeeded.
            self.database.mark_reminder_triggered(
                reminder_id,
                current_time,
            )

            triggered.append({
                "reminder_id": reminder_id,
                "memory_id": memory_id,
                "title": title,
                "content": content,
                "reminder_time": reminder_time,
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
        print(f"Title: {title}")
        print(f"Details: {content}")
        print(f"Scheduled: {reminder_time}")
        print("=" * 40)