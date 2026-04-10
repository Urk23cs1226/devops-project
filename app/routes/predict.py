"""Prediction API route — accepts symptoms, returns disease prediction."""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.models.prediction import SymptomInput, PredictionResponse
from app.services.ml_service import ml_service
from app.services.db_service import db_service

router = APIRouter(prefix="/api", tags=["Prediction"])


@router.post("/predict", response_model=PredictionResponse)
async def predict_disease(input_data: SymptomInput):
    """
    Predict disease based on user-provided symptoms.

    Accepts a list of symptom names, matches them against known symptoms,
    and returns the top disease predictions with confidence scores.
    """
    try:
        result = ml_service.predict(input_data.symptoms)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    # Save to database (non-blocking, ignore errors)
    try:
        await db_service.save_prediction(result)
    except Exception:
        pass  # Don't fail the request if DB save fails

    return PredictionResponse(
        disease=result["disease"],
        confidence=result["confidence"],
        top_predictions=result["top_predictions"],
        symptoms_used=result["symptoms_used"],
        symptoms_matched=result["symptoms_matched"],
        timestamp=datetime.utcnow(),
    )


@router.get("/symptoms")
async def get_symptoms():
    """Return the full list of known symptoms for frontend auto-suggest."""
    symptoms = ml_service.get_symptom_list()
    # Format for display: replace underscores with spaces, title case
    formatted = [
        {"value": s, "label": s.replace("_", " ").title()}
        for s in symptoms
    ]
    return {"symptoms": formatted, "total": len(formatted)}
