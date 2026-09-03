from datetime import datetime
import threading


class TranscriptBuffer:

    def __init__(self):
        self._lock = threading.RLock()
        self._sentences = []
        self._next_entry_id = 1

    @property
    def sentences(self):
        """Return a copy of the current entries for legacy read access."""

        with self._lock:
            return [item.copy() for item in self._sentences]

    def add(self, text):

        with self._lock:
            entry_id = self._next_entry_id
            self._next_entry_id += 1

            self._sentences.append({
                "id": entry_id,
                "time": datetime.now(),
                "text": text
            })

            return entry_id

    def add_with_context(self, text, before=2, after=0):
        """Add an entry and atomically return its surrounding text context."""

        with self._lock:
            entry_id = self._next_entry_id
            self._next_entry_id += 1

            self._sentences.append({
                "id": entry_id,
                "time": datetime.now(),
                "text": text
            })

            index = len(self._sentences) - 1
            start = max(0, index - before)
            end = min(len(self._sentences), index + after + 1)

            context = "\n".join(
                entry["text"]
                for entry in self._sentences[start:end]
            )

            return entry_id, context

    def size(self):

        with self._lock:
            return len(self._sentences)

    def get(self, index):

        with self._lock:
            return self._sentences[index].copy()

    def get_context(self, index, before=2, after=2):

        with self._lock:
            start = max(0, index - before)
            end = min(len(self._sentences), index + after + 1)

            context = []

            for item in self._sentences[start:end]:
                context.append(item["text"])

            return "\n".join(context)

    def get_context_for(self, entry_id, before=2, after=0):
        """Return context around an entry ID while holding the buffer lock."""

        with self._lock:
            for index, item in enumerate(self._sentences):
                if item["id"] == entry_id:
                    start = max(0, index - before)
                    end = min(len(self._sentences), index + after + 1)

                    return "\n".join(
                        entry["text"]
                        for entry in self._sentences[start:end]
                    )

        raise ValueError(
            f"Transcript entry ID not found: {entry_id}"
        )

    def get_all_text(self):

        with self._lock:
            return "\n".join(
                item["text"]
                for item in self._sentences
            )

    def snapshot(self):
        """Capture all current entries and the ID of the last captured entry."""

        with self._lock:
            entries = [item.copy() for item in self._sentences]
            last_entry_id = (
                entries[-1]["id"]
                if entries
                else None
            )

            return {
                "entries": entries,
                "last_entry_id": last_entry_id,
            }

    def clear_through(self, entry_id):
        """Remove entries up to and including an acknowledged entry ID."""

        with self._lock:
            self._sentences = [
                item
                for item in self._sentences
                if item["id"] > entry_id
            ]

    def clear(self):

        with self._lock:
            self._sentences.clear()

    def remove(self, entry_id):
        """Remove one specific transcript entry."""

        with self._lock:
            self._sentences = [
                item
                for item in self._sentences
                if item["id"] != entry_id
            ]