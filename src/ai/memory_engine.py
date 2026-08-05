import json

from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

from src.ai.prompt_builder import PromptBuilder
from src.config import GEMINI_MODEL

class MemoryEngine:

    def __init__(self):

        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found.")

        self.client = genai.Client(api_key=api_key)
        self.prompt_builder = PromptBuilder()

    def process(self, mode, text, current_time):

        prompt = self.prompt_builder.build(
            mode=mode,
            text=text,
            current_time=current_time
        )

      

        response = self.client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )

        return json.loads(response.text)