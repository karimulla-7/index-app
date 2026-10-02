"""
Search Router for Index.
Provides AI-powered Natural Language Search ("Ask" mode).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from app import database, ai_service

router = APIRouter(prefix="/api/search", tags=["search"])

class AskSearchRequest(BaseModel):
    query: str

@router.post("/ask")
async def ask_search(payload: AskSearchRequest):
    """
    Natural Language Search ("Ask" mode).
    Takes questions or semantic descriptions e.g. "budget spreadsheets from last month"
    or "notes on system architecture", queries the AI retrieval service, and returns
    the matched files ranked with an explanatory synthesis.
    """
    clean_query = payload.query.strip()
    if not clean_query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    # Fetch catalog of all files
    all_files = database.get_all_files(sort_by="newest")
    if not all_files:
        return {
            "query": clean_query,
            "matched_file_ids": [],
            "files": [],
            "explanation": "The catalog is currently empty. Upload files to begin searching.",
            "provider": "none"
        }

    # Pass to AI retrieval service
    ai_result = await ai_service.natural_language_search(clean_query, all_files)
    matched_ids = ai_result.get("matched_file_ids", [])
    explanation = ai_result.get("explanation", "")
    provider = ai_result.get("provider", "local")

    # Fetch matched file records preserving LLM ranked order
    file_map = {f["id"]: f for f in all_files}
    matched_files = [file_map[fid] for fid in matched_ids if fid in file_map]

    return {
        "query": clean_query,
        "matched_file_ids": matched_ids,
        "files": matched_files,
        "explanation": explanation,
        "provider": provider
    }
