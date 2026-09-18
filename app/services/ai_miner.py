import json
import re
import logging
from google import genai
from groq import AsyncGroq
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.rule import RuleSchema

logger = logging.getLogger(__name__)

GROQ_API_KEYS = settings.groq_keys_list
GEMINI_API_KEYS = settings.gemini_keys_list

current_groq_idx = 0
current_gemini_idx = 0


async def extract_rules_from_text(raw_text: str) -> list[dict]:
    global current_groq_idx
    prompt = f"""
    You are an Expert Senior Backend Architect. Analyze the following technical text.
    Extract key code review rules, anti-patterns, or best practices for Python, FastAPI, or SQLAlchemy.

    Text excerpt:
    {raw_text[:14000]}

    Return the result STRICTLY as a JSON array of objects. Each object must have:
    - "name": string (short rule name)
    - "description": string (why it matters)
    - "example_bad": string (code snippet showing anti-pattern)
    - "example_good": string (correct approach code snippet)
    - "technologies": array of strings (e.g. ["python", "fastapi"], lowercase)

    If no relevant rules can be extracted, return an empty JSON array [].
    Do not wrap JSON in markdown blocks like ```json.
    """

    attempts = 0
    max_attempts = len(GROQ_API_KEYS)

    while attempts < max_attempts:
        client = AsyncGroq(api_key=GROQ_API_KEYS[current_groq_idx])
        try:
            response = await client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            content = response.choices[0].message.content.strip()

            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                try:
                    raw_json = json.loads(match.group(0))
                    validated_rules = [
                        RuleSchema(**rule).model_dump() for rule in raw_json
                    ]
                    return validated_rules
                except (json.JSONDecodeError, ValidationError) as e:
                    logger.warning(f"Groq output validation failed: {e}. Skipping.")
                    return []
            return []
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "rate limit" in error_msg or "503" in error_msg:
                logger.warning(f"Groq Key {current_groq_idx} failed. Switching key.")
                current_groq_idx = (current_groq_idx + 1) % len(GROQ_API_KEYS)
                attempts += 1
            else:
                logger.error("Failed to extract rules using Groq API", exc_info=True)
                raise e

    logger.error("ALL Groq API Keys are exhausted!")
    raise Exception("429 ALL GROQ KEYS EXHAUSTED")


async def generate_embedding(text: str) -> list[float]:
    global current_gemini_idx
    attempts = 0
    max_attempts = len(GEMINI_API_KEYS)

    while attempts < max_attempts:
        client = genai.Client(api_key=GEMINI_API_KEYS[current_gemini_idx])
        try:
            response = await client.aio.models.embed_content(
                model="gemini-embedding-2", contents=text
            )
            if response.embeddings:
                return response.embeddings[0].values
            return []
        except Exception as e:
            error_msg = str(e).lower()
            if (
                "429" in error_msg
                or "resource_exhausted" in error_msg
                or "503" in error_msg
            ):
                logger.warning(
                    f"Gemini Key {current_gemini_idx} failed. Switching key."
                )
                current_gemini_idx = (current_gemini_idx + 1) % len(GEMINI_API_KEYS)
                attempts += 1
            else:
                logger.error("Failed to generate embedding using Gemini", exc_info=True)
                raise e

    logger.error("ALL Gemini API Keys are exhausted!")
    raise Exception("429 ALL GEMINI KEYS EXHAUSTED")
