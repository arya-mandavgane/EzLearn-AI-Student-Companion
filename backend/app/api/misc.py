"""
misc.py — /api/health and /api/report-error
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings

router = APIRouter(tags=["misc"])


@router.get("/health")
def health_check():
    """Liveness probe. Reports whether AI is in mock mode and current active build version."""
    return {
        "status": "ok",
        "mock_mode": settings.ai_mock or settings.ai_provider == "mock",
        "ai_provider": settings.ai_provider,
        "build_version": "v2.1-grounded-strict",
        "grounding": "dual_schema_outlier_gated",
    }


class ErrorReportRequest(BaseModel):
    explanation_id: Optional[str] = None
    quiz_id: Optional[str] = None
    description: str
    contact_email: Optional[str] = None


@router.post("/report-error", status_code=202)
def report_error(req: ErrorReportRequest):
    """Student reports a wrong or unhelpful result."""
    import logging
    logging.getLogger(__name__).warning(
        "Error report received: explanation_id=%s quiz_id=%s description=%s",
        req.explanation_id, req.quiz_id, req.description[:200],
    )
    return {"status": "received", "message": "Thank you for your feedback. We'll review it shortly."}
