import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ai.prompt_builder import PromptBuilder


def main():

    builder = PromptBuilder()

    prompt = builder.build(
        mode="immediate",
        text="Tomorrow I have a meeting at 2 PM.",
        current_time=datetime.now()
    )

    print(prompt)


if __name__ == "__main__":
    main()