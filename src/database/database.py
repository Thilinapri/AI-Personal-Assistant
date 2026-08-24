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

        self.cursor = self.connection.cursor()

        self.lock = threading.Lock()

        self.create_tables()
        self.migrate_memories_table()

    def create_tables(self):

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
            supersedes_id INTEGER
        )
        """)

        self.connection.commit()

    def migrate_memories_table(self):
        """Add lifecycle columns to older databases without deleting data."""

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
                "ADD COLUMN supersedes_id INTEGER"
        }

        for column_name, sql in migrations.items():

            if column_name not in existing_columns:
                self.cursor.execute(sql)

        # Give old memories sensible lifecycle timestamps.
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

    def get_all_memories(self):

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