"""
prompt_builder.py

Builds prompts for the Memory Engine.
This module does NOT communicate with Gemini.
It only builds prompts.
"""

from datetime import datetime


class PromptBuilder:

    def build(self, mode: str, text: str, current_time: datetime) -> str:

        if mode == "immediate":
            return self._build_immediate_prompt(text, current_time)

        elif mode == "summary":
            return self._build_summary_prompt(text, current_time)

        raise ValueError(f"Unknown mode: {mode}")

    def _build_immediate_prompt(self, text: str, current_time: datetime) -> str:

        return f"""
You are the Memory Engine of an AI Personal Memory Assistant.

Current Date and Time:
{current_time.strftime("%Y-%m-%d %H:%M")}

Analyze the user's transcription.

Determine whether it contains information that should be stored.

Allowed categories:
- Reminder
- Task
- Shopping
- Note
- Preference
- Event

Rules:

1. Return JSON ONLY.
2. Do not explain your reasoning.
3. If nothing should be stored return:

{{
    "memories":[]
}}

4. If there are multiple memories return all of them.

5. Use this JSON format exactly:

{{
    "memories":[
        {{
            "category":"",
            "title":"",
            "content":"",
            "date":"",
            "time":"",
            "notification":false
        }}
    ]
}}

User Transcription:

{text}
"""

    def _build_summary_prompt(self, text: str, current_time: datetime) -> str:

        return f"""
You are the Memory Engine of an AI Personal Memory Assistant.

Current Date and Time:
{current_time.strftime("%Y-%m-%d %H:%M")}

The following conversation occurred during the last 20 minutes. Write a short,
factual summary and extract only useful memories.

Allowed memory categories:
- Reminder
- Task
- Shopping
- Note
- Preference
- Event

Return JSON ONLY. Do not use Markdown or explain your reasoning.

Use this exact response structure:

{{
    "summary": "Short factual summary.",
    "memories": [
        {{
            "category": "Task",
            "title": "Schedule dentist appointment",
            "content": "User needs to schedule a dentist appointment next week.",
            "date": "",
            "time": "",
            "notification": false
        }}
    ]
}}

Rules for each memory:
- Include category, title, content, date, time, and notification.
- title and content must be non-empty strings.
- date must be YYYY-MM-DD or an empty string.
- time must be HH:MM in 24-hour time or an empty string.
- notification must be a JSON boolean.
- Use an empty memories list when there are no memories to save.

Conversation:

{text}
"""
