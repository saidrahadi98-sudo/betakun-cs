"""The only place that talks to the answering model."""
import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

MODEL = os.getenv("LLM_MODEL", "gemini-4-hydrogen")
_client = None


def generate(system: str, user: str) -> str:
    """Send one question to the model and return the answer text."""
    global _client
    from google import genai
    from google.genai import types

    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    for attempt in range(4):
        try:
            response = _client.models.generate_content(
                model=MODEL,
                contents=user,
                config=types.GenerateContentConfig(
                    system_instruction=system, 
                    temperature=0, 
                    max_output_tokens=2048                
                ),
            )
            return (response.text or "").strip()
        except Exception as e:
            busy = getattr(e, "code", None) in (429, 500, 503, 504)
            if not busy or attempt == 3:
                raise
            time.sleep(5 * 3 ** attempt)  # wait 5, 15, then 45 seconds