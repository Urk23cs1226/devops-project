"""FastAPI application entry point — HealthGuard AI."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import get_settings
from app.services.ml_service import ml_service
from app.services.db_service import db_service
from app.routes import predict, history


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load ML model & connect DB. Shutdown: disconnect DB."""
    # Startup
    print("\n>> Starting HealthGuard AI...")
    ml_service.load_model()
    await db_service.connect()
    print("[OK] HealthGuard AI is ready!\n")
    yield
    # Shutdown
    await db_service.disconnect()
    print("[--] HealthGuard AI stopped.")


settings = get_settings()

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="AI-powered disease prediction from symptoms",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(predict.router)
app.include_router(history.router)

# Serve frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the main chatbot UI."""
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/dashboard", include_in_schema=False)
async def serve_dashboard():
    """Serve the prediction history dashboard."""
    return FileResponse(os.path.join(frontend_dir, "dashboard.html"))


@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "app": settings.APP_TITLE,
        "version": settings.APP_VERSION,
    }
