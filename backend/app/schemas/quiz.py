from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class QuizGenerateRequest(BaseModel):
    text: Optional[str] = Field(None, description="Study notes")
    document_id: Optional[str] = Field(None, description="Document ID")
    num_questions: int = Field(10, ge=1, le=15, description="Total questions to generate (default 10)")


class QuizQuestion(BaseModel):
    id: int
    type: Literal["mcq", "short"]
    question: str
    options: List[str] = []
    topic: str


class QuizResponse(BaseModel):
    quiz_id: str
    questions: List[QuizQuestion]


class AnswerItem(BaseModel):
    question_id: int
    answer: Optional[str] = ""
    is_correct: Optional[bool] = None


class SubmitAnswersRequest(BaseModel):
    answers: List[AnswerItem]


class QuestionReview(BaseModel):
    id: int
    type: str
    question: str
    student_answer: Optional[str] = ""
    correct_answer: str
    is_correct: bool
    explanation: str
    topic: str


class QuizResultResponse(BaseModel):
    score: int
    total: int
    results: List[QuestionReview]
    weak_topics: List[str]


# Aliases for naming flexibility
QuizRequest = QuizGenerateRequest
QuizQuestionClient = QuizQuestion
SubmitAnswers = SubmitAnswersRequest
QuizResult = QuizResultResponse
