"""
ai_wrapper.py
─────────────
The ONLY place in the project that calls the Gemini API.
All other modules must import and use generate() or generate_from_image() from here.
"""

import os
import time
import json
import logging

from dotenv import load_dotenv
from google import genai
from google.genai import types

# ── Load environment variables ────────────────────────────────────────────────
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
AI_MOCK        = os.getenv("AI_MOCK", "false").lower() in ("true", "1", "yes")
AI_MOCK_INVALID = os.getenv("AI_MOCK_INVALID", "false").lower() in ("true", "1", "yes")

# ── Set up a module-level logger ──────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ── Initialise the Gemini client ONCE at import time ─────────────────────────
if not GEMINI_API_KEY and not AI_MOCK:
    logger.warning("GEMINI_API_KEY is not set – AI calls will fail.")

_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


# ── Sample responses for Mock Mode ────────────────────────────────────────────

SAMPLE_EXPLAIN_JSON = json.dumps({
    "topic_type": "concept",
    "simple_explanation": "A stack is a linear data structure that follows the Last-In, First-Out (LIFO) principle. Think of it like a stack of plates where you add and remove from the top.",
    "exam_answer": "1) Definition: A stack is a linear data structure following the LIFO principle.\n2) Key Points:\n- Elements are added and removed only from the top.\n- Push adds an element to the stack.\n- Pop removes the top element.\n- Peek views the top element without removing it.\n3) Example: A pile of plates where the last placed plate is taken first."
})

SAMPLE_QUIZ_JSON = json.dumps([
    {
        "id": 1,
        "type": "mcq",
        "question": "What principle does a Stack data structure follow?",
        "options": ["FIFO (First In First Out)", "LIFO (Last In First Out)", "Random Access", "Priority Order"],
        "correct_answer": "LIFO (Last In First Out)",
        "explanation": "Stacks always insert and remove elements from the top end using LIFO.",
        "topic": "Stack Principle"
    },
    {
        "id": 2,
        "type": "mcq",
        "question": "Which operation is used to add an item to the top of a stack?",
        "options": ["pop", "enqueue", "push", "dequeue"],
        "correct_answer": "push",
        "explanation": "Push inserts an item onto the top of the stack.",
        "topic": "Stack Operations"
    },
    {
        "id": 3,
        "type": "mcq",
        "question": "What condition occurs when attempting to pop from an empty stack?",
        "options": ["Overflow", "Underflow", "Memory Leak", "Segmentation Fault"],
        "correct_answer": "Underflow",
        "explanation": "Removing an item when the stack is empty causes an underflow error.",
        "topic": "Error Handling"
    },
    {
        "id": 4,
        "type": "mcq",
        "question": "In Python, which list method corresponds directly to the push operation?",
        "options": ["insert(0, item)", "append(item)", "extend(item)", "add(item)"],
        "correct_answer": "append(item)",
        "explanation": "list.append() appends to the end of the list in O(1) time.",
        "topic": "Python Implementation"
    },
    {
        "id": 5,
        "type": "short",
        "question": "What does LIFO stand for, and why is it used to describe a stack?",
        "options": [],
        "correct_answer": "LIFO stands for Last In, First Out; the most recently added item is the first one removed.",
        "explanation": "LIFO means the last element pushed onto the stack is the first element popped off.",
        "topic": "LIFO Concept"
    }
])


# ── Shared retry helper ───────────────────────────────────────────────────────

def _call_with_retry(contents) -> str:
    """
    Internal helper: send *contents* to Gemini and retry once on failure.

    Returns the model's text response, or a string starting with "ERROR:".
    Never raises.
    """
    if _client is None:
        return "ERROR: GEMINI_API_KEY is missing and mock mode is off."

    for attempt in range(2):          # attempt 0 = first try, attempt 1 = retry
        try:
            response = _client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
            )
            return response.text

        except Exception as exc:
            logger.error("Gemini call failed (attempt %d): %s", attempt + 1, exc)

            err_str = str(exc).lower()
            is_rate_limit = "429" in err_str or "quota" in err_str or "rate" in err_str

            if attempt == 0:
                wait = 5 if is_rate_limit else 2
                logger.info("Retrying in %s s …", wait)
                time.sleep(wait)
            else:
                if is_rate_limit:
                    return (
                        "ERROR: The AI service is busy (rate limit reached). "
                        "Please wait a moment and try again."
                    )
                return f"ERROR: The AI service is unavailable. Details: {exc}"

    return "ERROR: Unknown failure in ai_wrapper._call_with_retry()."


# ── Public API ────────────────────────────────────────────────────────────────

def generate(prompt: str) -> str:
    """
    Send a text *prompt* to Gemini and return the text response.
    If AI_MOCK=true, returns fixed sample JSON based on prompt type.

    Returns
    ───────
    str  – the model's text, or an error message starting with "ERROR:".
    """
    if AI_MOCK:
        logger.info("AI_MOCK is enabled: returning mocked response.")
        if AI_MOCK_INVALID:
            logger.info("AI_MOCK_INVALID is active: returning deliberately invalid JSON.")
            return "This is deliberately invalid non-JSON output for error testing."
        if "quiz" in prompt.lower():
            return SAMPLE_QUIZ_JSON
        if "simulation" in prompt.lower() or "template" in prompt.lower():
            return "none"
        return SAMPLE_EXPLAIN_JSON

    return _call_with_retry(prompt)


def generate_from_image(image_bytes: bytes, mime_type: str, prompt: str) -> str:
    """
    Send an image together with a text *prompt* to Gemini and return the
    text response.

    If AI_MOCK=true, returns a sample transcription.
    """
    if AI_MOCK:
        logger.info("AI_MOCK is enabled: returning mocked transcription.")
        return "Sample transcribed study notes from image: Stacks follow LIFO principles."

    if _client is None:
        return "ERROR: GEMINI_API_KEY is missing and mock mode is off."

    contents = [
        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        types.Part.from_text(text=prompt),
    ]
    return _call_with_retry(contents)
