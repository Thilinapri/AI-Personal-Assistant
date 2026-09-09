import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.ai.memory_engine import MemoryEngine


class FakePrivacyGateway:

    def __init__(
        self,
        result=None,
        error=None,
        output_safe=True,
        validation_error=None,
    ):
        self.result = result
        self.error = error
        self.output_safe = output_safe
        self.validation_error = validation_error
        self.calls = []
        self.validation_calls = []

    def prepare(
        self,
        sentences,
        mode,
        purpose,
        pinned_original_index=None,
    ):
        self.calls.append(
            {
                "sentences": list(sentences),
                "mode": mode,
                "purpose": purpose,
                "pinned_original_index": (
                    pinned_original_index
                ),
            }
        )

        if self.error is not None:
            raise self.error

        return self.result

    def validate_cloud_output(
        self,
        value,
    ):
        self.validation_calls.append(
            value
        )

        if self.validation_error is not None:
            raise self.validation_error

        if self.output_safe:
            return (
                True,
                [],
            )

        return (
            False,
            ["PASSWORD"],
        )

    @staticmethod
    def rehydrate_output(
        text,
        mapping,
    ):
        result = text

        for placeholder, original in (
            mapping.items()
        ):
            result = result.replace(
                placeholder,
                original,
            )

        return result


class FakePromptBuilder:

    def __init__(self):
        self.calls = []

    def build(
        self,
        mode,
        text,
        current_time,
    ):
        self.calls.append(
            {
                "mode": mode,
                "text": text,
                "current_time": current_time,
            }
        )

        return f"PROMPT::{text}"


class MemoryEnginePrivacyTests(
    unittest.TestCase
):

    def setUp(self):

        self.client = MagicMock()

        self.client.models.generate_content = (
            MagicMock()
        )

        self.client.models.generate_content.return_value = (
            SimpleNamespace(
                text='{"memories": []}'
            )
        )

        self.env_patch = patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": (
                    "test-only-key"
                )
            },
            clear=False,
        )

        self.dotenv_patch = patch(
            "src.ai.memory_engine.load_dotenv"
        )

        self.client_patch = patch(
            "src.ai.memory_engine.genai.Client",
            return_value=self.client,
        )

        self.env_patch.start()
        self.dotenv_patch.start()
        self.client_patch.start()

    def tearDown(self):

        self.client_patch.stop()
        self.dotenv_patch.stop()
        self.env_patch.stop()

    def make_engine(
        self,
        gateway,
    ):

        engine = MemoryEngine(
            privacy_gateway=gateway
        )

        engine.prompt_builder = (
            FakePromptBuilder()
        )

        return engine

    def test_privacy_gateway_is_required(self):

        with self.assertRaises(
            ValueError
        ):
            MemoryEngine(
                privacy_gateway=None
            )

    def test_blocked_privacy_result_never_calls_gemini(
        self,
    ):

        privacy_result = SimpleNamespace(
            cloud_allowed=False,
        )

        gateway = FakePrivacyGateway(
            result=privacy_result
        )

        engine = self.make_engine(
            gateway
        )

        result = engine.process(
            mode="immediate",
            sentences=[
                "My password is Secret123."
            ],
            current_time=datetime.now(),
        )

        self.assertEqual(
            result,
            {
                "memories": [],
            },
        )

        self.client.models.generate_content.assert_not_called()

    def test_privacy_gateway_error_never_calls_gemini(
        self,
    ):

        gateway = FakePrivacyGateway(
            error=RuntimeError(
                "privacy failure"
            )
        )

        engine = self.make_engine(
            gateway
        )

        result = engine.process(
            mode="immediate",
            sentences=[
                "Raw private transcript."
            ],
            current_time=datetime.now(),
        )

        self.assertEqual(
            result,
            {
                "memories": [],
            },
        )

        self.client.models.generate_content.assert_not_called()

    def test_only_sanitized_capsule_reaches_prompt(
        self,
    ):

        raw_text = (
            "Remind me to email "
            "person@example.com tomorrow."
        )

        sanitized_text = (
            "Remind me to email "
            "<EMAIL_1> tomorrow."
        )

        privacy_result = SimpleNamespace(
            cloud_allowed=True,
            capsule=SimpleNamespace(
                text=sanitized_text
            ),
            mapping={},
        )

        gateway = FakePrivacyGateway(
            result=privacy_result
        )

        engine = self.make_engine(
            gateway
        )

        engine.process(
            mode="immediate",
            sentences=[
                raw_text
            ],
            current_time=datetime.now(),
        )

        self.assertEqual(
            engine.prompt_builder.calls[0]["text"],
            sanitized_text,
        )

        self.assertNotEqual(
            engine.prompt_builder.calls[0]["text"],
            raw_text,
        )

        self.client.models.generate_content.assert_called_once()

    def test_amber_placeholders_are_rehydrated_locally(
        self,
    ):

        privacy_result = SimpleNamespace(
            cloud_allowed=True,
            capsule=SimpleNamespace(
                text=(
                    "Remind me to email "
                    "<EMAIL_1> tomorrow."
                )
            ),
            mapping={
                "<EMAIL_1>": (
                    "person@example.com"
                )
            },
        )

        gateway = FakePrivacyGateway(
            result=privacy_result
        )

        engine = self.make_engine(
            gateway
        )

        self.client.models.generate_content.return_value = (
            SimpleNamespace(
                text=(
                    '{"memories": ['
                    '{"content": '
                    '"Email <EMAIL_1> tomorrow"}'
                    ']}'
                )
            )
        )

        result = engine.process(
            mode="immediate",
            sentences=[
                (
                    "Remind me to email "
                    "person@example.com tomorrow."
                )
            ],
            current_time=datetime.now(),
        )

        self.assertEqual(
            result["memories"][0]["content"],
            (
                "Email person@example.com "
                "tomorrow"
            ),
        )

    def test_unsafe_cloud_output_is_discarded_before_rehydration(
        self,
    ):

        privacy_result = SimpleNamespace(
            cloud_allowed=True,
            capsule=SimpleNamespace(
                text="Safe sanitized context."
            ),
            mapping={},
        )

        gateway = FakePrivacyGateway(
            result=privacy_result,
            output_safe=False,
        )

        engine = self.make_engine(
            gateway
        )

        self.client.models.generate_content.return_value = (
            SimpleNamespace(
                text=(
                    '{"memories": ['
                    '{"content": '
                    '"Use password Secret123"'
                    '}]}'
                )
            )
        )

        result = engine.process(
            mode="immediate",
            sentences=[
                "Safe sanitized context."
            ],
            current_time=datetime.now(),
        )

        self.assertEqual(
            result,
            {
                "memories": [],
            },
        )

        self.assertEqual(
            len(gateway.validation_calls),
            1,
        )

    def test_cloud_output_validation_error_fails_closed(
        self,
    ):

        privacy_result = SimpleNamespace(
            cloud_allowed=True,
            capsule=SimpleNamespace(
                text="Safe sanitized context."
            ),
            mapping={},
        )

        gateway = FakePrivacyGateway(
            result=privacy_result,
            validation_error=RuntimeError(
                "output validation failure"
            ),
        )

        engine = self.make_engine(
            gateway
        )

        result = engine.process(
            mode="immediate",
            sentences=[
                "Safe sanitized context."
            ],
            current_time=datetime.now(),
        )

        self.assertEqual(
            result,
            {
                "memories": [],
            },
        )


if __name__ == "__main__":
    unittest.main()