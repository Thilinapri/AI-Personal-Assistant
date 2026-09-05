from dataclasses import dataclass

from src.privacy.context_selector import ScoredSentence


@dataclass(frozen=True)
class DisclosureResult:
    """
    Result of applying EchoMind's minimum-disclosure policy.
    """

    text: str
    selected_sentences: tuple[str, ...]
    selected_original_indexes: tuple[int, ...]

    original_selected_count: int
    original_word_count: int

    disclosed_sentence_count: int
    disclosed_word_count: int

    excluded_sentence_count: int
    truncated: bool


class MinimumDisclosureGate:
    """
    Keeps the highest-value context within a small disclosure budget.

    No additional AI model or embedding call is used here.
    """

    DEFAULT_LIMITS = {
        "immediate": {
            "max_sentences": 3,
            "max_words": 150,
        },
        "session": {
            "max_sentences": 10,
            "max_words": 400,
        },
    }

    def __init__(self, limits=None):

        self.limits = (
            limits
            if limits is not None
            else self.DEFAULT_LIMITS
        )

        self._validate_limits()

    def apply(
        self,
        items: list[ScoredSentence],
        mode: str,
        pinned_original_index: int | None = None,
    ) -> DisclosureResult:

        if mode not in self.limits:
            raise ValueError(
                f"Unsupported disclosure mode: {mode}"
            )

        if items is None:
            raise ValueError(
                "Disclosure items cannot be None."
            )

        if not isinstance(items, (list, tuple)):
            raise ValueError(
                "Disclosure items must be a list or tuple."
            )

        for item in items:

            if not isinstance(item, ScoredSentence):
                raise ValueError(
                    "All disclosure items must be "
                    "ScoredSentence objects."
                )

        if not items:
            return DisclosureResult(
                text="",
                selected_sentences=(),
                selected_original_indexes=(),
                original_selected_count=0,
                original_word_count=0,
                disclosed_sentence_count=0,
                disclosed_word_count=0,
                excluded_sentence_count=0,
                truncated=False,
            )

        max_sentences = (
            self.limits[mode]["max_sentences"]
        )

        max_words = (
            self.limits[mode]["max_words"]
        )

        original_word_count = sum(
            self._word_count(item.text)
            for item in items
        )

        chosen = []
        chosen_indexes = set()
        used_words = 0

        # In immediate mode, the trigger sentence can be pinned
        # so it cannot be displaced by supporting context.
        if pinned_original_index is not None:

            pinned_item = next(
                (
                    item
                    for item in items
                    if item.original_index
                    == pinned_original_index
                ),
                None,
            )

            if pinned_item is not None:

                text, words_used = self._fit_text(
                    pinned_item.text,
                    max_words,
                )

                if text:
                    chosen.append(
                        (
                            pinned_item,
                            text,
                        )
                    )

                    chosen_indexes.add(
                        pinned_item.original_index
                    )

                    used_words += words_used

        # Rank remaining sentences by usefulness.
        remaining = sorted(
            (
                item
                for item in items
                if item.original_index
                not in chosen_indexes
            ),
            key=lambda item: (
                -item.score,
                item.original_index,
            ),
        )

        for item in remaining:

            if len(chosen) >= max_sentences:
                break

            remaining_words = (
                max_words - used_words
            )

            if remaining_words <= 0:
                break

            text, words_used = self._fit_text(
                item.text,
                remaining_words,
            )

            if not text:
                continue

            chosen.append(
                (
                    item,
                    text,
                )
            )

            chosen_indexes.add(
                item.original_index
            )

            used_words += words_used

            # If the sentence itself had to be shortened,
            # the word budget is exhausted.
            if words_used < self._word_count(
                item.text
            ):
                break

        # Selection uses importance ranking.
        # Final text returns to conversation order.
        chosen.sort(
            key=lambda pair: (
                pair[0].original_index
            )
        )

        selected_sentences = tuple(
            text
            for _, text in chosen
        )

        selected_original_indexes = tuple(
            item.original_index
            for item, _ in chosen
        )

        disclosed_word_count = sum(
            self._word_count(text)
            for text in selected_sentences
        )

        disclosed_sentence_count = len(
            selected_sentences
        )

        excluded_sentence_count = (
            len(items)
            - disclosed_sentence_count
        )

        truncated = (
            disclosed_sentence_count < len(items)
            or disclosed_word_count < original_word_count
        )

        return DisclosureResult(
            text="\n".join(
                selected_sentences
            ),
            selected_sentences=selected_sentences,
            selected_original_indexes=selected_original_indexes,
            original_selected_count=len(items),
            original_word_count=original_word_count,
            disclosed_sentence_count=disclosed_sentence_count,
            disclosed_word_count=disclosed_word_count,
            excluded_sentence_count=excluded_sentence_count,
            truncated=truncated,
        )

    @staticmethod
    def _fit_text(
        text,
        max_words,
    ):
        words = text.split()

        if not words or max_words <= 0:
            return "", 0

        if len(words) <= max_words:
            return text, len(words)

        shortened = " ".join(
            words[:max_words]
        )

        return shortened, max_words

    def _validate_limits(self):

        for mode in (
            "immediate",
            "session",
        ):

            if mode not in self.limits:
                raise ValueError(
                    f"Missing disclosure limits for {mode}."
                )

            max_sentences = (
                self.limits[mode].get(
                    "max_sentences"
                )
            )

            max_words = (
                self.limits[mode].get(
                    "max_words"
                )
            )

            if (
                not isinstance(max_sentences, int)
                or max_sentences <= 0
            ):
                raise ValueError(
                    f"{mode} max_sentences must "
                    "be a positive integer."
                )

            if (
                not isinstance(max_words, int)
                or max_words <= 0
            ):
                raise ValueError(
                    f"{mode} max_words must "
                    "be a positive integer."
                )

    @staticmethod
    def _word_count(text):
        return len(text.split())