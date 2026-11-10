import unittest

from src.ai.transcript_buffer import TranscriptBuffer


class TranscriptBufferTests(
    unittest.TestCase
):

    def test_add_with_context_returns_sentence_list(
        self,
    ):

        buffer = TranscriptBuffer()

        buffer.add(
            "First sentence."
        )

        buffer.add(
            "Second sentence."
        )

        entry_id, context = (
            buffer.add_with_context(
                "Remind me about the meeting tomorrow.",
                before=2,
                after=0,
            )
        )

        self.assertIsInstance(
            context,
            list,
        )

        self.assertEqual(
            context,
            [
                "First sentence.",
                "Second sentence.",
                (
                    "Remind me about the meeting "
                    "tomorrow."
                ),
            ],
        )

        self.assertEqual(
            entry_id,
            3,
        )


    def test_add_with_context_respects_before_limit(
        self,
    ):

        buffer = TranscriptBuffer()

        buffer.add(
            "Old sentence."
        )

        buffer.add(
            "Recent sentence."
        )

        _, context = (
            buffer.add_with_context(
                "Trigger sentence.",
                before=1,
                after=0,
            )
        )

        self.assertEqual(
            context,
            [
                "Recent sentence.",
                "Trigger sentence.",
            ],
        )


if __name__ == "__main__":
    unittest.main()