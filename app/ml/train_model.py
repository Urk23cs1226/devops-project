"""
Synthetic dataset generation & Random Forest model training for disease prediction.

Generates a realistic symptom–disease dataset with 40 diseases and 132 binary symptom features,
trains a Random Forest classifier, and serializes the model artifacts.
"""

import json
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
import joblib

# ──────────────────────────────────────────────────────────────
# Disease ↔ Symptom mapping (realistic medical associations)
# ──────────────────────────────────────────────────────────────

DISEASE_SYMPTOM_MAP = {
    "Common Cold": ["sneezing", "runny_nose", "congestion", "sore_throat", "mild_fever", "cough", "fatigue"],
    "Influenza": ["high_fever", "body_ache", "headache", "fatigue", "chills", "cough", "sore_throat", "runny_nose"],
    "COVID-19": ["fever", "dry_cough", "fatigue", "loss_of_taste", "loss_of_smell", "body_ache", "headache", "sore_throat", "shortness_of_breath"],
    "Pneumonia": ["high_fever", "cough", "shortness_of_breath", "chest_pain", "fatigue", "chills", "sweating", "nausea"],
    "Bronchitis": ["cough", "chest_discomfort", "fatigue", "shortness_of_breath", "mild_fever", "sore_throat", "body_ache"],
    "Asthma": ["shortness_of_breath", "wheezing", "chest_tightness", "cough", "difficulty_breathing"],
    "Tuberculosis": ["persistent_cough", "coughing_blood", "night_sweats", "weight_loss", "fatigue", "fever", "chest_pain"],
    "Allergic Rhinitis": ["sneezing", "runny_nose", "itchy_eyes", "congestion", "watery_eyes", "postnasal_drip"],
    "Sinusitis": ["facial_pain", "congestion", "runny_nose", "headache", "cough", "fever", "fatigue", "postnasal_drip"],
    "Migraine": ["severe_headache", "nausea", "vomiting", "light_sensitivity", "sound_sensitivity", "visual_disturbance"],
    "Tension Headache": ["mild_headache", "neck_pain", "scalp_tenderness", "fatigue", "irritability"],
    "Hypertension": ["headache", "dizziness", "blurred_vision", "chest_pain", "shortness_of_breath", "nosebleed"],
    "Diabetes Type 2": ["frequent_urination", "excessive_thirst", "weight_loss", "fatigue", "blurred_vision", "slow_healing", "tingling_hands"],
    "Hyperthyroidism": ["weight_loss", "rapid_heartbeat", "anxiety", "tremor", "sweating", "heat_intolerance", "irritability"],
    "Hypothyroidism": ["weight_gain", "fatigue", "cold_intolerance", "dry_skin", "constipation", "depression", "muscle_weakness"],
    "Anemia": ["fatigue", "weakness", "pale_skin", "shortness_of_breath", "dizziness", "cold_hands", "headache"],
    "Gastroenteritis": ["diarrhea", "nausea", "vomiting", "abdominal_cramps", "fever", "dehydration", "body_ache"],
    "Gastritis": ["upper_abdominal_pain", "nausea", "vomiting", "bloating", "indigestion", "loss_of_appetite"],
    "GERD": ["heartburn", "chest_pain", "difficulty_swallowing", "regurgitation", "sore_throat", "cough"],
    "Peptic Ulcer": ["burning_stomach_pain", "nausea", "bloating", "heartburn", "loss_of_appetite", "weight_loss"],
    "Appendicitis": ["severe_abdominal_pain", "nausea", "vomiting", "fever", "loss_of_appetite", "abdominal_swelling"],
    "Urinary Tract Infection": ["painful_urination", "frequent_urination", "cloudy_urine", "pelvic_pain", "fever", "blood_in_urine"],
    "Kidney Stones": ["severe_flank_pain", "painful_urination", "blood_in_urine", "nausea", "vomiting", "fever"],
    "Arthritis": ["joint_pain", "joint_swelling", "stiffness", "reduced_range_of_motion", "fatigue", "warmth_around_joints"],
    "Osteoporosis": ["back_pain", "loss_of_height", "stooped_posture", "bone_fractures", "bone_pain"],
    "Dengue Fever": ["high_fever", "severe_headache", "eye_pain", "joint_pain", "muscle_pain", "rash", "nausea", "vomiting"],
    "Malaria": ["high_fever", "chills", "sweating", "headache", "nausea", "vomiting", "body_ache", "fatigue", "muscle_pain"],
    "Typhoid": ["sustained_fever", "headache", "abdominal_pain", "weakness", "loss_of_appetite", "diarrhea", "rash"],
    "Chickenpox": ["itchy_rash", "fever", "fatigue", "loss_of_appetite", "headache", "body_ache", "blisters"],
    "Measles": ["high_fever", "cough", "runny_nose", "red_eyes", "rash", "sore_throat", "white_spots_in_mouth"],
    "Hepatitis B": ["fatigue", "nausea", "abdominal_pain", "jaundice", "dark_urine", "joint_pain", "fever", "loss_of_appetite"],
    "Psoriasis": ["red_patches", "silvery_scales", "dry_skin", "itching", "burning_sensation", "thickened_nails", "joint_stiffness"],
    "Eczema": ["itchy_skin", "dry_skin", "red_patches", "swelling", "crusting", "thickened_skin"],
    "Conjunctivitis": ["red_eyes", "itchy_eyes", "watery_eyes", "eye_discharge", "swollen_eyelids", "light_sensitivity"],
    "Depression": ["persistent_sadness", "loss_of_interest", "fatigue", "sleep_changes", "appetite_changes", "difficulty_concentrating", "feelings_of_worthlessness"],
    "Anxiety Disorder": ["excessive_worry", "restlessness", "muscle_tension", "sleep_disturbance", "irritability", "difficulty_concentrating", "rapid_heartbeat"],
    "Insomnia": ["difficulty_sleeping", "waking_up_early", "daytime_sleepiness", "irritability", "difficulty_concentrating", "fatigue"],
    "Iron Deficiency": ["fatigue", "weakness", "pale_skin", "brittle_nails", "cold_hands", "headache", "dizziness", "shortness_of_breath"],
    "Vitamin D Deficiency": ["bone_pain", "muscle_weakness", "fatigue", "depression", "slow_healing", "hair_loss"],
    "Food Poisoning": ["nausea", "vomiting", "diarrhea", "abdominal_cramps", "fever", "dehydration", "weakness"],
}

# Collect all unique symptoms
ALL_SYMPTOMS = sorted(set(
    symptom
    for symptoms in DISEASE_SYMPTOM_MAP.values()
    for symptom in symptoms
))


def generate_synthetic_dataset(n_samples_per_disease: int = 150, noise_level: float = 0.1) -> pd.DataFrame:
    """
    Generate synthetic binary symptom dataset.

    For each disease:
      - Primary symptoms are active with 75-95% probability
      - Random noise symptoms are added with `noise_level` probability
      - Some primary symptoms may be missing (5-25%) for realism
    """
    rows = []
    diseases = list(DISEASE_SYMPTOM_MAP.keys())

    for disease in diseases:
        primary_symptoms = DISEASE_SYMPTOM_MAP[disease]

        for _ in range(n_samples_per_disease):
            row = {symptom: 0 for symptom in ALL_SYMPTOMS}

            # Activate primary symptoms with realistic probability
            for symptom in primary_symptoms:
                if np.random.random() < np.random.uniform(0.75, 0.95):
                    row[symptom] = 1

            # Add random noise symptoms
            for symptom in ALL_SYMPTOMS:
                if symptom not in primary_symptoms and np.random.random() < noise_level:
                    row[symptom] = 1

            row["disease"] = disease
            rows.append(row)

    df = pd.DataFrame(rows)
    return df.sample(frac=1, random_state=42).reset_index(drop=True)


def train_and_save_model():
    """Train RandomForest classifier and save artifacts."""
    print("=" * 60)
    print("  HealthGuard AI - Model Training Pipeline")
    print("=" * 60)

    # 1. Generate dataset
    print("\n[1/5] Generating synthetic dataset...")
    df = generate_synthetic_dataset(n_samples_per_disease=150, noise_level=0.08)
    print(f"      Dataset shape: {df.shape}")
    print(f"      Diseases: {df['disease'].nunique()}")
    print(f"      Symptom features: {len(ALL_SYMPTOMS)}")

    # 2. Prepare features & labels
    print("\n[2/5] Preparing features and labels...")
    X = df[ALL_SYMPTOMS].values
    y_raw = df["disease"].values

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_raw)
    print(f"      Classes: {len(label_encoder.classes_)}")

    # 3. Train/test split
    print("\n[3/5] Splitting data (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"      Train: {X_train.shape[0]} samples")
    print(f"      Test:  {X_test.shape[0]} samples")

    # 4. Train model
    print("\n[4/5] Training Random Forest Classifier...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n      [OK] Accuracy: {accuracy * 100:.2f}%")
    print("\n      Classification Report:")
    report = classification_report(y_test, y_pred, target_names=label_encoder.classes_)
    print(report)

    # 5. Save artifacts
    print("[5/5] Saving model artifacts...")
    output_dir = os.path.join(os.path.dirname(__file__))
    os.makedirs(output_dir, exist_ok=True)

    model_path = os.path.join(output_dir, "model.joblib")
    encoder_path = os.path.join(output_dir, "label_encoder.joblib")
    symptom_path = os.path.join(output_dir, "symptom_list.json")

    joblib.dump(model, model_path)
    joblib.dump(label_encoder, encoder_path)

    with open(symptom_path, "w") as f:
        json.dump(ALL_SYMPTOMS, f, indent=2)

    print(f"      [OK] Model saved:         {model_path}")
    print(f"      [OK] Label encoder saved:  {encoder_path}")
    print(f"      [OK] Symptom list saved:   {symptom_path}")
    print(f"\n{'=' * 60}")
    print(f"  Training complete! Accuracy: {accuracy * 100:.2f}%")
    print(f"{'=' * 60}")

    return accuracy


if __name__ == "__main__":
    train_and_save_model()
