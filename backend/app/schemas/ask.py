from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    chunk_id: str
    page: int
    snippet: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Student's question")
    input_id: Optional[str] = Field(None, description="Optional input/document ID context")
    document_id: Optional[str] = Field(None, description="Legacy document ID alias")
    context_text: Optional[str] = Field(None, description="Optional explicit notes text")
    language: Optional[str] = Field("en", description="Target answer language (en, hi, mr, hinglish)")


class AskResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    confidence: Literal["high", "medium", "low"] = "high"
    not_found_in_notes: bool = False
    general_knowledge_fallback: bool = False
    warnings: List[str] = []
