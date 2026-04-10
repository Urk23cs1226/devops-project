"""Prediction API route — accepts symptoms, returns disease prediction."""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from app.models.prediction import SymptomInput, PredictionResponse
from app.services.ml_service import ml_service
from app.services.db_service import db_service
from deep_translator import GoogleTranslator

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

    lang = input_data.language
    if lang != 'en':
        try:
            translator = GoogleTranslator(source='auto', target=lang)
            result["disease"] = translator.translate(result["disease"])
            for tp in result["top_predictions"]:
                tp["disease"] = translator.translate(tp["disease"])
            result["symptoms_matched"] = translator.translate_batch(result["symptoms_matched"]) if result["symptoms_matched"] else []
            result["recommended_medicines"] = translator.translate_batch(result["recommended_medicines"]) if result["recommended_medicines"] else []
        except Exception as e:
            print(f"Translation failed: {e}")

    # Default disclaimer
    disclaimer = (
        "⚠️ This prediction is for educational/demo purposes only. "
        "It is NOT medical advice. Please consult a qualified healthcare professional."
    )
    if lang != 'en':
        try:
            disclaimer = GoogleTranslator(source='auto', target=lang).translate(disclaimer)
        except:
            pass

    return PredictionResponse(
        disease=result["disease"],
        confidence=result["confidence"],
        top_predictions=result["top_predictions"],
        symptoms_used=result["symptoms_used"],
        symptoms_matched=result["symptoms_matched"],
        recommended_medicines=result.get("recommended_medicines", []),
        timestamp=datetime.utcnow(),
        disclaimer=disclaimer
    )


@router.get("/symptoms")
async def get_symptoms(language: str = Query("en")):
    """Return the full list of known symptoms for frontend auto-suggest, with translation."""
    symptoms = ml_service.get_symptom_list()
    
    # Format labels
    labels = [s.replace("_", " ").title() for s in symptoms]
    
    if language != 'en':
        try:
            translator = GoogleTranslator(source='en', target=language)
            # Batch translate in chunks of 50 to avoid timeout
            translated_labels = []
            chunk_size = 50
            for i in range(0, len(labels), chunk_size):
                chunk = labels[i:i + chunk_size]
                translated_labels.extend(translator.translate_batch(chunk))
            labels = [tl if tl else ol for tl, ol in zip(translated_labels, labels)]
        except Exception as e:
            print(f"Symptom translation failed: {e}")

    formatted = [
        {"value": s, "label": l}
        for s, l in zip(symptoms, labels)
    ]
    return {"symptoms": formatted, "total": len(formatted)}
