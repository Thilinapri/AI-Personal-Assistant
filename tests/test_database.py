import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ai.memory_engine import MemoryEngine
from src.database.database import Database


def main():

    engine = MemoryEngine()
    database = Database()

    result = engine.process(
        mode="immediate",
        text="Tomorrow I have a meeting with my supervisor at 2 PM. Remind me.",
        current_time=datetime.now()
    )

    database.save_memories(result["memories"])

    memories = database.get_all_memories()

    for memory in memories:
        print(memory)

    database.close()


if __name__ == "__main__":
    main()