"""The only place that talks to the answering model."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MODEL = os.getenv("LLM_MODEL", "gemini-4-hydrogen")
_client = None


def generate(system: str, user: str) -> str:
    """Send one question to the model and return the answer text."""
    global _client
    from google import genai
    from google.genai import types

    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = _client.models.generate_content(
        model=MODEL,
        contents=user,
        config=types.GenerateContentConfig(system_instruction=system, max_output_tokens=2048),
    )
    text = (response.text or "").strip()
    # max_output_tokens was 400 at first and the answer came back empty;
    # the model's thinking used up the limit, so it was raised to 2048.
    # if not text: 
       # print("DEBUG empty answer, finish reason:", response.candidates[0].finish_reason if response.candidates else "no candidates")
    return text