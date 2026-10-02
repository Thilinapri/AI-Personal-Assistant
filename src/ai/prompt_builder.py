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
    "notification": true,
    "reminder_before_hours": 2
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

9. Set "notification" to true when:

- the user explicitly requests a reminder, OR
- the memory represents an upcoming event or activity that would
  reasonably benefit from a reminder.

Examples:
- "Remind me about the meeting." -> true
- "Don't forget to remind me." -> true
- an important upcoming appointment may also -> true

For an update to an existing reminder-type event, keep
notification true when the reminder is still useful.

10. SMART REMINDER:

When notification is true, intelligently determine how many hours
before the event the reminder should be sent.

Consider:
- event type
- importance
- preparation required
- travel requirements
- urgency
- available context

Return this value as:

"reminder_before_hours"

Do not use one fixed reminder time for every event.

Examples:
- routine meeting may need a short lead time
- exam or important presentation may need more preparation time
- travel-related events may need additional lead time

If notification is false:

"reminder_before_hours": 0

Do not invent an event date or event time that the user
did not provide.

11. Date format must be:

YYYY-MM-DD

or an empty string if there is no date.

12. Time format must be:

HH:MM

using 24-hour time,

or an empty string if there is no time.

Examples:
10 AM -> 10:00
2 PM -> 14:00
6:30 PM -> 18:30

13. Resolve explicit and relative dates using the current date
and time when necessary.

14. title and content must both be non-empty strings.

15. notification must be a JSON boolean:
true or false

16. reminder_before_hours must be a JSON number.

When notification is false, use:

"reminder_before_hours": 0

17. Use exactly this JSON structure:

{{
    "memories": [
        {{
            "category": "",
            "title": "",
            "content": "",
            "date": "",
            "time": "",
            "notification": false,
            "reminder_before_hours": 0
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
            "notification": false,
            "reminder_before_hours": 0
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
- reminder_before_hours

2. category must be one of the allowed categories.

3. title and content must be non-empty strings.

4. date must be:
YYYY-MM-DD
or an empty string.

5. time must be:
HH:MM
or an empty string.

6. notification must be a JSON boolean.

7. reminder_before_hours must be a JSON number.

8. Extract updates and corrections as memories.

Statements such as:
- moved
- changed
- rescheduled
- postponed
- updated
- cancelled
- now
- instead
- no longer

must not be ignored.

The Memory Manager will later decide whether the extracted
information is a new memory, duplicate, update, or related memory.

9. For updated information:
- extract the latest/current value
- keep the title stable where possible
- preserve the change in the content

10. SMART REMINDER:

If a memory represents an upcoming event or activity that would
benefit from a reminder, set notification to true.

When notification is true, intelligently determine an appropriate
reminder lead time based on:
- event type
- importance
- preparation required
- travel requirements
- urgency
- available context

Return the selected lead time in:

"reminder_before_hours"

Do not use one fixed reminder time for every event.

If no reminder is appropriate:

"notification": false,
"reminder_before_hours": 0

Do not invent an exact event date or time when the user
did not provide one.

11. Use an empty memories list when there are no useful
memories to save.

Conversation:

{text}
"""