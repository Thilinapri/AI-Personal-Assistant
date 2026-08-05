"""
keyword_filter.py

Checks whether a transcription should be sent to the
Memory Engine immediately.

If no important keywords are found, the transcription
will be stored in the conversation buffer for the
20-minute session analysis.
"""


class KeywordFilter:

    def __init__(self):

        self.keywords = {

            # Wake Word
            "nova",

            # Reminder
            "remind",
            "remember",
            "don't forget",
            "dont forget",

            # Time
            "today",
            "tomorrow",
            "tonight",
            "morning",
            "afternoon",
            "evening",

            # Tasks
            "need to",
            "have to",
            "must",
            "should",

            # Events
            "meeting",
            "appointment",
            "interview",
            "birthday",
            "exam",
            "deadline",
            "presentation",

            # Shopping
            "buy",
            "shopping",
            "purchase",
            "groceries",

            # Work / Study
            "assignment",
            "project",
            "submission"
        }

    def should_process(self, transcription: str) -> bool:
        """
        Returns True if the transcription contains
        any keyword that requires immediate AI analysis.
        """

        text = transcription.lower()

        for keyword in self.keywords:

            if keyword in text:
                return True

        return False