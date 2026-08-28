"""
keyword_filter.py

Checks whether a transcription contains a trigger that
requires immediate AI processing.

All other conversation remains in the TranscriptBuffer
and is handled by the 20-minute session analysis.
"""


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

    def should_process(self, transcription: str) -> bool:
        """
        Returns True if the transcription contains
        an immediate-processing trigger.
        """

        text = transcription.lower()

        for keyword in self.keywords:

            if keyword in text:
                return True

        return False