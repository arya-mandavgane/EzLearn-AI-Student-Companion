"""
text_cleaner.py — Input text cleaning, validation, and language detection.
"""
import re
from typing import Tuple, List

# Devanagari Unicode range for Hindi / Marathi
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")

# Common Hinglish marker words
HINGLISH_WORDS = {
    "kya", "hai", "nahi", "kaise", "hota", "hoti", "hote", "bhi",
    "aur", "yeh", "woh", "kar", "karna", "samajh", "batao", "padhna",
    "seekhna", "padho", "karo", "accha", "bahut", "thoda", "kuch",
}

# Common Marathi marker words
MARATHI_WORDS = {
    "आहे", "नाही", "कसे", "करा", "पाहिजे", "म्हणजे", "काय", "आणि", "पण",
    "कसा", "कशी", "झाले", "झाला", "झाली", "करणे", "शिकणे", "अभ्यास",
}


def clean_text(text: str) -> str:
    """Normalize whitespace and remove non-printable control characters."""
    if not text:
        return ""
    # Remove null bytes and non-printable control characters (except newline, tab)
    cleaned = "".join(ch for ch in text if ch in ("\n", "\r", "\t") or ch >= " ")
    # Replace multiple spaces with single space, preserve paragraphs
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.splitlines()]
    return "\n".join(lines).strip()


def validate_text(text: str) -> Tuple[bool, str]:
    """
    Validate that text has meaningful content (not empty, whitespace only, or only emojis).
    Returns (is_valid, error_message).
    """
    cleaned = clean_text(text)
    if not cleaned:
        return False, "Input text cannot be empty or whitespace only."

    # Check for meaningful alphanumeric or word characters
    has_letters = bool(re.search(r"[\w\u0900-\u097F]", cleaned))
    if not has_letters:
        return False, "Input contains only symbols or emojis. Please provide readable study notes."

    return True, ""


def detect_language(text: str) -> str:
    """
    Detect language: 'hi' (Hindi), 'mr' (Marathi), 'hinglish', or 'en' (English).
    """
    if not text:
        return "en"

    devanagari_chars = len(DEVANAGARI_RE.findall(text))
    total_alpha = len(re.findall(r"[a-zA-Z\u0900-\u097F]", text))

    if total_alpha == 0:
        return "en"

    # If significant Devanagari script present
    if devanagari_chars / total_alpha > 0.2:
        # Check for specific Marathi markers
        words = {w.strip(".,!?:;\"'।") for w in text.split()}
        if any(mw in words for mw in MARATHI_WORDS):
            return "mr"
        return "hi"

    # If Roman script, check for Hinglish words
    words_lower = {w.lower().strip(".,!?:;\"'()") for w in text.split()}
    hinglish_matches = words_lower.intersection(HINGLISH_WORDS)
    if len(hinglish_matches) >= 2 or (len(words_lower) <= 10 and len(hinglish_matches) >= 1):
        return "hinglish"

    return "en"


def check_prompt_injection(text: str) -> Tuple[bool, List[str]]:
    """
    Detect adversarial attempts like 'ignore previous instructions', 'reveal prompt', etc.
    Returns (is_suspicious, warnings).
    """
    lower = text.lower()
    suspicious_patterns = [
        "ignore previous instructions",
        "ignore all previous instructions",
        "system prompt",
        "you are now in developer mode",
        "jailbreak",
        "disregard all previous",
        "override system",
    ]
    warnings = []
    for pattern in suspicious_patterns:
        if pattern in lower:
            warnings.append(
                "Notice: Your input contains system-like commands. "
                "These will be treated strictly as study data and not executed as AI instructions."
            )
            return True, warnings

    return False, []


RANDOM_COMMAND_PATTERNS = [
    r"^(hi|hello|hey|yo|hola|namaste|good\s+(morning|afternoon|evening|night)|howdy)[\s\.,!]*$",
    r"^who\s+(are\s+you|created\s+you|made\s+you)[\s\.,!\?]*$",
    r"^what\s+(is\s+your\s+name|can\s+you\s+do)[\s\.,!\?]*$",
    r"^(tell\s+me\s+a\s+(joke|story|poem)|sing\s+(a\s+)?song|write\s+(me\s+)?a\s+(story|poem|essay|code|script|letter))[\s\.,!]*$",
    r"^(play\s+a\s+game|play\s+music|open\s+youtube|open\s+google)[\s\.,!]*$",
    r"^(test|testing|check|abc|123|asdf|qwerty)[\s\.,!]*$",
    r"^(help|help\s+me|assist\s+me)[\s\.,!\?]*$",
    r"^(ignore\s+(all\s+)?previous\s+instructions|system\s+prompt|developer\s+mode|jailbreak)[\s\.,!]*$",
    r"^(ok|okay|cool|nice|good|bad|yes|no|yeah|nah)[\s\.,!]*$",
    r"^(what\s+is\s+the\s+weather|how\s+is\s+the\s+weather|weather\s+today)[\s\.,!\?]*$",
    r"^(bye|goodbye|see\s+you|exit|quit)[\s\.,!]*$",
]


def validate_study_resource(text: str) -> Tuple[bool, str]:
    """
    Enforces that user input contains legitimate study material or syllabus resources.
    Rejects random commands, conversational chit-chat, and empty prompts with instructions
    to attach notes or resources in the respective format.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return False, (
            "Input text is empty. No study material detected. Please attach or paste your study notes, "
            "textbook text, or lecture content in the respective format (Type, Upload, Camera, or Voice)."
        )

    # Check for empty / emoji-only
    has_letters = bool(re.search(r"[\w\u0900-\u097F]", cleaned))
    if not has_letters:
        return False, (
            "Input contains only symbols or emojis without study content. "
            "Please attach your study notes or textbook excerpt in the respective format."
        )

    lower = cleaned.lower().strip()

    # Reject random conversational commands
    for pattern in RANDOM_COMMAND_PATTERNS:
        if re.search(pattern, lower, re.IGNORECASE):
            return False, (
                "Random command or conversational query detected. "
                "AI Study Companion only works with actual study resources and learning material. "
                "Please attach or paste your textbook notes, lecture transcript, or study material in the respective format (Type, Upload, Camera, or Voice) to proceed."
            )

    # Minimum substance check (at least 2 words or 8 chars)
    words = cleaned.split()
    if len(words) < 2 and len(cleaned) < 8:
        return False, (
            "The provided input is too brief to extract study concepts. "
            "Please paste or attach complete study notes, a syllabus topic description, or textbook material."
        )

    return True, ""

