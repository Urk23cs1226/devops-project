"""ML model service — loads trained model and performs disease predictions."""

import json
import os
import numpy as np
import joblib
from typing import List, Tuple
from app.config import get_settings
from app.ml.medicine_map import DISEASE_MEDICINE_MAP

class MLService:
    """Handles ML model loading, inference, and symptom matching."""

    def __init__(self):
        self.model = None
        self.label_encoder = None
        self.symptom_list: List[str] = []
        self._loaded = False

    def load_model(self):
        """Load model, label encoder, and symptom list from disk."""
        settings = get_settings()

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        model_path = os.path.join(base_dir, settings.MODEL_PATH)
        encoder_path = os.path.join(base_dir, settings.LABEL_ENCODER_PATH)
        symptom_path = os.path.join(base_dir, settings.SYMPTOM_LIST_PATH)

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at {model_path}. "
                "Run 'python -m app.ml.train_model' first."
            )

        self.model = joblib.load(model_path)
        self.label_encoder = joblib.load(encoder_path)

        with open(symptom_path, "r") as f:
            self.symptom_list = json.load(f)

        self._loaded = True
        print(f"[OK] ML Model loaded: {len(self.symptom_list)} symptoms, "
              f"{len(self.label_encoder.classes_)} diseases")

    def _match_symptoms(self, user_symptoms: List[str]) -> List[str]:
        """
        Match user-input symptom strings to known symptom names.
        Handles fuzzy matching by checking substring containment.
        """
        matched = []
        for user_sym in user_symptoms:
            normalized = user_sym.lower().strip().replace(" ", "_")
            # Exact match first
            if normalized in self.symptom_list:
                matched.append(normalized)
                continue
            # Substring match
            for known_sym in self.symptom_list:
                if normalized in known_sym or known_sym in normalized:
                    matched.append(known_sym)
                    break

        return list(set(matched))

    def predict(self, symptoms: List[str]) -> dict:
        """
        Predict disease from a list of symptom strings.

        Returns dict with disease name, confidence, top 3 predictions,
        matched symptoms, and original symptoms.
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        matched_symptoms = self._match_symptoms(symptoms)

        # Build binary feature vector
        feature_vector = np.zeros(len(self.symptom_list))
        for symptom in matched_symptoms:
            idx = self.symptom_list.index(symptom)
            feature_vector[idx] = 1

        # Predict with probabilities
        probabilities = self.model.predict_proba([feature_vector])[0]
        top_indices = np.argsort(probabilities)[::-1][:5]

        top_predictions = []
        for idx in top_indices:
            disease_name = self.label_encoder.inverse_transform([idx])[0]
            confidence = round(float(probabilities[idx]) * 100, 2)
            top_predictions.append({
                "disease": disease_name,
                "confidence": confidence
            })

        primary = top_predictions[0]
        recommended = DISEASE_MEDICINE_MAP.get(primary["disease"], ["Consult a healthcare professional"])

        return {
            "disease": primary["disease"],
            "confidence": primary["confidence"],
            "top_predictions": top_predictions[:3],
            "symptoms_used": symptoms,
            "symptoms_matched": matched_symptoms,
            "recommended_medicines": recommended,
        }

    def get_symptom_list(self) -> List[str]:
        """Return the list of all known symptoms for frontend auto-suggest."""
        return self.symptom_list


# Singleton instance
ml_service = MLService()
