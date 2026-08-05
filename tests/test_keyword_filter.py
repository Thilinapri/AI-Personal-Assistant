import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ai.keyword_filter import KeywordFilter


def main():
    keyword_filter = KeywordFilter()

    test_sentences = [
        "Hello, how are you?",
        "Tomorrow I have a meeting.",
        "I need to buy milk.",
        "Nova remind me to call my mom.",
        "The weather is beautiful.",
    ]

    for sentence in test_sentences:
        print(sentence)
        print(keyword_filter.should_process(sentence))
        print("-" * 40)


if __name__ == "__main__":
    main()