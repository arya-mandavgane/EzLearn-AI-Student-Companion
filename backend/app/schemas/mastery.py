from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class MasteryItem(BaseModel):
    topic: str
    mastery_level: float  # 0.0 to 1.0
    quizzes_taken: int
    last_reviewed: Optional[datetime] = None
    status: str = "learning"  # "mastered", "learning", "needs_review"


class MasteryResponse(BaseModel):
    topics: List[MasteryItem]
    overall_mastery: float


class RevisionItem(BaseModel):
    id: str
    topic: str
    due_date: datetime
    urgency: str  # "high", "medium", "low"
    suggested_quiz_marks: int = 5


class RevisionResponse(BaseModel):
    due_items: List[RevisionItem]
    total_due: int


class DashboardStats(BaseModel):
    total_study_minutes: int
    concepts_mastered: int
    quizzes_completed: int
    revision_items_due: int


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_topics: List[MasteryItem]
    revisions_due: List[RevisionItem]


# Schema alias for Dashboard
Dashboard = DashboardResponse
