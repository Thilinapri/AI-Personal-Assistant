from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ScoredSentence:
    """
    A locally selected sentence together with its usefulness score.

    score is between 0.0 and 1.0.
    """

    text: str
    score: float
    original_index: int
    selection_source: str


@dataclass
class ContextSelectionResult:
    """
    Result of locally selecting memory-relevant conversation text.
    """

    selected_items: list[ScoredSentence]
    original_sentence_count: int
    semantic_scored_count: int

    @property
    def selected_sentences(self):
        """
        Preserve the old interface used by existing code/tests.
        """

        return [
            item.text
            for item in self.selected_items
        ]

    @property
    def selected_sentence_count(self):
        return len(self.selected_items)


class ContextSelector:
    """
    Selects potentially useful memory content locally.

    Selection happens in two stages:

    1. Cheap rule-based scoring.
    2. MiniLM semantic scoring only for uncertain sentences.

    No additional model is introduced.
    """

    DEFAULT_SEMANTIC_THRESHOLD = 0.45

    EXPLICIT_REMINDER_PHRASES = (
        "remind me",
        "remember to",
        "don't forget",
        "do not forget",
    )

    HIGH_PRIORITY_PHRASES = (
        "deadline",
        "appointment",
        "meeting",
        "submit",
        "submission",
        "due date",
        "i need to",
        "i have to",
        "i must",
    )

    ACTION_PHRASES = (
        "call me",
        "call ",
        "send ",
        "pay ",
        "buy ",
        "book ",
        "pick up",
        "promise",
        "promised",
    )

    PREFERENCE_PHRASES = (
        "remember that",
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

        # Computed once when the selector is created.
        self.prototype_embeddings = (
            self.embedding_service.encode_many(
                self.MEMORY_PROTOTYPES
            )
        )

    def select(
        self,
        sentences,
    ) -> ContextSelectionResult:

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

            if sentence:
                cleaned.append(
                    (
                        index,
                        sentence,
                    )
                )

        if not cleaned:
            return ContextSelectionResult(
                selected_items=[],
                original_sentence_count=0,
                semantic_scored_count=0,
            )

        selected = {}
        uncertain = []

        for index, sentence in cleaned:

            if self._is_filler(sentence):
                continue

            rule_score = self._rule_score(
                sentence
            )

            if rule_score is not None:

                selected[index] = ScoredSentence(
                    text=sentence,
                    score=rule_score,
                    original_index=index,
                    selection_source="rule",
                )

                continue

            uncertain.append(
                (
                    index,
                    sentence,
                )
            )

        # MiniLM runs only for uncertain sentences,
        # and all uncertain sentences are processed in one batch.
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

                    selected[index] = ScoredSentence(
                        text=sentence,
                        score=self._clamp_score(score),
                        original_index=index,
                        selection_source="semantic",
                    )

        # Keep original conversation order here.
        # Ranking will be done later by MinimumDisclosureGate.
        selected_items = [
            selected[index]
            for index, _ in cleaned
            if index in selected
        ]

        return ContextSelectionResult(
            selected_items=selected_items,
            original_sentence_count=len(cleaned),
            semantic_scored_count=len(uncertain),
        )

    def _rule_score(
        self,
        sentence,
    ):
        """
        Cheap deterministic usefulness score.

        Higher scores represent stronger memory/reminder intent.
        """

        lowered = sentence.lower()

        if any(
            phrase in lowered
            for phrase in self.EXPLICIT_REMINDER_PHRASES
        ):
            return 1.0

        if any(
            phrase in lowered
            for phrase in self.HIGH_PRIORITY_PHRASES
        ):
            return 0.90

        if any(
            phrase in lowered
            for phrase in self.ACTION_PHRASES
        ):
            return 0.85

        if any(
            phrase in lowered
            for phrase in self.PREFERENCE_PHRASES
        ):
            return 0.80

        if (
            self.TEMPORAL_PATTERN.search(sentence)
            or self.CLOCK_PATTERN.search(sentence)
        ):
            return 0.75

        return None

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
    def _clamp_score(
        score,
    ):
        return max(
            0.0,
            min(
                1.0,
                float(score),
            ),
        )

    @staticmethod
    def _dot_product(
        first,
        second,
    ):
        """
        Dot product equals cosine similarity because the
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