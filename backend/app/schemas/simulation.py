from typing import List, Optional, Any
from pydantic import BaseModel, Field


class SimulationCatalogItem(BaseModel):
    id: str
    title: str
    description: str
    keywords: List[str]
    category: Optional[str] = "General"


class SimulationPlanRequest(BaseModel):
    request: str = Field(..., min_length=1, description="Requested simulation topic or keywords")


class SimulationItem(BaseModel):
    label: str
    status: Optional[str] = "active"
    info: Optional[str] = None


class SimulationPrediction(BaseModel):
    question: str
    options: List[str]
    correct_index: int = 0
    explanation: str


class SimulationStep(BaseModel):
    step_number: int
    title: str
    description: str
    items: List[SimulationItem] = []
    rule: Optional[str] = None
    prediction: Optional[SimulationPrediction] = None


class SimulationPlanResponse(BaseModel):
    template: str  # "stack", "queue", or "process"
    title: str
    intro: str
    real_life_analogy: Optional[str] = None
    steps: Optional[List[SimulationStep]] = None
    message: Optional[str] = None
