class MemoryManager:
    """Coordinates long-term memory storage and management."""

    def __init__(self, database):
        self.database = database

    def store_memories(self, memories):
        """Store extracted memories using the current database implementation."""

        if not memories:
            return

        self.database.save_memories(memories)