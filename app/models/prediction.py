"""Pydantic models for API request/response validation."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SymptomInput(BaseModel):
    """Request model for symptom-based disease prediction."""
    symptoms: List[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="List of symptom names",
        json_schema_extra={"example": ["headache", "fever", "fatigue"]}
    )


class TopPrediction(BaseModel):
    """Single prediction with disease name and confidence."""
    disease: str
    confidence: float = Field(..., ge=0, le=100)


class PredictionResponse(BaseModel):
    """Response model for a disease prediction."""
    disease: str
    confidence: float = Field(..., ge=0, le=100)
    top_predictions: List[TopPrediction]
    symptoms_used: List[str]
    symptoms_matched: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    disclaimer: str = (
        "⚠️ This prediction is for educational/demo purposes only. "
        "It is NOT medical advice. Please consult a qualified healthcare professional."
    )


class PredictionHistory(BaseModel):
    """Model for a stored prediction record."""
    id: Optional[str] = None
    disease: str
    confidence: float
    symptoms: List[str]
    top_predictions: List[TopPrediction]
    timestamp: datetime


class HistoryResponse(BaseModel):
    """Paginated response for prediction history."""
    predictions: List[PredictionHistory]
    total: int
    page: int
    limit: int
    total_pages: int


class StatsResponse(BaseModel):
    """Aggregate statistics for predictions."""
    total_predictions: int
    top_diseases: List[dict]
    avg_confidence: float
    recent_predictions: int
