import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ai.memory_engine import MemoryEngine


def main():

    engine = MemoryEngine()

    result = engine.process(
        mode="immediate",
        text="Tomorrow I have a meeting with my supervisor at 2 PM. Remind me.",
        current_time=datetime.now()
    )

    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()