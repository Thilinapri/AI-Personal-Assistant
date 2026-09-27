"""
Builds prompts for the Memory Engine.

This module does NOT communicate with Gemini.
It only builds prompts.
"""

from datetime import datetime


class PromptBuilder:

    def build(
        self,
        mode: str,
        text: str,
        current_time: datetime
    ) -> str:

        if mode == "immediate":
            return self._build_immediate_prompt(
                text,
                current_time
            )

        elif mode == "summary":
            return self._build_summary_prompt(
                text,
                current_time
            )

        raise ValueError(
            f"Unknown mode: {mode}"
        )

    def _build_immediate_prompt(
        self,
        text: str,
        current_time: datetime
    ) -> str:

        return f"""
You are the Memory Engine of an AI Personal Memory Assistant.

Current Date and Time:
{current_time.strftime("%Y-%m-%d %H:%M")}

Analyze the user's transcription and extract useful memories.

Allowed categories:
- Reminder
- Task
- Shopping
- Note
- Preference
- Event

Return JSON ONLY:

{{
    "memories":[
        {{
            "category":"",
            "title":"",
            "content":"",
            "date":"",
            "time":"",
            "notification":false,
            "reminder_before_hours":0
        }}
    ]
}}

Rules:

- Use only the allowed categories.
- title and content must be non-empty.
- date must be YYYY-MM-DD or "".
- time must be HH:MM in 24-hour format or "".
- Calculate relative dates using the current date and time.
- Do not invent dates or event times.
- If nothing should be stored, return an empty memories array.

Smart Reminder:

If an upcoming event or activity would benefit from a reminder,
set notification to true.

When notification is true, intelligently determine how many hours
before the event the reminder should be sent based on the event,
importance, preparation, travel, and context.

Return this value as reminder_before_hours.

Do not use a fixed reminder time for every event.

If no reminder is appropriate:
notification = false
reminder_before_hours = 0

User Transcription:


{text}
"""

    def _build_summary_prompt(
        self,
        text: str,
        current_time: datetime
    ) -> str:

        return f"""
You are the Memory Engine of an AI Personal Memory Assistant.

Current Date and Time:
{current_time.strftime("%Y-%m-%d %H:%M")}

The following conversation occurred during the last 20 minutes.

Write a short, factual summary and extract only useful memories.

Allowed memory categories:
- Reminder
- Task
- Shopping
- Note
- Preference
- Event

Return JSON ONLY.
Do not use Markdown or explain your reasoning.

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
            "notification": false,
            "reminder_before_hours": 0
        }}
    ]
}}

Rules for each memory:

- Include category, title, content, date, time,
  notification, and reminder_before_hours.
- category must be one of the allowed categories.
- title and content must be non-empty strings.
- date must be YYYY-MM-DD or an empty string.
- time must be HH:MM in 24-hour format or an empty string.
- notification must be a JSON boolean.
- reminder_before_hours must be a JSON number.
- Use reminder_before_hours = 0 when notification is false.
- Use an empty memories list when there are no memories to save.

Smart Reminder:

If a memory represents an upcoming event or activity that would
benefit from a reminder, set notification to true.

When notification is true, intelligently determine an appropriate
reminder lead time based on the event type, importance, preparation
required, travel requirements, and context.

Do not use one fixed reminder time for every event.

Return the selected lead time in "reminder_before_hours".

If no reminder is appropriate:

"notification": false,
"reminder_before_hours": 0

Do not invent an exact event time when the user did not provide one.

Conversation:

{text}
"""