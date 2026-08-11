import re
import threading
from datetime import datetime


class SessionProcessor:
    """Periodically converts a transcript snapshot into persisted memories."""

    ALLOWED_CATEGORIES = {
        "Reminder",
        "Task",
        "Shopping",
        "Note",
        "Preference",
        "Event",
    }
    MEMORY_FIELDS = {
        "category",
        "title",
        "content",
        "date",
        "time",
        "notification",
    }
    DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
    TIME_PATTERN = re.compile(r"\d{2}:\d{2}")

    def __init__(
        self,
        transcript_buffer,
        memory_engine,
        database,
        interval_seconds=20 * 60,
    ):
        self.transcript_buffer = transcript_buffer
        self.memory_engine = memory_engine
        self.database = database
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        """Start the independent session-processing daemon thread."""

        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="SessionProcessor",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        """Wake the processor if it is waiting for its next interval."""

        self._stop_event.set()

    def join(self, timeout=None):
        """Wait for the processor thread, if it has been started."""

        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def _run(self):
        while not self._stop_event.wait(self.interval_seconds):
            try:
                self.process_current_session()
            except Exception as error:
                # Keep the scheduler alive if an unexpected cycle error occurs.
                print(f"Session processing failed: {error}")

    def process_current_session(self):
        """Process and acknowledge one stable transcript snapshot."""

        snapshot = self.transcript_buffer.snapshot()
        entries = snapshot["entries"]

        if not entries:
            return False

        text = "\n".join(entry["text"] for entry in entries)

        try:
            response = self.memory_engine.process(
                mode="summary",
                text=text,
                current_time=datetime.now(),
            )
        except Exception as error:
            print(f"Session Gemini processing failed: {error}")
            return False

        try:
            summary, memories = self._validate_response(response)
        except ValueError as error:
            print(f"Session response validation failed: {error}")
            return False

        try:
            if memories:
                self.database.save_memories(memories)
        except Exception as error:
            print(f"Session memory saving failed: {error}")
            return False

        print(f"Session summary: {summary}")
        self.transcript_buffer.clear_through(snapshot["last_entry_id"])
        return True

    @classmethod
    def _validate_response(cls, response):
        if not isinstance(response, dict):
            raise ValueError("response must be a JSON object")

        if not isinstance(response.get("summary"), str):
            raise ValueError("summary must be a string")

        memories = response.get("memories")
        if not isinstance(memories, list):
            raise ValueError("memories must be a list")

        for memory in memories:
            cls._validate_memory(memory)

        return response["summary"], memories

    @classmethod
    def _validate_memory(cls, memory):
        if not isinstance(memory, dict):
            raise ValueError("each memory must be an object")

        missing_fields = cls.MEMORY_FIELDS - memory.keys()
        if missing_fields:
            raise ValueError(
                f"memory is missing fields: {', '.join(sorted(missing_fields))}"
            )

        if (
            not isinstance(memory["category"], str)
            or memory["category"] not in cls.ALLOWED_CATEGORIES
        ):
            raise ValueError("memory category is not allowed")

        for field in ("title", "content"):
            if not isinstance(memory[field], str) or not memory[field].strip():
                raise ValueError(f"memory {field} must be a non-empty string")

        cls._validate_date(memory["date"])
        cls._validate_time(memory["time"])

        if not isinstance(memory["notification"], bool):
            raise ValueError("memory notification must be a boolean")

    @classmethod
    def _validate_date(cls, value):
        if value == "":
            return

        if not isinstance(value, str) or not cls.DATE_PATTERN.fullmatch(value):
            raise ValueError("memory date must be YYYY-MM-DD or empty")

        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as error:
            raise ValueError("memory date must be a valid YYYY-MM-DD") from error

    @classmethod
    def _validate_time(cls, value):
        if value == "":
            return

        if not isinstance(value, str) or not cls.TIME_PATTERN.fullmatch(value):
            raise ValueError("memory time must be HH:MM or empty")

        try:
            datetime.strptime(value, "%H:%M")
        except ValueError as error:
            raise ValueError("memory time must be a valid HH:MM") from error
