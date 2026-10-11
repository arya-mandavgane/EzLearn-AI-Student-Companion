"""
app/main.py
───────────
AI Study Companion — Phase 0 FastAPI application.
All routers mounted under /api prefix.
Backward-compatible root paths (/health, /explain, /upload, etc.) still work
via the legacy main.py; this new app is served on port 8001 during transition.

Run with:
    uvicorn app.main:app --reload --port 8001
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging

from app.api import misc, auth, inputs, explain, ask, quiz, mastery, simulations, sync, chat

# ── Logging ───────────────────────────────────────────────────────────────────
setup_logging()
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Study Companion",
    version="0.1.0",
    description=(
        "Turn any study material into a clear explanation, an interactive simulation, "
        "and a quiz — in the student's own language."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Wire shared in-memory stores between routers ──────────────────────────────
# inputs router owns the store; explain and quiz routers get a reference
from app.api.inputs import get_input_store
from app.api import explain as explain_mod, quiz as quiz_mod

@app.on_event("startup")
async def _wire_stores():
    from app.models.database import init_db
    init_db()
    store = get_input_store()
    explain_mod.set_document_store(store)
    quiz_mod.set_input_store(store)
    logger.info("AI Study Companion started | mock=%s | provider=%s | db=initialized",
                settings.ai_mock, settings.ai_provider)

# ── Routers under /api ────────────────────────────────────────────────────────
app.include_router(misc.router,         prefix="/api")
app.include_router(auth.router,         prefix="/api")
app.include_router(inputs.router,       prefix="/api")
app.include_router(explain.router,      prefix="/api")
app.include_router(ask.router,          prefix="/api")
app.include_router(quiz.router,         prefix="/api")
app.include_router(mastery.router,      prefix="/api")
app.include_router(simulations.router,  prefix="/api")
app.include_router(sync.router,         prefix="/api")
app.include_router(chat.router,         prefix="/api")

# ── Root-level endpoints for backward compatibility with existing clients ──────
from app.api.inputs import legacy_router as inputs_legacy_router
app.include_router(misc.router,         include_in_schema=False)
app.include_router(explain.router,      include_in_schema=False)
app.include_router(ask.router,          include_in_schema=False)
app.include_router(quiz.router,         include_in_schema=False)
app.include_router(simulations.router,  include_in_schema=False)
app.include_router(inputs.router,       include_in_schema=False)
app.include_router(inputs_legacy_router, include_in_schema=False)

# ── Root redirect for convenience ─────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():
    return {"message": "AI Study Companion API", "docs": "/api/docs"}

