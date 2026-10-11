"""
explain.py — /api/explain and /api/explain/{id}/feedback
─────────────────────────────────────────────────────────
Phase 4: Topic Detection, Pedagogical Format Selection & Multi-Language Generation.
Formats:
  1. simulation (launches dynamic interactive simulation)
  2. analogy (everyday real-life physical picture first)
  3. comparison_table (responsive multi-column contrast)
  4. worked_example (step-by-step sequential problem solving)

Supports:
- Format switching via "This didn't help" feedback
- Level selection: simple, normal, exam_ready
- Languages: en, hi, mr, hinglish
- Backward compatibility with Phase 1-3 clients
- AGENTS.md Rule 3: All AI calls strictly via app.ai.provider
"""
import json
import uuid
import hashlib
import logging
from pathlib import Path
from typing import Optional, Any, Dict, List

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ai.provider import generate
from app.schemas.explain import (
    ExplanationRequest, ExplanationResponse,
    ExplanationFeedbackRequest, ExplainRequest, ExplainResponse,
    SectionSchema, KeyTermSchema, TableSchema, WorkedStepSchema,
)
from app.services.text_cleaner import validate_study_resource, clean_text
from app.models.database import get_db
from app.models.models import User, FeedbackRecord
from app.core.security import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter(tags=["explain"])

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "ai" / "prompts"

# Cache for explanations
_explain_cache: Dict[str, Dict[str, Any]] = {}
# Stored explanation records by ID for feedback and format switching
_explanations_by_id: Dict[str, Dict[str, Any]] = {}
# Shared in-memory document store reference
_documents: Dict[str, Any] = {}


def set_document_store(store: dict):
    global _documents
    _documents = store


def _resolve_text(text: Optional[str], document_id: Optional[str]) -> str:
    if document_id:
        if document_id not in _documents:
            raise HTTPException(status_code=404, detail="Document not found. Please upload it again.")
        doc = _documents[document_id]
        return "\n\n".join(f"[Page {p['page']}]\n{p['text']}" for p in doc["pages"])
    elif text and text.strip():
        return text
    raise HTTPException(status_code=422, detail="Provide either 'text' or 'document_id'.")


def _parse_ai_json(raw_text: str, expected_type=dict) -> Any:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 2 and lines[-1].strip() == "```":
            cleaned = "\n".join(lines[1:-1]).strip()
        else:
            cleaned = "\n".join(lines[1:]).strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, expected_type):
            return data
    except Exception:
        pass

    # Substring bracket extraction fallback
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        sub = cleaned[first_brace : last_brace + 1]
        try:
            data = json.loads(sub)
            if isinstance(data, expected_type):
                return data
        except Exception:
            pass

    logger.error("JSON parse error on raw AI response: %s", raw_text[:300])
    raise ValueError("AI response was not valid JSON")


def _classify_topic(text: str) -> Dict[str, Any]:
    """Classify text into simulation | analogy | comparison_table | worked_example."""
    # Fast heuristic checks first
    lower = text.lower()
    if any(k in lower for k in ["stack", "queue", "push", "pop", "enqueue", "dequeue", "fifo", "lifo", "binary search"]):
        sim_id = "stack" if "stack" in lower else ("queue" if "queue" in lower else "process")
        return {"topic": "Data Structures / Algorithms", "subtopic": "Linear Process", "topic_type": "simulation", "simulation_id": sim_id}
    if any(k in lower for k in [" vs ", " versus ", "difference between", "compare", "advantages and disadvantages", "distinguish between"]):
        return {"topic": "Comparison Study", "subtopic": "Key Differences", "topic_type": "comparison_table", "simulation_id": None}
    if any(k in lower for k in ["calculate", "solve for", "derive", "formula", "equation", "step 1", "step 2"]):
        return {"topic": "Problem Solving", "subtopic": "Worked Steps", "topic_type": "worked_example", "simulation_id": None}

    # Use classifier prompt
    try:
        prompt_path = PROMPTS_DIR / "classify.txt"
        template = prompt_path.read_text(encoding="utf-8")
        prompt = template.replace("{text}", text[:1500])
        res = generate(prompt)
        parsed = _parse_ai_json(res, expected_type=dict)
        return parsed
    except Exception as exc:
        logger.warning("Classifier failed (%s), defaulting to analogy.", exc)
        return {"topic": "Concept", "subtopic": "Overview", "topic_type": "analogy", "simulation_id": None}


def _generate_explanation_payload(
    text: str,
    marks: int = 5,
    level: str = "normal",
    language: str = "en",
    format_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates complete structured explanation JSON adhering to section 4 spec."""
    classification = _classify_topic(text)
    topic_type = format_override or classification.get("topic_type", "analogy")
    simulation_id = classification.get("simulation_id")

    # Read explanation prompt template
    prompt_path = PROMPTS_DIR / "explain.txt"
    template = prompt_path.read_text(encoding="utf-8")
    prompt = (
        template.replace("{topic_type}", topic_type)
        .replace("{language}", language)
        .replace("{level}", level)
        .replace("{marks}", str(marks))
        .replace("{text}", text)
    )

    raw_text = generate(prompt)
    if raw_text.startswith("ERROR:"):
        raise HTTPException(status_code=503, detail=raw_text)

    try:
        data = _parse_ai_json(raw_text, expected_type=dict)
    except ValueError:
        # Fallback synthesis
        data = {
            "topic": classification.get("topic", "Study Topic"),
            "subtopic": classification.get("subtopic", "Core Concepts"),
            "topic_type": topic_type,
            "language": language,
            "summary": "Here is a simplified summary based on your study material.",
            "real_life_picture": "Think of this like an everyday real-world system where parts work together seamlessly.",
            "sections": [{"heading": "Key Principles", "body_markdown": text[:600], "citations": []}],
            "key_terms": [{"term": "Key Concept", "meaning": "Fundamental idea from your notes"}],
            "simulation_id": simulation_id,
            "table": None,
            "worked_example_steps": [],
            "exam_answer": f"Definition and structured explanation ({marks} marks).",
            "not_found_in_notes": False,
            "confidence": "medium",
        }

    # Ensure format consistency
    exp_id = str(uuid.uuid4())
    data["id"] = exp_id
    data["topic_type"] = topic_type
    if simulation_id and not data.get("simulation_id"):
        data["simulation_id"] = simulation_id
    if "warnings" not in data:
        data["warnings"] = []

    return data


# ── POST /explain ─────────────────────────────────────────────────────────────

@router.post("/explain")
def generate_explanation(
    req: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Generate rich explanation with dynamic format detection (analogy, simulation, table, worked_example).
    Accepts both legacy ExplainRequest ({text, marks}) and full ExplanationRequest.
    """
    text_input = req.get("text")
    doc_id = req.get("document_id") or req.get("input_id")
    text = _resolve_text(text_input, doc_id)

    is_valid, err_msg = validate_study_resource(text)
    if not is_valid:
        raise HTTPException(status_code=422, detail=err_msg)

    marks = int(req.get("marks", 5))
    level = req.get("level", "normal")
    language = req.get("language", "en")
    format_override = req.get("format_override")

    warnings = []
    if len(text) > settings.max_explain_chars:
        text = text[: settings.max_explain_chars]
        warnings.append(
            f"Notes exceeded {settings.max_explain_chars} characters. Truncated for AI context."
        )

    cache_key = hashlib.sha256(f"{text}|{marks}|{level}|{language}|{format_override}".encode()).hexdigest()
    if cache_key in _explain_cache:
        logger.info("Cache hit for /explain")
        cached = _explain_cache[cache_key].copy()
        cached["warnings"] = warnings + cached.get("warnings", [])
        return cached

    logger.info("Generating explanation | marks=%d | level=%s | lang=%s | format_override=%s", marks, level, language, format_override)
    data = _generate_explanation_payload(
        text=text,
        marks=marks,
        level=level,
        language=language,
        format_override=format_override,
    )
    data["warnings"].extend(warnings)

    # Save to memory and cache
    _explain_cache[cache_key] = data
    _explanations_by_id[data["id"]] = {
        "text": text,
        "marks": marks,
        "level": level,
        "language": language,
        "current_format": data["topic_type"],
        "data": data,
    }

    # Backward compatibility with existing Phase 1-3 frontend:
    # Ensure simple_explanation and exam_answer fields exist
    if "simple_explanation" not in data or not data["simple_explanation"]:
        data["simple_explanation"] = data.get("summary") or "Core summary of your study topic."
    if "exam_answer" not in data or not data["exam_answer"]:
        data["exam_answer"] = f"Key exam points ({marks} marks):\n" + "\n".join(
            f"- {s.get('heading')}: {s.get('body_markdown')}" for s in data.get("sections", [])
        )

    return data


# ── POST /explain/{id}/feedback ───────────────────────────────────────────────

@router.post("/explain/{explanation_id}/feedback", status_code=status.HTTP_202_ACCEPTED)
def explain_feedback(
    explanation_id: str,
    req: ExplanationFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Record feedback on explanation.
    If 'This didn't help' (helpful=False or rating<=2), automatically switches to the NEXT best format.
    """
    logger.info("Feedback received for %s: rating=%s helpful=%s comment=%s",
                explanation_id, req.rating, req.helpful, req.comment)

    # Save feedback to DB
    try:
        fb = FeedbackRecord(
            user_id=current_user.id if current_user else None,
            explanation_id=explanation_id,
            rating=req.rating or (5 if req.helpful else 1),
            comment=f"helpful={req.helpful}; reason={req.reason}; {req.comment or ''}",
        )
        db.add(fb)
        db.commit()
    except Exception as exc:
        logger.warning("Could not persist feedback: %s", exc)

    FORMAT_CYCLE = ["analogy", "comparison_table", "worked_example", "simulation"]

    # Check if student requested next format
    is_unhelpful = (req.helpful is False) or (req.rating is not None and req.rating <= 2)
    new_explanation = None

    if is_unhelpful and req.switch_format and explanation_id in _explanations_by_id:
        record = _explanations_by_id[explanation_id]
        curr = record.get("current_format", "analogy")
        next_format = FORMAT_CYCLE[(FORMAT_CYCLE.index(curr) + 1) % len(FORMAT_CYCLE)] if curr in FORMAT_CYCLE else "analogy"

        logger.info("Switching format for %s from %s to %s", explanation_id, curr, next_format)
        new_data = _generate_explanation_payload(
            text=record["text"],
            marks=record["marks"],
            level=record["level"],
            language=record["language"],
            format_override=next_format,
        )
        record["current_format"] = next_format
        record["data"] = new_data
        _explanations_by_id[new_data["id"]] = record
        new_explanation = new_data

    return {
        "status": "received",
        "message": "Thank you for your feedback!",
        "switched_format": new_explanation.get("topic_type") if new_explanation else None,
        "new_explanation": new_explanation,
    }
