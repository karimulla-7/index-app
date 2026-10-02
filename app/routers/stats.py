"""
System status and statistics router for Index.
"""

from fastapi import APIRouter
from app import database, config

router = APIRouter(prefix="/api/system", tags=["system"])

@router.get("/status")
def get_system_status():
    """
    Returns application configuration status and catalog statistics.
    Useful for UI badges and viva presentations.
    """
    stats = database.get_system_stats()
    active_provider = config.get_active_ai_provider()

    return {
        "status": "healthy",
        "app_name": "Index - Archival File Management System",
        "version": "1.0.0",
        "ai": {
            "active_provider": active_provider,
            "has_gemini_key": bool(config.GEMINI_API_KEY),
            "gemini_model": config.GEMINI_MODEL,
            "is_offline_fallback": active_provider == "local_heuristic"
        },
        "stats": stats
    }
