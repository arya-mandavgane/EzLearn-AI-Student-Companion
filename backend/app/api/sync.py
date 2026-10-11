"""
sync.py — /api/sync  (Phase 8 stub)
"""
from fastapi import APIRouter

router = APIRouter(tags=["sync"])


@router.post("/sync")
def sync(body: dict = {}):
    return {
        "status": "coming_soon",
        "message": "Offline sync will be available in Phase 8.",
    }
