"""History API routes — prediction history and aggregate statistics."""

from fastapi import APIRouter, Query
from app.services.db_service import db_service

router = APIRouter(prefix="/api", tags=["History"])


@router.get("/history")
async def get_history(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str = Query("", description="Search disease name"),
):
    """Return paginated prediction history."""
    return await db_service.get_history(page=page, limit=limit, search=search)


@router.get("/history/stats")
async def get_stats():
    """Return aggregate statistics about all predictions."""
    return await db_service.get_stats()
