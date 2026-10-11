from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field


class CitationSchema(BaseModel):
    chunk_id: str
    page: int
    snippet: str


class SectionSchema(BaseModel):
    heading: str
    body_markdown: str
    citations: List[CitationSchema] = []


class KeyTermSchema(BaseModel):
    term: str
    meaning: str


class TableSchema(BaseModel):
    columns: List[str]
    rows: List[List[str]]


class WorkedStepSchema(BaseModel):
    step: str
    explanation: str


class ExplanationResponse(BaseModel):
    id: str
    topic: str
    subtopic: str
    topic_type: Literal["simulation", "analogy", "comparison_table", "worked_example"]
    language: str = "en"
    summary: str
    real_life_picture: str
    sections: List[SectionSchema] = []
    key_terms: List[KeyTermSchema] = []
    simulation_id: Optional[str] = None
    table: Optional[TableSchema] = None
    worked_example_steps: List[WorkedStepSchema] = []
    not_found_in_notes: bool = False
    confidence: Literal["high", "medium", "low"] = "high"
    warnings: List[str] = []


class ExplanationRequest(BaseModel):
    text: Optional[str] = Field(None, min_length=1, description="Study notes")
    document_id: Optional[str] = Field(None, description="Uploaded document ID")
    input_id: Optional[str] = Field(None, description="Input ID alias")
    marks: Optional[Literal[2, 5, 10]] = Field(5, description="Exam marks: 2, 5, or 10")
    level: Optional[Literal["simple", "normal", "exam_ready"]] = Field("normal", description="Explanation depth")
    format_override: Optional[Literal["simulation", "analogy", "comparison_table", "worked_example"]] = Field(
        None, description="Manual format override if student requests or switches"
    )
    language: Optional[str] = Field("en", description="Target explanation language (en, hi, mr, hinglish)")


class ExplanationFeedbackRequest(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description="Star rating from 1 to 5")
    helpful: Optional[bool] = Field(None, description="Whether this explanation was helpful")
    reason: Optional[str] = Field(None, description="Feedback reason")
    comment: Optional[str] = None
    switch_format: Optional[bool] = Field(True, description="Whether to re-generate in next best format if unhelpful")


# Backward-compatible models for Phase 1-3
class ExplainRequest(BaseModel):
    text: Optional[str] = Field(None, min_length=1, description="Student's study notes or topic name")
    document_id: Optional[str] = Field(None, description="ID returned by /upload")
    marks: Literal[2, 5, 10] = Field(..., description="Exam marks: 2, 5, or 10")


class ExplainResponse(BaseModel):
    topic_type: str
    simple_explanation: str
    exam_answer: Union[str, dict]
    warnings: List[str] = []
