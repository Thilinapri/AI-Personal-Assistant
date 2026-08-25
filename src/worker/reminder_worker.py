import threading


class ReminderWorker(threading.Thread):
    """Periodically checks for reminders that are due."""

    def __init__(
        self,
        reminder_manager,
        check_interval=30,
    ):
        super().__init__(
            daemon=True,
            name="ReminderWorker",
        )

        self.reminder_manager = reminder_manager
        self.check_interval = check_interval

        self.stop_event = threading.Event()

    def run(self):
        """Check for due reminders until the worker is stopped."""

        print("⏰ Reminder worker started.")

        while not self.stop_event.is_set():

            try:
                self.reminder_manager.check_due_reminders()

            except Exception as error:
                print(
                    f"Reminder check failed: {error}"
                )

            self.stop_event.wait(
                self.check_interval
            )

        print("⏰ Reminder worker stopped.")

    def stop(self):
        """Request a clean worker shutdown."""

        self.stop_event.set()