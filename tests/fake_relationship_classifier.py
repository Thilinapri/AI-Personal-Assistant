from src.memory.relationship_classifier import RelationshipClassifier


class FakeRelationshipClassifier(RelationshipClassifier):
    """Simple classifier used for local tests."""

    def __init__(self, relationship="new"):

        if relationship not in self.VALID_RELATIONSHIPS:
            raise ValueError(
                f"Invalid relationship: {relationship}"
            )

        self.relationship = relationship

    def classify(self, new_memory, existing_memory):
        """Return the relationship selected for the test."""

        return self.relationship