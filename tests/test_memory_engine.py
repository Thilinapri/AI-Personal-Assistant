import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.ai.memory_engine import MemoryEngine
from src.ai.openrouter_client import OpenRouterClientError


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


class FakeContextSelector:

    def __init__(
        self,
        selected_items=None,
        error=None,
    ):
        self.selected_items = (
            selected_items
            if selected_items is not None
            else []
        )
        self.error = error
        self.calls = []

    def select(
        self,
        sentences,
    ):
        self.calls.append(
            list(sentences)
        )

        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            selected_items=self.selected_items
        )


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
        gateway=None,
        context_selector=None,
    ):

        engine = MemoryEngine(
            privacy_gateway=gateway,
            context_selector=context_selector,
            provider="gemini",
        )

        engine.prompt_builder = (
            FakePromptBuilder()
        )

        return engine

    def test_engine_requires_privacy_or_context_selector(
        self,
    ):

        with self.assertRaises(
            ValueError
        ):
            MemoryEngine(
                privacy_gateway=None,
                context_selector=None,
                provider="gemini",
            )

    def test_privacy_gateway_is_optional_when_context_selector_exists(
        self,
    ):

        selector = FakeContextSelector(
            selected_items=[
                SimpleNamespace(
                    original_index=0,
                    text=(
                        "I have a meeting "
                        "tomorrow at 2 PM."
                    ),
                )
            ]
        )

        engine = self.make_engine(
            gateway=None,
            context_selector=selector,
        )

        result = engine.process(
            mode="summary",
            sentences=[
                (
                    "I have a meeting "
                    "tomorrow at 2 PM."
                )
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
            len(selector.calls),
            1,
        )

        self.assertEqual(
            engine.prompt_builder.calls[0]["text"],
            (
                "I have a meeting "
                "tomorrow at 2 PM."
            ),
        )

        self.client.models.generate_content.assert_called_once()

    def test_privacy_off_keeps_immediate_trigger_sentence(
        self,
    ):

        selector = FakeContextSelector(
            selected_items=[]
        )

        engine = self.make_engine(
            gateway=None,
            context_selector=selector,
        )

        sentence = (
            "Remember, my meeting is "
            "tomorrow at 2 PM."
        )

        engine.process(
            mode="immediate",
            sentences=[
                sentence
            ],
            current_time=datetime.now(),
        )

        self.assertEqual(
            engine.prompt_builder.calls[0]["text"],
            sentence,
        )

        self.client.models.generate_content.assert_called_once()

    def test_privacy_off_context_selector_error_stops_gemini(
        self,
    ):

        selector = FakeContextSelector(
            error=RuntimeError(
                "selector failure"
            )
        )

        engine = self.make_engine(
            gateway=None,
            context_selector=selector,
        )

        result = engine.process(
            mode="summary",
            sentences=[
                "Potential memory."
            ],
            current_time=datetime.now(),
        )

        self.assertEqual(
            result,
            {
                "summary": "",
                "memories": [],
            },
        )

        self.client.models.generate_content.assert_not_called()

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
            gateway=gateway
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
            gateway=gateway
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
            gateway=gateway
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
            gateway=gateway
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
            gateway=gateway
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
            len(
                gateway.validation_calls
            ),
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
            gateway=gateway
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


class OpenRouterMemoryEngineTests(unittest.TestCase):

    def setUp(self):
        self.router_patcher = patch(
            "src.ai.memory_engine.OpenRouterClient"
        )
        self.gemini_patcher = patch(
            "src.ai.memory_engine.genai.Client"
        )
        self.dotenv_patcher = patch(
            "src.ai.memory_engine.load_dotenv"
        )
        self.router_class = self.router_patcher.start()
        self.gemini_class = self.gemini_patcher.start()
        self.dotenv_patcher.start()
        self.router = self.router_class.return_value
        self.router.generate_text.return_value = (
            '{"memories": []}'
        )

    def tearDown(self):
        self.dotenv_patcher.stop()
        self.gemini_patcher.stop()
        self.router_patcher.stop()

    def make_engine(
        self,
        gateway=None,
        context_selector=None,
    ):
        if gateway is None and context_selector is None:
            context_selector = FakeContextSelector()

        engine = MemoryEngine(
            privacy_gateway=gateway,
            context_selector=context_selector,
            provider="openrouter",
        )
        engine.prompt_builder = FakePromptBuilder()
        return engine

    def test_initialization_uses_only_openrouter(self):
        self.make_engine()
        self.router_class.assert_called_once_with()
        self.gemini_class.assert_not_called()

    def test_gemini_key_is_not_required(self):
        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": ""},
        ):
            self.make_engine()

        self.router_class.assert_called_once()
        self.gemini_class.assert_not_called()

    def test_immediate_prompt_reaches_openrouter(self):
        selector = FakeContextSelector(
            selected_items=[
                SimpleNamespace(
                    original_index=0,
                    text="Remember the dentist appointment.",
                )
            ]
        )
        engine = self.make_engine(
            context_selector=selector
        )

        engine.process(
            mode="immediate",
            sentences=[
                "Remember the dentist appointment."
            ],
            current_time=datetime.now(),
        )

        self.router.generate_text.assert_called_once_with(
            "PROMPT::Remember the dentist appointment."
        )

    def test_summary_prompt_reaches_openrouter(self):
        selector = FakeContextSelector(
            selected_items=[
                SimpleNamespace(
                    original_index=0,
                    text="The team meeting is tomorrow.",
                )
            ]
        )
        engine = self.make_engine(
            context_selector=selector
        )

        engine.process(
            mode="summary",
            sentences=[
                "The team meeting is tomorrow.",
            ],
            current_time=datetime.now(),
        )

        self.router.generate_text.assert_called_once_with(
            "PROMPT::The team meeting is tomorrow."
        )

    def test_openrouter_json_is_parsed_into_memory_structure(self):
        self.router.generate_text.return_value = (
            '{"memories": [{"category": "Reminder", '
            '"title": "Dentist", "content": "Dentist appointment", '
            '"date": "", "time": "", "notification": true, '
            '"reminder_before_hours": 2}]}'
        )
        engine = self.make_engine()

        result = engine.process(
            mode="immediate",
            sentences=["Dentist appointment tomorrow."],
            current_time=datetime.now(),
        )

        self.assertEqual(
            result["memories"][0]["title"],
            "Dentist",
        )
        self.assertTrue(
            result["memories"][0]["notification"]
        )

    def test_immediate_and_summary_output_structures(self):
        engine = self.make_engine(
            context_selector=FakeContextSelector(
                selected_items=[
                    SimpleNamespace(
                        original_index=0,
                        text="Meeting discussed tomorrow.",
                    )
                ]
            )
        )

        self.router.generate_text.return_value = (
            '{"memories": []}'
        )
        immediate = engine.process(
            mode="immediate",
            sentences=["Remember this."],
            current_time=datetime.now(),
        )
        self.assertEqual(
            immediate,
            {"memories": []},
        )

        self.router.generate_text.return_value = (
            '{"summary": "Meeting discussed.", "memories": []}'
        )
        summary = engine.process(
            mode="summary",
            sentences=["Meeting discussed tomorrow."],
            current_time=datetime.now(),
        )
        self.assertEqual(
            summary,
            {
                "summary": "Meeting discussed.",
                "memories": [],
            },
        )

    def test_unsupported_provider_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "Unsupported memory LLM provider",
        ):
            MemoryEngine(
                privacy_gateway=None,
                context_selector=FakeContextSelector(),
                provider="unsupported",
            )

        self.router_class.assert_not_called()
        self.gemini_class.assert_not_called()

    def test_blocked_privacy_gateway_prevents_openrouter(self):
        gateway = FakePrivacyGateway(
            result=SimpleNamespace(
                cloud_allowed=False
            )
        )
        engine = self.make_engine(gateway=gateway)

        result = engine.process(
            mode="immediate",
            sentences=["Raw private information."],
            current_time=datetime.now(),
        )

        self.assertEqual(
            result,
            {"memories": []},
        )
        self.router.generate_text.assert_not_called()

    def test_privacy_gateway_exception_prevents_openrouter(self):
        gateway = FakePrivacyGateway(
            error=RuntimeError("privacy failure")
        )
        engine = self.make_engine(gateway=gateway)

        result = engine.process(
            mode="immediate",
            sentences=["Raw private information."],
            current_time=datetime.now(),
        )

        self.assertEqual(
            result,
            {"memories": []},
        )
        self.router.generate_text.assert_not_called()

    def test_only_sanitized_capsule_reaches_openrouter(self):
        gateway = FakePrivacyGateway(
            result=SimpleNamespace(
                cloud_allowed=True,
                capsule=SimpleNamespace(
                    text="Email <EMAIL_1> tomorrow."
                ),
                mapping={
                    "<EMAIL_1>": "person@example.com"
                },
            )
        )
        engine = self.make_engine(gateway=gateway)

        engine.process(
            mode="immediate",
            sentences=[
                "Email person@example.com tomorrow."
            ],
            current_time=datetime.now(),
        )

        prompt = engine.prompt_builder.calls[0]["text"]
        self.assertEqual(
            prompt,
            "Email <EMAIL_1> tomorrow.",
        )
        self.assertNotIn(
            "person@example.com",
            prompt,
        )
        self.router.generate_text.assert_called_once()

    def test_output_validation_precedes_rehydration(self):
        gateway = FakePrivacyGateway(
            result=SimpleNamespace(
                cloud_allowed=True,
                capsule=SimpleNamespace(
                    text="Safe <EMAIL_1> context."
                ),
                mapping={
                    "<EMAIL_1>": "person@example.com"
                },
            ),
            output_safe=False,
        )
        gateway.rehydrate_output = MagicMock(
            side_effect=gateway.rehydrate_output
        )
        engine = self.make_engine(gateway=gateway)
        self.router.generate_text.return_value = (
            '{"memories": [{"content": "Use Secret123"}]}'
        )

        result = engine.process(
            mode="immediate",
            sentences=["Safe context."],
            current_time=datetime.now(),
        )

        self.assertEqual(
            result,
            {"memories": []},
        )
        self.assertEqual(
            len(gateway.validation_calls),
            1,
        )
        gateway.rehydrate_output.assert_not_called()

    def test_validated_output_is_rehydrated_locally(self):
        gateway = FakePrivacyGateway(
            result=SimpleNamespace(
                cloud_allowed=True,
                capsule=SimpleNamespace(
                    text="Email <EMAIL_1> tomorrow."
                ),
                mapping={
                    "<EMAIL_1>": "person@example.com"
                },
            )
        )
        engine = self.make_engine(gateway=gateway)
        self.router.generate_text.return_value = (
            '{"memories": [{"content": "Email <EMAIL_1> tomorrow"}]}'
        )

        result = engine.process(
            mode="immediate",
            sentences=[
                "Email person@example.com tomorrow."
            ],
            current_time=datetime.now(),
        )

        self.assertEqual(
            result["memories"][0]["content"],
            "Email person@example.com tomorrow",
        )

    def test_invalid_model_json_raises_safe_error(self):
        engine = self.make_engine()
        self.router.generate_text.return_value = (
            "raw secret response"
        )

        with self.assertRaisesRegex(
            ValueError,
            "Invalid JSON returned by the memory provider",
        ):
            engine.process(
                mode="immediate",
                sentences=["Remember this."],
                current_time=datetime.now(),
            )

    def test_openrouter_error_does_not_trigger_gemini(self):
        engine = self.make_engine()
        self.router.generate_text.side_effect = (
            OpenRouterClientError(
                "OpenRouter request failed."
            )
        )

        with self.assertRaises(
            OpenRouterClientError
        ):
            engine.process(
                mode="immediate",
                sentences=["Remember this."],
                current_time=datetime.now(),
            )

        self.gemini_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()