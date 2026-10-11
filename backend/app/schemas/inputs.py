from typing import List, Optional
from pydantic import BaseModel, Field


class TextInputRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Study notes raw text")
    title: Optional[str] = None


class TextInputResponse(BaseModel):
    input_id: str
    cleaned_text: str
    status: str = "ready"
    language: str = "en"
    warnings: List[str] = []


class FileUploadResponse(BaseModel):
    input_id: str
    status: str = "queued"
    extracted_text: str = ""
    warnings: List[str] = []


class VoiceInputResponse(BaseModel):
    input_id: Optional[str] = None
    transcript: str
    detected_language: str = "en"
    status: str = "ready"
    warnings: List[str] = []


class UrlInputRequest(BaseModel):
    url: str = Field(..., description="URL of video or article")


class UrlInputResponse(BaseModel):
    status: str = "coming_soon"
    message: str = "Video link ingestion is coming soon."


class DocumentPage(BaseModel):
    page: int
    text: str


class JobStatusResponse(BaseModel):
    input_id: str
    status: str = "ready"   # "queued" | "processing" | "ready" | "failed"
    progress: int = 100
    extracted_text: str = ""
    pages: List[DocumentPage] = []
    warnings: List[str] = []


class UpdateTextInput(BaseModel):
    text: str


# Legacy / backward-compatible models
class UploadResponse(BaseModel):
    document_id: str
    source_type: str          # "pdf" or "image"
    pages: List[DocumentPage]
    warnings: List[str]


class UpdateTextRequest(BaseModel):
    pages: List[DocumentPage]
