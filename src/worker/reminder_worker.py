import threading


class ReminderWorker(threading.Thread):
    """Periodically checks for reminders that are due."""

    def __init__(
        self,
        reminder_manager,
        check_interval=30,
        notification_queue=None,
    ):
        super().__init__(
            daemon=True,
            name="ReminderWorker",
        )

        self.reminder_manager = reminder_manager
        self.check_interval = check_interval

        # Optional queue for TFT display notifications.
        # If no display queue is supplied, existing
        # reminder behaviour remains unchanged.
        self.notification_queue = notification_queue

        self.stop_event = threading.Event()

    def run(self):
        """Check for due reminders until the worker is stopped."""

        print("⏰ Reminder worker started.")

        while not self.stop_event.is_set():

            try:
                triggered_reminders = (
                    self.reminder_manager.check_due_reminders()
                )

                # Forward already-triggered reminders
                # to the display without changing the
                # reminder manager's existing logic.
                if self.notification_queue is not None:

                    for reminder in triggered_reminders:

                        self.notification_queue.put(
                            reminder
                        )

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
