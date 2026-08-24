from datetime import datetime


class ReminderManager:
    """Checks and triggers reminders for stored memories."""

    def __init__(self, database, notifier=None):

        self.database = database
        self.notifier = notifier or self._default_notifier

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

            # Notify first.
            self.notifier(
                title,
                content,
                reminder_time,
            )

            # Only mark it triggered after notification succeeds.
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