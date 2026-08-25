import re
from difflib import SequenceMatcher

from src.memory.relationship_classifier import RelationshipClassifier


class RuleBasedRelationshipClassifier(RelationshipClassifier):
    """
    Conservative local classifier for memory relationships.

    Semantic retrieval finds possible matching memories first.
    This classifier then decides whether a candidate is:

    - duplicate
    - update
    - related
    - new

    It intentionally avoids treating cosine similarity alone
    as proof that a memory should be replaced.
    """

    UPDATE_WORDS = {
        "moved",
        "changed",
        "rescheduled",
        "updated",
        "postponed",
        "instead",
        "now",
        "cancelled",
        "canceled",
    }

    def classify(self, new_memory, existing_memory):

        new_category = self._normalize(new_memory.get("category"))
        old_category = self._normalize(existing_memory.get("category"))

        new_title = self._normalize(new_memory.get("title"))
        old_title = self._normalize(existing_memory.get("title"))

        new_content = self._normalize(new_memory.get("content"))
        old_content = self._normalize(existing_memory.get("content"))

        new_date = self._normalize(new_memory.get("date"))
        old_date = self._normalize(existing_memory.get("date"))

        new_time = self._normalize(new_memory.get("time"))
        old_time = self._normalize(existing_memory.get("time"))

        title_similarity = self._text_similarity(
            new_title,
            old_title,
        )

        content_similarity = self._text_similarity(
            new_content,
            old_content,
        )

        same_category = new_category == old_category
        same_date = new_date == old_date
        same_time = new_time == old_time

        # ---------------------------------
        # Duplicate
        # ---------------------------------

        if (
            same_category
            and same_date
            and same_time
            and title_similarity >= 0.90
            and content_similarity >= 0.80
        ):
            return "duplicate"

        # ---------------------------------
        # Update
        # ---------------------------------

        temporal_change = (
            (
                new_date
                and old_date
                and new_date != old_date
            )
            or (
                new_time
                and old_time
                and new_time != old_time
            )
        )

        update_language = self._contains_update_word(
            new_content
        )

        if (
            same_category
            and title_similarity >= 0.80
            and temporal_change
            and (
                update_language
                or same_date
            )
        ):
            return "update"

        # ---------------------------------
        # Related
        # ---------------------------------

        if (
            same_category
            and (
                title_similarity >= 0.65
                or content_similarity >= 0.65
            )
        ):
            return "related"

        # ---------------------------------
        # New
        # ---------------------------------

        return "new"

    def _normalize(self, value):

        if value is None:
            return ""

        text = str(value).lower().strip()

        text = re.sub(
            r"[^\w\s:-]",
            "",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text

    def _text_similarity(
        self,
        text_a,
        text_b,
    ):

        if not text_a or not text_b:
            return 0.0

        return SequenceMatcher(
            None,
            text_a,
            text_b,
        ).ratio()

    def _contains_update_word(
        self,
        text,
    ):

        words = set(text.split())

        return bool(
            words.intersection(
                self.UPDATE_WORDS
            )
        )