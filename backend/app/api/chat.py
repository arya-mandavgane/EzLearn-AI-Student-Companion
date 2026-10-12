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
  4. 10-Question Quiz (single attempt lock)
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
        "give", "write", "define", "summary", "notes", "question", "answer", "please"
    }

    q_tokens = {w for w in re.findall(r"\b[a-zA-Z]{3,}\b", prompt.lower()) if w not in _stopwords}
    notes_tokens = {w for w in re.findall(r"\b[a-zA-Z]{3,}\b", combined_notes.lower()) if w not in _stopwords}
    shared_tokens = q_tokens.intersection(notes_tokens)

    # ── STEP 2: SCAN FILE CONTEXT & VERIFY SUBJECT DOMAIN VIA AI ───────────────
    context_scan_prompt = f"""You are a strict academic verifier.
A student uploaded study notes on a specific subject and asked a question.
Your job is to identify the subject domain of the notes, the subject domain of the question, and determine if they match.

STUDENT QUESTION:
{prompt}

ATTACHED STUDY RESOURCES (Study notes uploaded in this chat):
{combined_notes[:7000]}

Rules:
1. Identify "notes_subject": What academic subject are the uploaded notes about? (e.g. "Computer Science - Data Structures", "Operating Systems", "Organic Chemistry", "Macroeconomics").
2. Identify "question_subject": What academic subject is the student's question about? (e.g. "Geography", "European History", "Computer Science", "Cooking", "World Geography").
3. "same_domain": Are the notes subject and question subject within the exact same academic curriculum/field? (true or false). If notes are Computer Science and question is Geography, this MUST be false!
4. "fits_context": Does the student's question belong within the specific syllabus and topics of the uploaded notes? (true or false).

Respond ONLY with valid JSON:
{{
  "notes_subject": "Academic subject of the notes",
  "question_subject": "Academic subject of the question",
  "same_domain": false,
  "fits_context": false,
  "reason": "Clear explanation of why it fits or does NOT fit the notes context"
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
            ai_same_domain = _parse_bool(scan_data.get("same_domain"), default=False)
            ai_fits_context = _parse_bool(scan_data.get("fits_context"), default=False)

            if ai_same_domain and ai_fits_context:
                fits_context = True
            elif ai_fits_context and (len(shared_tokens) > 0 or len(relevant_chunks) > 0):
                fits_context = True
    except Exception as e:
        logger.warning("Error parsing scan json: %s", e)
        fits_context = len(relevant_chunks) > 0 and len(shared_tokens) > 0

    # HARD ENFORCEMENT: If the question shares ZERO meaningful keywords with the notes AND has ZERO relevant chunks, it is 100% an out-of-context outlier topic!
    if len(shared_tokens) == 0 and len(relevant_chunks) == 0:
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
    exp_prompt = f"""You are AI Study Companion. The student asked a question that has been verified to fit within the context of their attached study notes ({domain}).

STUDENT QUESTION: {prompt}

ATTACHED RESOURCES IN THIS CHAT (Exclusive Source of Truth):
{combined_notes[:7000]}

STRICT RULES:
1. Exclusive Source of Truth: Answer SOLELY using the content and concepts in the attached resources above. Do NOT answer from external general knowledge.
2. Everyday real-life picture / physical analogy FIRST.
3. Clear concept summary in 2-3 plain sentences.
4. Structured explanation with key points drawn directly from the attached resources.
5. Technical terms in English with plain definitions found in the notes.

Respond with valid JSON:
{{
  "topic": "Main Topic",
  "is_outlier": false,
  "topic_type": "analogy" | "comparison_table" | "worked_example" | "simulation",
  "real_life_picture": "Everyday physical picture",
  "summary": "Plain 2-3 sentence summary",
  "body": "Detailed explanation synthesized purely from the attached study resources",
  "key_terms": [{{"term": "Term", "meaning": "Meaning"}}]
}}
"""
    raw_exp = generate(exp_prompt)
    try:
        from app.api.explain import _parse_ai_json
        explanation_data = _parse_ai_json(raw_exp, expected_type=dict)
        if not isinstance(explanation_data, dict):
            explanation_data = {}
    except Exception:
        explanation_data = {}

    # Guarantee required fields are present even in mock mode or fallback
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
    sim_prompt = f"""Design a visual single-phase process diagram / interactive demonstration for: '{topic_name}' within the academic context of '{domain}'.
Instead of multi-phase step navigation or paging, design a comprehensive single-phase view showing all its interconnected parts/components clearly.
Return valid JSON:
{{
  "template": "process" | "stack" | "queue" | "sorting",
  "title": "Interactive Process Demonstration: {topic_name}",
  "intro": "1-2 sentences introducing the entire system and how all components operate together in a single unified process.",
  "parts": [
    {{"id": 1, "name": "Part / Component 1", "role": "Specific role or function in this process", "details": "Detailed explanation of how this part operates."}},
    {{"id": 2, "name": "Part / Component 2", "role": "Specific role or function in this process", "details": "Detailed explanation of how this part operates."}},
    {{"id": 3, "name": "Part / Component 3", "role": "Specific role or function in this process", "details": "Detailed explanation of how this part operates."}}
  ],
  "analogy": "Everyday analogy explaining this process."
}}
"""
    raw_sim = generate(sim_prompt)
    simulation_data = None
    try:
        from app.api.explain import _parse_ai_json
        simulation_data = _parse_ai_json(raw_sim, expected_type=dict)
    except Exception:
        simulation_data = {
            "template": "process",
            "title": f"Process Map: {topic_name}",
            "intro": f"Single comprehensive visual view of {topic_name} displaying all its interconnected parts simultaneously.",
            "parts": [
                {"id": 1, "name": "Input / Ingestion", "role": "Receives raw data, signals, or stimulus", "details": "The entry boundary where inputs are captured and validated."},
                {"id": 2, "name": "Core Processing", "role": "Applies rules, algorithms, or transformations", "details": "Processes and computes state changes across the system."},
                {"id": 3, "name": "Output & Resolution", "role": "Delivers formatted results or final state", "details": "The final stage producing actionable outputs and persisting results."}
            ],
            "analogy": "A factory assembly line turning raw inputs into completed products.",
        }

    # 5. Step 4: Generate 10-Question Quiz based on all attached resources
    quiz_res = generate_quiz(QuizGenerateRequest(text=combined_notes[:4000], num_questions=10))
    from app.api.quiz import _quizzes
    backend_quiz = _quizzes.get(quiz_res.quiz_id, {})
    quiz_payload = {
        "quiz_id": quiz_res.quiz_id,
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
    Score the 10-question quiz for this turn.
    Locks the attempt (attempt once; subsequent calls return results).
    Generates AI suggestions regarding topic accuracy, strengths, and must-do topics.
    """
    msg = db.query(MessageRecord).filter(MessageRecord.id == msg_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found.")

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

@router.get("/reports/{timeframe}")
def get_performance_report(
    timeframe: str,  # "daily", "weekly", "monthly"
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Computes user accuracy, weakness, strengths, and must-do topics
    aggregated over Daily, Weekly, or Monthly periods for the signed-in user.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Performance reports are available only for registered and signed-in students.",
        )

    now = datetime.now(timezone.utc)
    if timeframe == "daily":
        start_date = now - timedelta(days=1)
        period_label = "Past 24 Hours"
    elif timeframe == "weekly":
        start_date = now - timedelta(days=7)
        period_label = "Past 7 Days"
    elif timeframe == "monthly":
        start_date = now - timedelta(days=30)
        period_label = "Past 30 Days"
    else:
        raise HTTPException(status_code=400, detail="Invalid timeframe. Use 'daily', 'weekly', or 'monthly'.")

    # Query all messages with quiz attempts within period
    q = db.query(MessageRecord).join(ConversationRecord).filter(
        MessageRecord.created_at >= start_date,
        MessageRecord.quiz_attempt_json.isnot(None),
    )
    if current_user:
        q = q.filter(ConversationRecord.user_id == current_user.id)

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
        if acc >= 75.0 and st["total"] >= 2:
            strengths.append({"topic": t, "accuracy": round(acc, 1), "tested": st["total"]})
        elif acc < 60.0:
            weaknesses.append({"topic": t, "accuracy": round(acc, 1), "tested": st["total"]})
            must_do_topics.append(t)

    # If no tested weaknesses, pick from recent topics
    if not must_do_topics:
        must_do_topics = list(topic_stats.keys())[:3]

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
