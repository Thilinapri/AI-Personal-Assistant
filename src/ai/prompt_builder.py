"""
prompt_builder.py

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
        current_time: datetime,
    ) -> str:

        if mode == "immediate":
            return self._build_immediate_prompt(
                text,
                current_time,
            )

        if mode == "summary":
            return self._build_summary_prompt(
                text,
                current_time,
            )

        raise ValueError(
            f"Unknown mode: {mode}"
        )

    def _build_immediate_prompt(
        self,
        text: str,
        current_time: datetime,
    ) -> str:

        return f"""
You are the Memory Engine of EchoMind,
an AI Personal Memory Assistant.

Current Date and Time:
{current_time.strftime("%Y-%m-%d %H:%M")}

Analyze the user's transcription and extract information
that should be remembered.

Allowed categories:
- Reminder
- Task
- Shopping
- Note
- Preference
- Event

IMPORTANT MEMORY RULES:

1. Return JSON ONLY.
2. Do not explain your reasoning.
3. If nothing useful should be remembered, return:

{{
    "memories": []
}}

4. Extract all useful memories when more than one is present.

5. Information that CHANGES or CORRECTS something previously
   mentioned is still an important memory and MUST be extracted.

Examples of update language include:
- moved
- changed
- rescheduled
- postponed
- updated
- cancelled
- now
- instead
- no longer
- changed to

For example:

"My project presentation has moved to Friday at 2 PM."

must be extracted as a memory.

Do NOT ignore it simply because it sounds like an update
to earlier information.

The Memory Manager will decide whether the extracted memory
is NEW, DUPLICATE, UPDATE, or RELATED.

6. For an update or correction:
- extract the NEW/current information
- use the new date and time
- keep a stable title describing the underlying event
- include the changed information clearly in content
- do not put words such as "updated version" in the title
  unless they are genuinely part of the event name

Example:

User:
"My project presentation has moved to September 25th at 2 PM instead."

Good extraction:

{{
    "category": "Reminder",
    "title": "Project presentation",
    "content": "Project presentation has moved to September 25th at 2:00 PM.",
    "date": "2026-09-25",
    "time": "14:00",
    "notification": true
}}

7. Keep titles stable whenever possible.

For example, these should normally use the same title:

"Project presentation is Friday at 10 AM."
"My project presentation moved to 2 PM."

Title:
"Project presentation"

This helps EchoMind compare the new memory with the
existing memory.

8. If the user explicitly says:
- remind me
- remember
- remember this
- don't forget

and the statement describes something the user wants
EchoMind to retain, prefer the Reminder category when appropriate.

9. Set "notification" to true when the user explicitly requests
a reminder or clearly asks EchoMind to remind them.

Examples:
- "Remind me about the meeting." -> true
- "Don't forget to remind me." -> true

For an update to an existing reminder-type event, keep
notification true when the user's wording clearly continues
the reminder intent.

10. Date format must be:

YYYY-MM-DD

or an empty string if there is no date.

11. Time format must be:

HH:MM

using 24-hour time,

or an empty string if there is no time.

Examples:
10 AM -> 10:00
2 PM -> 14:00
6:30 PM -> 18:30

12. Resolve explicit dates using the current date when necessary.

13. title and content must both be non-empty strings.

14. notification must be a JSON boolean:
true or false

15. Use exactly this JSON structure:

{{
    "memories": [
        {{
            "category": "",
            "title": "",
            "content": "",
            "date": "",
            "time": "",
            "notification": false
        }}
    ]
}}

User Transcription:

{text}
"""

    def _build_summary_prompt(
        self,
        text: str,
        current_time: datetime,
    ) -> str:

        return f"""
You are the Memory Engine of EchoMind,
an AI Personal Memory Assistant.

Current Date and Time:
{current_time.strftime("%Y-%m-%d %H:%M")}

The following conversation occurred during the recent
conversation session.

Write a short factual summary and extract only useful memories.

Allowed memory categories:
- Reminder
- Task
- Shopping
- Note
- Preference
- Event

Return JSON ONLY.
Do not use Markdown.
Do not explain your reasoning.

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

MEMORY RULES:

1. Include:
- category
- title
- content
- date
- time
- notification

2. title and content must be non-empty strings.

3. date must be:
YYYY-MM-DD
or an empty string.

4. time must be:
HH:MM
or an empty string.

5. notification must be a JSON boolean.

6. Extract updates and corrections as memories.

Statements such as:
- moved
- changed
- rescheduled
- postponed
- updated
- now
- instead

must not be ignored.

The Memory Manager will later decide whether the extracted
information is a new memory, duplicate, update, or related memory.

7. For updated information:
- extract the latest/current value
- keep the title stable where possible
- preserve the change in the content

8. Use an empty memories list when there are no useful
memories to save.

Conversation:

{text}
"""