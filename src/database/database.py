import sqlite3
import threading
from pathlib import Path


class Database:

    def __init__(self):

        db_path = Path("data")
        db_path.mkdir(exist_ok=True)

        self.connection = sqlite3.connect(
            db_path / "memory.db",
            check_same_thread=False
        )

        self.cursor = self.connection.cursor()

        self.lock = threading.Lock()

        self.create_tables()

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.connection.commit()

    def save_memories(self, memories):

        with self.lock:

            for memory in memories:

                self.cursor.execute("""
                INSERT INTO memories
                (
                    category,
                    title,
                    content,
                    date,
                    time,
                    notification
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """, (

                    memory["category"],
                    memory["title"],
                    memory["content"],
                    memory["date"],
                    memory["time"],
                    int(memory["notification"])

                ))

            self.connection.commit()

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