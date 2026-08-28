class RelationshipClassifier:
    """Classifies the relationship between two memories."""

    VALID_RELATIONSHIPS = {
        "duplicate",
        "update",
        "related",
        "new",
    }

    def classify(self, new_memory, existing_memory):
        """
        Determine how a new memory relates to an existing memory.

        A real AI classifier can be plugged in later.
        """

        raise NotImplementedError(
            "A relationship classifier implementation is required."
        )
    