import sqlite3
import threading
from pathlib import Path


class Database:

    def __init__(self, database_path=None):

        if database_path is None:
            db_directory = Path("data")
            db_directory.mkdir(exist_ok=True)

            database_path = db_directory / "memory.db"

        self.connection = sqlite3.connect(
            database_path,
            check_same_thread=False
        )

        self.connection.execute("PRAGMA foreign_keys = ON")

        self.cursor = self.connection.cursor()

        self.lock = threading.Lock()

        self.create_tables()
        self.migrate_memories_table()

    def create_tables(self):

        # ---------------------------------
        # Memories Table
        # ---------------------------------

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            date TEXT,
            time TEXT,
            notification INTEGER DEFAULT 0,
            processed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            status TEXT NOT NULL DEFAULT 'active',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            seen_count INTEGER NOT NULL DEFAULT 1,
            supersedes_id INTEGER,

            embedding TEXT,
            embedding_model TEXT
        )
        """)

        # ---------------------------------
        # Reminders Table
        # ---------------------------------

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_id INTEGER NOT NULL,
            reminder_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            triggered_at TIMESTAMP,

            FOREIGN KEY (memory_id)
                REFERENCES memories(id)
                ON DELETE CASCADE
        )
        """)

        self.connection.commit()

    def migrate_memories_table(self):
        """Add new columns to older databases without deleting data."""

        self.cursor.execute("PRAGMA table_info(memories)")

        existing_columns = {
            row[1]
            for row in self.cursor.fetchall()
        }

        migrations = {
            "status":
                "ALTER TABLE memories "
                "ADD COLUMN status TEXT NOT NULL DEFAULT 'active'",

            "updated_at":
                "ALTER TABLE memories "
                "ADD COLUMN updated_at TIMESTAMP",

            "last_seen_at":
                "ALTER TABLE memories "
                "ADD COLUMN last_seen_at TIMESTAMP",

            "seen_count":
                "ALTER TABLE memories "
                "ADD COLUMN seen_count INTEGER NOT NULL DEFAULT 1",

            "supersedes_id":
                "ALTER TABLE memories "
                "ADD COLUMN supersedes_id INTEGER",

            "embedding":
                "ALTER TABLE memories "
                "ADD COLUMN embedding TEXT",

            "embedding_model":
                "ALTER TABLE memories "
                "ADD COLUMN embedding_model TEXT"
        }

        for column_name, sql in migrations.items():

            if column_name not in existing_columns:
                self.cursor.execute(sql)

        self.cursor.execute("""
        UPDATE memories
        SET updated_at = created_at
        WHERE updated_at IS NULL
        """)

        self.cursor.execute("""
        UPDATE memories
        SET last_seen_at = created_at
        WHERE last_seen_at IS NULL
        """)

        self.connection.commit()

    def save_memories(self, memories):
        """Legacy method for saving multiple memories."""

        with self.lock:

            try:
                with self.connection:

                    for memory in memories:

                        self.cursor.execute("""
                        INSERT INTO memories
                        (
                            category,
                            title,
                            content,
                            date,
                            time,
                            notification,
                            updated_at,
                            last_seen_at
                        )
                        VALUES (
                            ?, ?, ?, ?, ?, ?,
                            CURRENT_TIMESTAMP,
                            CURRENT_TIMESTAMP
                        )
                        """, (
                            memory["category"],
                            memory["title"],
                            memory["content"],
                            memory["date"],
                            memory["time"],
                            int(memory["notification"])
                        ))

            except Exception:
                self.connection.rollback()
                raise

    def insert_memory(self, memory, supersedes_id=None):
        """Insert one active memory and return its database ID."""

        with self.lock:

            with self.connection:

                cursor = self.connection.execute("""
                    INSERT INTO memories
                    (
                        category,
                        title,
                        content,
                        date,
                        time,
                        notification,
                        status,
                        updated_at,
                        last_seen_at,
                        seen_count,
                        supersedes_id
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?,
                        'active',
                        CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP,
                        1,
                        ?
                    )
                """, (
                    memory["category"],
                    memory["title"],
                    memory["content"],
                    memory["date"],
                    memory["time"],
                    int(memory["notification"]),
                    supersedes_id,
                ))

                return cursor.lastrowid

    def replace_memory(self, old_memory_id, new_memory):
        """Replace an older memory with a new active version."""

        with self.lock:

            with self.connection:

                cursor = self.connection.execute("""
                    INSERT INTO memories
                    (
                        category,
                        title,
                        content,
                        date,
                        time,
                        notification,
                        status,
                        updated_at,
                        last_seen_at,
                        seen_count,
                        supersedes_id
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?,
                        'active',
                        CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP,
                        1,
                        ?
                    )
                """, (
                    new_memory["category"],
                    new_memory["title"],
                    new_memory["content"],
                    new_memory["date"],
                    new_memory["time"],
                    int(new_memory["notification"]),
                    old_memory_id,
                ))

                new_memory_id = cursor.lastrowid

                self.connection.execute("""
                    UPDATE memories
                    SET
                        status = 'superseded',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (old_memory_id,))

                return new_memory_id

    def get_memory(self, memory_id):
        """Return one memory by ID."""

        with self.lock:

            cursor = self.connection.execute("""
                SELECT
                    id,
                    category,
                    title,
                    content,
                    date,
                    time,
                    notification,
                    processed,
                    created_at,
                    status,
                    updated_at,
                    last_seen_at,
                    seen_count,
                    supersedes_id,
                    embedding,
                    embedding_model
                FROM memories
                WHERE id = ?
            """, (memory_id,))

            return cursor.fetchone()

    def get_active_memories(self):
        """Return all memories that are currently active."""

        with self.lock:

            cursor = self.connection.execute("""
                SELECT
                    id,
                    category,
                    title,
                    content,
                    date,
                    time,
                    notification,
                    processed,
                    created_at,
                    status,
                    updated_at,
                    last_seen_at,
                    seen_count,
                    supersedes_id,
                    embedding,
                    embedding_model
                FROM memories
                WHERE status = 'active'
                ORDER BY id DESC
            """)

            return cursor.fetchall()

    def increment_seen(self, memory_id):
        """Record that an existing memory was observed again."""

        with self.lock:

            with self.connection:

                self.connection.execute("""
                    UPDATE memories
                    SET
                        seen_count = seen_count + 1,
                        last_seen_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (memory_id,))

    def mark_superseded(self, memory_id):
        """Mark an older memory as replaced by newer information."""

        with self.lock:

            with self.connection:

                self.connection.execute("""
                    UPDATE memories
                    SET
                        status = 'superseded',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (memory_id,))

    def update_embedding(
        self,
        memory_id,
        embedding,
        embedding_model,
    ):
        """Store a serialized embedding for a memory."""

        with self.lock:

            with self.connection:

                self.connection.execute("""
                    UPDATE memories
                    SET
                        embedding = ?,
                        embedding_model = ?
                    WHERE id = ?
                """, (
                    embedding,
                    embedding_model,
                    memory_id,
                ))

    # ---------------------------------
    # Reminder Operations
    # ---------------------------------

    def create_reminder(self, memory_id, reminder_time):
        """Create a pending reminder and return its ID."""

        with self.lock:

            with self.connection:

                cursor = self.connection.execute("""
                    INSERT INTO reminders
                    (
                        memory_id,
                        reminder_time,
                        status
                    )
                    VALUES (?, ?, 'pending')
                """, (
                    memory_id,
                    reminder_time,
                ))

                return cursor.lastrowid

    def get_due_reminders(self, current_time):
        """Return pending reminders whose scheduled time has arrived."""

        with self.lock:

            cursor = self.connection.execute("""
                SELECT
                    reminders.id,
                    reminders.memory_id,
                    reminders.reminder_time,
                    reminders.status,
                    memories.title,
                    memories.content
                FROM reminders
                JOIN memories
                    ON reminders.memory_id = memories.id
                WHERE reminders.status = 'pending'
                  AND reminders.reminder_time <= ?
                  AND memories.status = 'active'
                ORDER BY reminders.reminder_time ASC
            """, (current_time,))

            return cursor.fetchall()

    def mark_reminder_triggered(
        self,
        reminder_id,
        triggered_at,
    ):
        """Mark a reminder as triggered so it fires only once."""

        with self.lock:

            with self.connection:

                self.connection.execute("""
                    UPDATE reminders
                    SET
                        status = 'triggered',
                        triggered_at = ?
                    WHERE id = ?
                """, (
                    triggered_at,
                    reminder_id,
                ))

    def get_all_memories(self):
        """Return all memories for compatibility with existing code."""

        with self.lock:

            self.cursor.execute("""
            SELECT
                id,
                category,
                title,
                content,
                date,
                time,
                notification,
                created_at
            FROM memories
            ORDER BY id DESC
            """)

            return self.cursor.fetchall()

    def close(self):

        self.connection.close()