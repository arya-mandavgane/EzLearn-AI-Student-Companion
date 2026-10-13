"""
chat.py — /api/chat/*
─────────────────────
Complete Chatbot Backend Pipeline:
- Conversations management (list, create, get, delete)
- Per-conversation dynamic resource collection (text, image, audio, files) with OCR & transcription
- Combined dynamic RAG with fallback to web/external references
- Turn-based generation:
  1. What you asked
  2. Explanation (multi-format with everyday analogy)
  3. Demonstration / simulation plan
  4. 5-Question Quiz (single attempt lock)
  5. AI-based performance suggestions upon quiz completion
- Daily / Weekly / Monthly performance reports (accuracy, weaknesses, strengths, must-do topics)
"""
import io
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.models import (
    ConversationRecord, MessageRecord, ChatResourceRecord,
    User, QuizRecord, QuizAttemptRecord, MasteryRecord,
)
from app.core.security import get_current_user_optional
from app.services.text_cleaner import clean_text, detect_language, validate_study_resource
from app.services.chunking import chunk_plain_text, chunk_pages
from app.services.vector_store import global_vector_store
from app.ai.provider import generate, generate_from_image, generate_from_audio, embed
from app.api.quiz import generate_quiz
from app.schemas.quiz import QuizGenerateRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Study Session"


class AddTextResourceRequest(BaseModel):
    text: str = Field(..., min_length=2, description="Pasted study resource text")
    title: Optional[str] = "Pasted Notes"


class SendMessageRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Student's message / question")


class SubmitChatQuizRequest(BaseModel):
    message_id: str
    answers: List[Dict[str, Any]]  # [{"question_id": 1, "answer": "..."}]


# ── Conversation CRUD ─────────────────────────────────────────────────────────

@router.get("/conversations")
def list_conversations(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    List chat history ONLY for registered, signed-in users.
    Guest users receive an empty list (no history access).
    """
    if not current_user:
        return []

    convs = (
        db.query(ConversationRecord)
        .filter(ConversationRecord.user_id == current_user.id)
        .order_by(ConversationRecord.updated_at.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "title": c.title,
            "resource_count": len(c.resources),
            "message_count": len(c.messages),
            "updated_at": c.updated_at.isoformat() if c.updated_at else c.created_at.isoformat(),
        }
        for c in convs
    ]


@router.post("/conversations")
def create_conversation(
    req: Optional[CreateConversationRequest] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Create a new chatbot conversation session."""
    title = (req.title if req and req.title else "New Study Session")
    conv = ConversationRecord(
        id=str(uuid.uuid4()),
        user_id=current_user.id if current_user else None,
        title=title,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {"id": conv.id, "title": conv.title, "created_at": conv.created_at.isoformat()}


@router.get("/conversations/{conv_id}")
def get_conversation(
    conv_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Fetch complete chat conversation with messages and attached resources."""
    conv = db.query(ConversationRecord).filter(ConversationRecord.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    # Data isolation: If conversation belongs to another registered user, block access
    if conv.user_id and current_user and conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied: Not your conversation.")
    if conv.user_id and not current_user:
        raise HTTPException(status_code=403, detail="Please sign in to access this saved conversation.")

    resources = [
        {
            "id": r.id,
            "resource_type": r.resource_type,
            "title": r.title,
            "snippet": (r.content[:160] + "...") if len(r.content) > 160 else r.content,
            "created_at": r.created_at.isoformat() if r.created_at else "",
        }
        for r in conv.resources
    ]

    messages = []
    for m in conv.messages:
        messages.append({
            "id": m.id,
            "role": m.role,
            "user_prompt": m.user_prompt,
            "explanation": json.loads(m.explanation_json) if m.explanation_json else None,
            "simulation": json.loads(m.simulation_json) if m.simulation_json else None,
            "quiz": json.loads(m.quiz_json) if m.quiz_json else None,
            "quiz_attempt": json.loads(m.quiz_attempt_json) if m.quiz_attempt_json else None,
            "ai_suggestions": m.ai_suggestions,
            "citations": json.loads(m.citations_json) if m.citations_json else [],
            "created_at": m.created_at.isoformat() if m.created_at else "",
        })

    return {
        "id": conv.id,
        "title": conv.title,
        "resources": resources,
        "messages": messages,
    }


@router.delete("/conversations/{conv_id}")
def delete_conversation(
    conv_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Delete a conversation and all its messages & resources."""
    conv = db.query(ConversationRecord).filter(ConversationRecord.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if conv.user_id and current_user and conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied: Not your conversation.")
    db.delete(conv)
    db.commit()
    return {"status": "deleted", "id": conv_id}


# ── Resource Ingestion for Specific Conversation ─────────────────────────────

@router.post("/conversations/{conv_id}/resources/text")
def add_text_resource(
    conv_id: str,
    req: AddTextResourceRequest,
    db: Session = Depends(get_db),
):
    """Add typed or pasted study notes to this specific conversation."""
    conv = db.query(ConversationRecord).filter(ConversationRecord.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    cleaned = clean_text(req.text)
    is_valid, err_msg = validate_study_resource(cleaned)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err_msg)

    res_id = str(uuid.uuid4())
    lang = detect_language(cleaned)
    record = ChatResourceRecord(
        id=res_id,
        conversation_id=conv_id,
        resource_type="text",
        title=req.title or "Pasted Notes",
        content=cleaned,
        metadata_json=json.dumps({"language": lang}),
    )
    db.add(record)

    # Auto-update conversation title if it's the first resource
    if conv.title == "New Study Session":
        words = cleaned.split()[:5]
        conv.title = " ".join(words).title() or "Study Session"

    db.commit()

    # Index into vector store for RAG
    chunks = chunk_plain_text(f"{conv_id}-{res_id}", cleaned)
    embs = embed([c.content for c in chunks])
    global_vector_store.add_chunks(chunks, embeddings=embs)

    return {
        "status": "added",
        "resource_id": res_id,
        "title": record.title,
        "resource_type": "text",
        "snippet": cleaned[:160] + "...",
    }


@router.post("/conversations/{conv_id}/resources/upload")
async def add_file_or_media_resource(
    conv_id: str,
    resource_type: str = Form(..., description="'file', 'image', or 'audio'"),
    title: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Add file (PDF), image (Camera or Gallery), or audio (Recorded or Pre-recorded)
    to this conversation. Performs OCR / speech transcription and indexes for RAG.
    """
    conv = db.query(ConversationRecord).filter(ConversationRecord.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload.")

    mime = file.content_type or ""
    extracted_text = ""
    res_type = resource_type.lower()

    if res_type == "image" or mime.startswith("image/"):
        res_type = "image"
        # Vision LLM transcription
        prompt = (
            "Extract and transcribe all educational notes, diagrams, math, or text from this image. "
            "Return clean readable study notes."
        )
        extracted_text = generate_from_image(data, mime or "image/jpeg", prompt)

    elif res_type == "audio" or mime.startswith("audio/"):
        res_type = "audio"
        # Audio transcription
        extracted_text = generate_from_audio(data, mime or "audio/webm")

    elif mime == "application/pdf" or file.filename.endswith(".pdf"):
        res_type = "file"
        # PyMuPDF extraction
        try:
            import pymupdf
            doc = pymupdf.open(stream=data, filetype="pdf")
            pages_txt = []
            for p_idx, page in enumerate(doc):
                txt = page.get_text().strip()
                if txt:
                    pages_txt.append(f"[Page {p_idx+1}]\n{txt}")
            extracted_text = "\n\n".join(pages_txt)
        except Exception as exc:
            logger.warning("PDF extraction failed: %s", exc)
            extracted_text = ""

    else:
        # Fallback text decoding
        try:
            extracted_text = data.decode("utf-8", errors="ignore")
        except Exception:
            extracted_text = ""

    cleaned = clean_text(extracted_text)
    if not cleaned:
        cleaned = f"Extracted study material from {file.filename or 'attached resource'}."

    res_id = str(uuid.uuid4())
    record = ChatResourceRecord(
        id=res_id,
        conversation_id=conv_id,
        resource_type=res_type,
        title=title or file.filename or f"{res_type.capitalize()} Resource",
        content=cleaned,
        metadata_json=json.dumps({"filename": file.filename, "size": len(data)}),
    )
    db.add(record)

    if conv.title == "New Study Session":
        conv.title = (file.filename or f"{res_type.capitalize()} Notes").replace(".pdf", "")

    db.commit()

    # Index into vector store for RAG
    chunks = chunk_plain_text(f"{conv_id}-{res_id}", cleaned)
    embs = embed([c.content for c in chunks])
    global_vector_store.add_chunks(chunks, embeddings=embs)

    return {
        "status": "added",
        "resource_id": res_id,
        "title": record.title,
        "resource_type": res_type,
        "snippet": cleaned[:160] + "...",
    }


# ── Chat & Response Generation ───────────────────────────────────────────────

@router.post("/conversations/{conv_id}/messages")
def send_chat_message(
    conv_id: str,
    req: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Send a prompt to the chatbot.
    Enforces Rule: Resources MUST be attached to this conversation.
    Generates required format:
      1. What you asked
      2. Explanation (multi-format with real-world picture)
      3. Demonstration / simulation
      4. 10-Question Quiz
    """
    conv = db.query(ConversationRecord).filter(ConversationRecord.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    # 1. Enforce: User cannot chat without adding resources to THIS specific conversation
    if not conv.resources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No study resources attached to this current chat. Resources uploaded in other chats do not apply. Please click the '+' button to add text notes, images, PDFs, or audio to this chat before typing questions.",
        )

    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    # Aggregate ALL resources attached to THIS specific conversation
    combined_notes = "\n\n---\n\n".join(
        f"[{r.resource_type.upper()} RESOURCE: {r.title}]\n{r.content}" for r in conv.resources
    )

    # 2. RAG retrieval strictly over THIS conversation's indexed chunks (never leak other chats)
    this_conv_prefix = f"{conv_id}-"
    q_vec = embed([prompt])[0] if embed([prompt]) else None
    search_res = global_vector_store.search(query=prompt, query_embedding=q_vec, top_k=12)
    conv_chunks = [
        (c, score) for c, score in search_res
        if (c.chunk_id.startswith(this_conv_prefix) or (c.input_id and c.input_id.startswith(this_conv_prefix)))
    ]
    relevant_chunks = [c for c, score in conv_chunks if score >= 0.28]

    citations = [
        {"page": c.page, "snippet": c.snippet, "chunk_id": c.chunk_id} for c in relevant_chunks
    ]

    # ── STEP 1: DETERMINISTIC LEXICAL & SEMANTIC OVERLAP CHECK ─────────────────
    import re
    _stopwords = {
        "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "can", "could", "should", "would",
        "may", "might", "must", "shall", "will", "and", "or", "but", "if", "because",
        "as", "until", "while", "of", "at", "by", "for", "with", "about", "against",
        "between", "into", "through", "during", "before", "after", "above", "below",
        "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "all", "any", "both", "each",
        "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only",
        "own", "same", "so", "than", "too", "very", "explain", "tell", "describe",
        "give", "write", "define", "summary", "notes", "question", "answer", "please",
        "show", "state", "find", "calculate", "list", "name", "help", "solve", "detail",
        "provide", "information", "info", "discuss", "view", "know", "check", "need",
        "simple", "terms", "words", "understand", "short", "long", "easy", "basic",
        "main", "first", "second", "best", "different", "used", "use", "using", "make",
        "like", "good", "right", "way", "point", "well", "also", "mean", "meaning",
        # Generic academic terms that appear in all disciplines
        "formula", "theorem", "theory", "law", "rule", "definition", "concept",
        "principle", "problem", "solution", "example", "method", "system", "type",
        "types", "process", "approach", "model", "step", "steps", "meaning", "name",
    }

    q_tokens = {w for w in re.findall(r"\b[a-zA-Z]{3,}\b", prompt.lower()) if w not in _stopwords}
    notes_tokens = {w for w in re.findall(r"\b[a-zA-Z]{3,}\b", combined_notes.lower()) if w not in _stopwords}
    shared_tokens = q_tokens.intersection(notes_tokens)

    # ── STEP 2: VERIFY TOPIC IS ACTUALLY IN NOTES VIA STRICT AI ────────────────
    context_scan_prompt = f"""You are a strict academic verification auditor.
A student uploaded study notes on a specific topic and asked a question.
Your job is to determine whether the student's question is about a concept that is ACTUALLY PRESENT OR TAUGHT in the uploaded notes.

STUDENT QUESTION:
{prompt}

STUDENT'S UPLOADED STUDY NOTES:
{combined_notes[:7000]}

STRICT RULES:
1. "notes_subject": State the exact academic subject of the uploaded notes (e.g. "Computer Science - Data Structures", "Operating Systems", etc.).
2. "question_subject": State the exact academic subject of the student question (e.g. "Geometry - Pythagoras Theorem", "World Geography", "Biology", etc.).
3. "is_covered_in_notes": Answer true ONLY if the topic of the question ('{prompt}') is directly discussed, defined, or taught in the uploaded notes above.
4. If the notes are about Computer Science and the question is about Geometry/Math (like Pythagoras theorem), Geography, Literature, etc., "is_covered_in_notes" MUST BE FALSE.
5. If the question cannot be answered using the concepts in the uploaded notes, "is_covered_in_notes" MUST BE FALSE.

Respond ONLY with valid JSON:
{{
  "notes_subject": "Academic subject of the notes",
  "question_subject": "Academic subject of the question",
  "is_covered_in_notes": false,
  "reason": "Why this is or is not covered in the notes"
}}
"""
    raw_scan = generate(context_scan_prompt)

    def _parse_bool(val, default=False) -> bool:
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            v = val.strip().lower()
            if v in ("true", "1", "yes"):
                return True
            if v in ("false", "0", "no"):
                return False
        return default

    fits_context = False
    notes_domain = "Uploaded study notes"
    q_domain = "Asked topic"

    try:
        from app.api.explain import _parse_ai_json
        scan_data = _parse_ai_json(raw_scan, expected_type=dict)
        if isinstance(scan_data, dict):
            notes_domain = scan_data.get("notes_subject") or notes_domain
            q_domain = scan_data.get("question_subject") or q_domain
            is_covered = _parse_bool(scan_data.get("is_covered_in_notes"), default=False)

            if is_covered:
                fits_context = True
    except Exception as e:
        logger.warning("Error parsing scan json: %s", e)
        fits_context = False

    # HARD ENFORCEMENT: If the question shares ZERO meaningful topic keywords with the notes, it CANNOT be answered from the notes!
    if len(q_tokens) > 0 and len(shared_tokens) == 0:
        fits_context = False

    # ── CASE A: QUESTION DOES NOT FIT IN FILE CONTEXT ─────────────────────────
    # Questions that do not fit in the context of the file MUST NOT be answered.
    # Refuse strictly: no explanation body, no simulation, no quiz.
    if not fits_context:
        notice = (
            f"I cannot answer this question because it is outside the scope of your uploaded notes. "
            f"Your uploaded notes are about '{notes_domain}', while your question is about '{q_domain}'. "
            "EzLearn answers questions strictly based on your uploaded study materials. "
            "Please ask a question related to your uploaded notes or attach resources covering this topic."
        )

        explanation_data = {
            "topic": prompt,
            "is_outlier": True,
            "outlier_notice": notice,
            "file_context": notes_domain,
            "body": None,
            "summary": None,
            "real_life_picture": None,
            "key_terms": [],
        }

        # Save record with NO simulation and NO quiz
        msg_id = str(uuid.uuid4())
        msg = MessageRecord(
            id=msg_id,
            conversation_id=conv_id,
            role="assistant",
            user_prompt=prompt,
            explanation_json=json.dumps(explanation_data),
            simulation_json=None,
            quiz_json=None,
            citations_json=json.dumps([]),
            ai_suggestions=None,
        )
        db.add(msg)
        conv.updated_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "message_id": msg_id,
            "user_prompt": prompt,
            "explanation": explanation_data,
            "simulation": None,
            "quiz": None,
            "citations": [],
            "is_outlier": True,
        }

    # ── CASE B: QUESTION FITS FILE CONTEXT ─────────────────────────────────────
    # Synthesize across attached resources in this conversation.
    # Answers must be based purely on the attached study materials without external web knowledge.
    domain = notes_domain

    # 3. Step 2: Generate Explanation strictly grounded in the attached materials
    exp_prompt = f"""You are AI Study Companion. A student uploaded study notes on {domain} and asked a question.

STUDENT QUESTION:
{prompt}

STUDENT'S UPLOADED STUDY NOTES (Your ONLY allowed source of information):
{combined_notes[:7000]}

STRICT GROUNDING DIRECTIVE:
You are an extractive and synthesized grounding engine. You are STRICTLY FORBIDDEN from using any pre-trained external knowledge.
1. Scan the STUDENT'S UPLOADED STUDY NOTES above.
2. Does the uploaded text explicitly define, explain, or answer the student's question ('{prompt}')?
   - If NO (the concept or question is outside the uploaded notes, such as asking about geometry/theorems/formulas/topics not mentioned in the text):
     You MUST return EXACTLY this JSON:
     {{
       "topic": "{prompt}",
       "is_outlier": true,
       "body": null,
       "summary": null,
       "real_life_picture": null,
       "key_terms": []
     }}
   - If YES (the concept is explicitly covered in the text):
     Return the explanation strictly synthesized from the text:
     {{
       "topic": "Specific Topic from Notes",
       "is_outlier": false,
       "topic_type": "analogy",
       "real_life_picture": "Analogy based on notes",
       "summary": "Summary based strictly on notes",
       "body": "Detailed explanation based strictly on the uploaded study notes",
       "key_terms": [{{"term": "Term", "meaning": "Meaning"}}]
     }}

Respond ONLY with valid JSON.
"""
    raw_exp = generate(exp_prompt)
    try:
        from app.api.explain import _parse_ai_json
        explanation_data = _parse_ai_json(raw_exp, expected_type=dict)
        if not isinstance(explanation_data, dict):
            explanation_data = {}
    except Exception:
        explanation_data = {}

    # If the model itself reported this topic as an outlier or missing from the notes, reject strictly!
    if explanation_data.get("is_outlier") is True or not explanation_data.get("body"):
        notice = (
            f"I cannot answer this question because it is outside the scope of your uploaded notes. "
            f"Your uploaded notes are about '{notes_domain}', while your question is about '{q_domain}'. "
            "EzLearn answers questions strictly based on your uploaded study materials. "
            "Please ask a question related to your uploaded notes or attach resources covering this topic."
        )
        explanation_data = {
            "topic": prompt,
            "is_outlier": True,
            "outlier_notice": notice,
            "file_context": notes_domain,
            "body": None,
            "summary": None,
            "real_life_picture": None,
            "key_terms": [],
        }
        msg_id = str(uuid.uuid4())
        msg = MessageRecord(
            id=msg_id,
            conversation_id=conv_id,
            role="assistant",
            user_prompt=prompt,
            explanation_json=json.dumps(explanation_data),
            simulation_json=None,
            quiz_json=None,
            citations_json=json.dumps([]),
            ai_suggestions=None,
        )
        db.add(msg)
        conv.updated_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "message_id": msg_id,
            "user_prompt": prompt,
            "explanation": explanation_data,
            "simulation": None,
            "quiz": None,
            "citations": [],
            "is_outlier": True,
        }

    explanation_data["is_outlier"] = False
    if "real_life_picture" not in explanation_data:
        explanation_data["real_life_picture"] = (
            explanation_data.get("simple_explanation")
            or "Think of this like an everyday real-world system where parts work together."
        )
    if "summary" not in explanation_data:
        explanation_data["summary"] = (
            explanation_data.get("simple_explanation")
            or "Here is the explanation synthesized from your attached notes."
        )
    if "body" not in explanation_data:
        explanation_data["body"] = (
            explanation_data.get("exam_answer")
            or combined_notes[:500]
        )
    if "topic" not in explanation_data:
        explanation_data["topic"] = prompt
    if "topic_type" not in explanation_data:
        explanation_data["topic_type"] = "analogy"
    if "key_terms" not in explanation_data:
        explanation_data["key_terms"] = []

    # 4. Step 3: Demonstration / Simulation Plan (Single unified view showing all parts)
    topic_name = explanation_data.get("topic") or prompt
    summary_text = explanation_data.get("summary") or ""
    analogy_text = explanation_data.get("analogy") or ""

    sim_prompt = f"""You are an expert educational visualizer.
The student asked: "{prompt}"
The system explained the topic: "{topic_name}" (Domain: {domain}).
Summary of explanation: "{summary_text}"

Design an interactive, concept-specific process diagram / demonstration directly modeling: "{topic_name}".
The simulation components and steps must precisely reflect the actual mechanism, stages, or architecture of what was asked and explained above.
Do NOT output generic placeholders, and do NOT use unrelated templates like Stack or Queue unless the concept itself is literally a Stack or Queue.

Return a valid JSON object strictly matching this schema:
{{
  "template": "process",
  "title": "{topic_name} Process Demonstration",
  "intro": "2 sentences explaining how this specific process or concept operates from start to finish.",
  "analogy": "{analogy_text or 'Everyday real-world intuition for this concept'}",
  "parts": [
    {{"id": 1, "name": "Exact Name of Phase / Step / Component 1", "role": "Specific role in {topic_name}", "details": "Detailed explanation of what occurs in this phase."}},
    {{"id": 2, "name": "Exact Name of Phase / Step / Component 2", "role": "Specific role in {topic_name}", "details": "Detailed explanation of what occurs in this phase."}},
    {{"id": 3, "name": "Exact Name of Phase / Step / Component 3", "role": "Specific role in {topic_name}", "details": "Detailed explanation of what occurs in this phase."}}
  ],
  "prediction": {{
    "question": "Concept check question testing understanding of this process",
    "options": ["Correct choice", "Incorrect choice 1", "Incorrect choice 2"],
    "correct_index": 0,
    "explanation": "Why this option is correct based on the process."
  }}
}}
Return ONLY valid JSON (no markdown, no extra commentary)."""

    raw_sim = generate(sim_prompt)
    simulation_data = None
    try:
        from app.api.explain import _parse_ai_json
        simulation_data = _parse_ai_json(raw_sim, expected_type=dict)
        # Ensure template is 'process' so it never falls into stack/queue plates or lines
        if isinstance(simulation_data, dict):
            simulation_data["template"] = "process"
    except Exception:
        simulation_data = {
            "template": "process",
            "title": f"{topic_name} Process Demonstration",
            "intro": f"Interactive structural demonstration of {topic_name} showing how its key components operate in sequence.",
            "parts": [
                {"id": 1, "name": f"{topic_name} Initiation", "role": "Input criteria and initial conditions", "details": f"Sets up the requirements and starting parameters for {topic_name}."},
                {"id": 2, "name": f"{topic_name} Execution", "role": "Core transformation and processing", "details": f"Applies the fundamental principles and logic of {topic_name}."},
                {"id": 3, "name": f"{topic_name} Verification", "role": "Validation and state resolution", "details": f"Confirms constraints, outputs, and terminal criteria of {topic_name}."}
            ],
            "analogy": analogy_text or f"A structured workflow coordinating all elements of {topic_name}.",
        }

    # 5. Step 4: Generate 5-Question Quiz focused specifically on the student's asked topic/query
    quiz_topic = explanation_data.get("topic") or prompt
    # Prioritize topic-relevant retrieved chunks, combined with notes context
    chunk_context = "\n\n".join(f"[EXCERPT - Page {c.page}]:\n{c.snippet or c.content}" for c in relevant_chunks[:6]) if relevant_chunks else ""
    quiz_context = f"{chunk_context}\n\n---\n\n{combined_notes[:4000]}" if chunk_context else combined_notes[:4000]

    quiz_res = generate_quiz(QuizGenerateRequest(
        text=quiz_context,
        num_questions=5,
        topic=quiz_topic,
    ))
    from app.api.quiz import _quizzes
    backend_quiz = _quizzes.get(quiz_res.quiz_id, {})
    quiz_payload = {
        "quiz_id": quiz_res.quiz_id,
        "topic": quiz_topic,
        "questions": [q.model_dump() for q in quiz_res.questions],
        "stored_questions": backend_quiz.get("questions", []),
    }

    # Record message in DB
    msg_id = str(uuid.uuid4())
    msg = MessageRecord(
        id=msg_id,
        conversation_id=conv_id,
        role="assistant",
        user_prompt=prompt,
        explanation_json=json.dumps(explanation_data),
        simulation_json=json.dumps(simulation_data),
        quiz_json=json.dumps(quiz_payload),
        citations_json=json.dumps(citations),
        ai_suggestions=None,
    )
    db.add(msg)
    conv.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "message_id": msg_id,
        "user_prompt": prompt,
        "explanation": explanation_data,
        "simulation": simulation_data,
        "quiz": quiz_payload,
        "citations": citations,
    }


# ── Step 5: Quiz Submission, Attempt Lock & AI Suggestions ───────────────────

@router.post("/conversations/{conv_id}/messages/{msg_id}/submit-quiz")
def submit_chat_quiz(
    conv_id: str,
    msg_id: str,
    req: SubmitChatQuizRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Score the 5-question quiz for this turn.
    Locks the attempt (attempt once; subsequent calls return results).
    Generates AI suggestions regarding topic accuracy, strengths, and must-do topics.
    """
    msg = db.query(MessageRecord).filter(MessageRecord.id == msg_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found.")

    # Link conversation to user if signed in
    if current_user:
        conv = db.query(ConversationRecord).filter(ConversationRecord.id == conv_id).first()
        if conv and not conv.user_id:
            conv.user_id = current_user.id
            db.commit()

    # Check if already attempted (Attempt Once constraint)
    if msg.quiz_attempt_json:
        return {
            "already_attempted": True,
            "quiz_attempt": json.loads(msg.quiz_attempt_json),
            "ai_suggestions": msg.ai_suggestions,
        }

    quiz_data = json.loads(msg.quiz_json) if msg.quiz_json else {}
    stored_questions = quiz_data.get("stored_questions", [])
    if not stored_questions:
        raise HTTPException(status_code=400, detail="Quiz questions unavailable.")

    # Score answers in code
    user_answers_map = {a.get("question_id"): str(a.get("answer", "")).strip() for a in req.answers}
    score = 0
    total = len(stored_questions)
    results_review = []
    weak_topics = []

    for q in stored_questions:
        q_id = q["id"]
        correct = str(q.get("correct_answer", "")).strip()
        user_ans = user_answers_map.get(q_id, "")
        is_corr = (user_ans.lower() == correct.lower())
        if is_corr:
            score += 1
        else:
            weak_topics.append(q.get("topic", "General"))

        results_review.append({
            "id": q_id,
            "type": q.get("type", "mcq"),
            "question": q.get("question", ""),
            "student_answer": user_ans,
            "correct_answer": correct,
            "is_correct": is_corr,
            "explanation": q.get("explanation", ""),
            "topic": q.get("topic", ""),
        })

    weak_topics_unique = list(dict.fromkeys(weak_topics))
    accuracy_pct = round((score / max(total, 1)) * 100, 1)

    # Generate AI Suggestions based on performance
    topic_context = json.loads(msg.explanation_json).get("topic", "the concept") if msg.explanation_json else "this concept"
    sug_prompt = f"""The student scored {score}/{total} ({accuracy_pct}%) on a quiz about '{topic_context}'.
Weak areas identified: {', '.join(weak_topics_unique) if weak_topics_unique else 'None! Perfect mastery'}.
Give 2-3 concise, encouraging AI pedagogical suggestions:
1) Performance assessment (strengths and gaps)
2) Specific must-do revision topics
3) A question asking for their thoughts or what part felt confusing.
"""
    ai_suggestions = generate(sug_prompt)
    if ai_suggestions.startswith("ERROR:"):
        ai_suggestions = f"Great effort! You scored {score}/{total}. Review {', '.join(weak_topics_unique[:2])} for full mastery."

    attempt_payload = {
        "score": score,
        "total": total,
        "accuracy_pct": accuracy_pct,
        "weak_topics": weak_topics_unique,
        "results": results_review,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }

    # Save to message record
    msg.quiz_attempt_json = json.dumps(attempt_payload)
    msg.ai_suggestions = ai_suggestions

    # Update global mastery / revision records for user
    if current_user:
        try:
            m_rec = db.query(MasteryRecord).filter(
                MasteryRecord.user_id == current_user.id,
                MasteryRecord.topic == topic_context,
            ).first()
            if not m_rec:
                m_rec = MasteryRecord(user_id=current_user.id, topic=topic_context, score=accuracy_pct / 100.0)
                db.add(m_rec)
            else:
                m_rec.score = round((m_rec.score + (accuracy_pct / 100.0)) / 2, 2)
                m_rec.last_tested_at = datetime.now(timezone.utc)
        except Exception as exc:
            logger.warning("Could not update mastery: %s", exc)

    db.commit()

    return {
        "already_attempted": False,
        "quiz_attempt": attempt_payload,
        "ai_suggestions": ai_suggestions,
    }


# ── Analytics: Daily / Weekly / Monthly Reports ───────────────────────────────
from sqlalchemy import or_

@router.get("/reports/{timeframe}")
def get_performance_report(
    timeframe: str,  # "daily", "weekly", "monthly"
    conv_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Computes user accuracy, weakness, strengths, and must-do topics
    aggregated over Daily, Weekly, or Monthly periods for the signed-in user or active session.
    """
    now = datetime.now(timezone.utc)
    now_naive = now.replace(tzinfo=None)
    if timeframe == "daily":
        start_date = now - timedelta(days=1)
        start_date_naive = now_naive - timedelta(days=1)
        period_label = "Past 24 Hours"
    elif timeframe == "weekly":
        start_date = now - timedelta(days=7)
        start_date_naive = now_naive - timedelta(days=7)
        period_label = "Past 7 Days"
    elif timeframe == "monthly":
        start_date = now - timedelta(days=30)
        start_date_naive = now_naive - timedelta(days=30)
        period_label = "Past 30 Days"
    else:
        raise HTTPException(status_code=400, detail="Invalid timeframe. Use 'daily', 'weekly', or 'monthly'.")

    # In SQLite, MessageRecord.created_at might be naive. Match either aware or naive UTC.
    date_filter = or_(
        MessageRecord.created_at >= start_date,
        MessageRecord.created_at >= start_date_naive,
    )

    q = db.query(MessageRecord).join(ConversationRecord).filter(
        date_filter,
        MessageRecord.quiz_attempt_json.isnot(None),
    )

    if current_user:
        # If user is logged in, link active conv if unlinked and query user's conversations
        if conv_id:
            active_c = db.query(ConversationRecord).filter(ConversationRecord.id == conv_id).first()
            if active_c and not active_c.user_id:
                active_c.user_id = current_user.id
                db.commit()
            q = q.filter(or_(ConversationRecord.user_id == current_user.id, ConversationRecord.id == conv_id))
        else:
            q = q.filter(ConversationRecord.user_id == current_user.id)
    elif conv_id:
        # Guest user querying their current study session conversation
        q = q.filter(ConversationRecord.id == conv_id)
    else:
        # Guest fallback: recent guest conversations
        q = q.filter(ConversationRecord.user_id.is_(None))

    messages = q.all()

    total_quizzes = len(messages)
    total_score = 0
    total_questions = 0
    topic_stats: Dict[str, Dict[str, int]] = {}  # topic -> {"correct": int, "total": int}

    for m in messages:
        try:
            att = json.loads(m.quiz_attempt_json)
            total_score += att.get("score", 0)
            total_questions += att.get("total", 0)
            for r in att.get("results", []):
                t = r.get("topic") or "General"
                if t not in topic_stats:
                    topic_stats[t] = {"correct": 0, "total": 0}
                topic_stats[t]["total"] += 1
                if r.get("is_correct"):
                    topic_stats[t]["correct"] += 1
        except Exception:
            pass

    overall_accuracy = round((total_score / max(total_questions, 1)) * 100, 1) if total_questions > 0 else 0.0

    # Categorize Strengths, Weaknesses & Must-do topics
    strengths = []
    weaknesses = []
    must_do_topics = []

    for t, st in topic_stats.items():
        acc = (st["correct"] / max(st["total"], 1)) * 100
        if acc >= 70.0 and st["total"] >= 1:
            strengths.append({"topic": t, "accuracy": round(acc, 1), "tested": st["total"]})
        else:
            weaknesses.append({"topic": t, "accuracy": round(acc, 1), "tested": st["total"]})
            must_do_topics.append(t)

    # If all tested topics scored high, suggest the ones with lower relative accuracy
    if not must_do_topics:
        sorted_strengths = sorted(strengths, key=lambda x: x["accuracy"])
        must_do_topics = [s["topic"] for s in sorted_strengths][:2]
        if not must_do_topics:
            must_do_topics = list(topic_stats.keys())[:2]

    return {
        "timeframe": timeframe,
        "period_label": period_label,
        "quizzes_completed": total_quizzes,
        "total_questions_answered": total_questions,
        "overall_accuracy_pct": overall_accuracy,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "must_do_topics": must_do_topics,
    }
