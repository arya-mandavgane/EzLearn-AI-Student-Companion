"""
mastery.py — /api/mastery, /api/revision/due, /api/dashboard  (Phase 6/7 stubs)
"""
from fastapi import APIRouter

router = APIRouter(tags=["mastery"])

_COMING_SOON = {"status": "coming_soon", "message": "Mastery tracking will be available in Phase 6."}


@router.get("/mastery")
def get_mastery():
    return _COMING_SOON


@router.get("/revision/due")
def get_revision_due():
    return _COMING_SOON


@router.get("/dashboard")
def get_dashboard():
    return _COMING_SOON
