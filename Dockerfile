# ──────────────────────────────────────────────────────────
# Stage 1: Builder — install deps & train ML model
# ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy app source
COPY app/ ./app/

# Train the ML model
RUN python -m app.ml.train_model

# ──────────────────────────────────────────────────────────
# Stage 2: Production — lean runtime image
# ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS production

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY app/ ./app/
COPY frontend/ ./frontend/

# Copy trained model artifacts from builder
COPY --from=builder /build/app/ml/model.joblib ./app/ml/model.joblib
COPY --from=builder /build/app/ml/label_encoder.joblib ./app/ml/label_encoder.joblib
COPY --from=builder /build/app/ml/symptom_list.json ./app/ml/symptom_list.json

# Environment defaults
ENV MONGODB_URI=mongodb://mongodb:27017
ENV DATABASE_NAME=healthcare_db
ENV MODEL_PATH=app/ml/model.joblib
ENV PORT=8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
