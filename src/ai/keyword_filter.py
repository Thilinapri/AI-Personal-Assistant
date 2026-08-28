"""
keyword_filter.py

Checks whether a transcription contains a trigger that
requires immediate AI processing.

All other conversation remains in the TranscriptBuffer
and is handled by the 20-minute session analysis.
"""

import re


class KeywordFilter:

    def __init__(self):
        self.keywords = {
            # Wake word
            "echo",

            # Immediate reminder commands
            "remind",
            "remember",
            "don't forget",
            "dont forget",
        }

        # Match keywords as complete words/phrases.
        patterns = [
            rf"\b{re.escape(keyword)}\b"
            for keyword in self.keywords
        ]

        self._pattern = re.compile(
            "|".join(patterns),
            re.IGNORECASE,
        )

    def should_process(self, transcription: str) -> bool:
        """
        Return True if the transcription contains
        an immediate-processing trigger.
        """

        if not transcription:
            return False

        return self._pattern.search(transcription) is not None