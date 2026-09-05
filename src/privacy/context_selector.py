from dataclasses import dataclass
import re


@dataclass
class ContextSelectionResult:
    """
    Result of locally selecting memory-relevant conversation text.
    """

    selected_sentences: list[str]
    original_sentence_count: int
    semantic_scored_count: int

    @property
    def selected_sentence_count(self):
        return len(self.selected_sentences)


class ContextSelector:
    """
    Selects potentially useful memory content locally.

    Selection happens in two stages:

    1. Cheap rule-based checks.
    2. MiniLM semantic scoring only for uncertain sentences.

    The EmbeddingService is injected so EchoMind can reuse the
    already-loaded local MiniLM model.
    """

    # Experimental starting threshold.
    # We will later evaluate this using project test data.
    DEFAULT_SEMANTIC_THRESHOLD = 0.45

    STRONG_PHRASES = (
        "remind me",
        "remember to",
        "remember that",
        "don't forget",
        "do not forget",
        "i need to",
        "i have to",
        "i must",
        "deadline",
        "appointment",
        "meeting",
        "submit",
        "submission",
        "due date",
        "call me",
        "call ",
        "send ",
        "pay ",
        "buy ",
        "book ",
        "pick up",
        "promise",
        "promised",
        "prefer",
        "preference",
        "favorite",
    )

    FILLER_PHRASES = {
        "ok",
        "okay",
        "yes",
        "no",
        "yeah",
        "yep",
        "nope",
        "hmm",
        "uh",
        "thanks",
        "thank you",
        "hello",
        "hi",
        "bye",
    }

    MEMORY_PROTOTYPES = (
        "Remember an appointment or scheduled meeting.",
        "A future event with a date or time.",
        "A task or action that the user needs to complete.",
        "A deadline or submission that must be completed.",
        "A commitment or promise involving the user.",
        "Something the user wants to buy or remember later.",
        "A personal preference that should be remembered.",
    )

    TEMPORAL_PATTERN = re.compile(
        r"\b(?:"
        r"today|tomorrow|tonight|"
        r"monday|tuesday|wednesday|thursday|"
        r"friday|saturday|sunday|"
        r"next\s+(?:week|month|monday|tuesday|wednesday|"
        r"thursday|friday|saturday|sunday)"
        r")\b",
        re.IGNORECASE,
    )

    CLOCK_PATTERN = re.compile(
        r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b",
        re.IGNORECASE,
    )

    def __init__(
        self,
        embedding_service,
        semantic_threshold=None,
    ):
        if embedding_service is None:
            raise ValueError(
                "ContextSelector requires an EmbeddingService."
            )

        self.embedding_service = embedding_service

        self.semantic_threshold = (
            semantic_threshold
            if semantic_threshold is not None
            else self.DEFAULT_SEMANTIC_THRESHOLD
        )

        if not 0.0 <= self.semantic_threshold <= 1.0:
            raise ValueError(
                "semantic_threshold must be between 0 and 1."
            )

        # Cache prototype embeddings once.
        self.prototype_embeddings = (
            self.embedding_service.encode_many(
                self.MEMORY_PROTOTYPES
            )
        )

    def select(
        self,
        sentences,
    ) -> ContextSelectionResult:
        """
        Select memory-relevant sentences while preserving
        their original order.
        """

        if sentences is None:
            raise ValueError("Sentences cannot be None.")

        if isinstance(sentences, str):
            raise ValueError(
                "Sentences must be a list or tuple of strings."
            )

        cleaned = []

        for index, sentence in enumerate(sentences):

            if not isinstance(sentence, str):
                raise ValueError(
                    "All sentences must be strings."
                )

            sentence = sentence.strip()

            if not sentence:
                continue

            cleaned.append(
                (
                    index,
                    sentence,
                )
            )

        if not cleaned:
            return ContextSelectionResult(
                selected_sentences=[],
                original_sentence_count=0,
                semantic_scored_count=0,
            )

        selected_indexes = set()
        uncertain = []

        for index, sentence in cleaned:

            if self._is_filler(sentence):
                continue

            if self._has_strong_signal(sentence):
                selected_indexes.add(index)
                continue

            uncertain.append(
                (
                    index,
                    sentence,
                )
            )

        # Only uncertain sentences use MiniLM.
        if uncertain:

            uncertain_texts = [
                sentence
                for _, sentence in uncertain
            ]

            sentence_embeddings = (
                self.embedding_service.encode_many(
                    uncertain_texts
                )
            )

            for (
                index,
                sentence,
            ), embedding in zip(
                uncertain,
                sentence_embeddings,
            ):

                score = self._maximum_similarity(
                    embedding
                )

                if score >= self.semantic_threshold:
                    selected_indexes.add(index)

        selected_sentences = [
            sentence
            for index, sentence in cleaned
            if index in selected_indexes
        ]

        return ContextSelectionResult(
            selected_sentences=selected_sentences,
            original_sentence_count=len(cleaned),
            semantic_scored_count=len(uncertain),
        )

    def _has_strong_signal(
        self,
        sentence,
    ):
        lowered = sentence.lower()

        if any(
            phrase in lowered
            for phrase in self.STRONG_PHRASES
        ):
            return True

        if self.TEMPORAL_PATTERN.search(sentence):
            return True

        if self.CLOCK_PATTERN.search(sentence):
            return True

        return False

    def _is_filler(
        self,
        sentence,
    ):
        normalized = sentence.strip().lower()

        normalized = normalized.rstrip(
            ".!?,"
        )

        return normalized in self.FILLER_PHRASES

    def _maximum_similarity(
        self,
        embedding,
    ):
        if not self.prototype_embeddings:
            return 0.0

        return max(
            self._dot_product(
                embedding,
                prototype,
            )
            for prototype in self.prototype_embeddings
        )

    @staticmethod
    def _dot_product(
        first,
        second,
    ):
        """
        Dot product equals cosine similarity here because
        EmbeddingService returns normalized embeddings.
        """

        if len(first) != len(second):
            raise ValueError(
                "Embedding dimensions do not match."
            )

        return sum(
            a * b
            for a, b in zip(
                first,
                second,
            )
        )