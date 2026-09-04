class DisabledMemoryEngine:
    """Placeholder memory engine used while Gemini is disabled."""

    def process(self, mode, text, current_time):
        return {
            "summary": "",
            "memories": [],
        }
