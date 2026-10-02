"""
Folders and Tags Router for Index.
Handles folder organization and tag discovery for the sidebar tag cloud.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app import database

router = APIRouter(tags=["folders_and_tags"])

class CreateFolderRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    color: Optional[str] = "#C09543"
    icon: Optional[str] = "folder"

@router.get("/api/folders")
def list_folders():
    """Retrieve all folders with their file counts."""
    return database.get_all_folders()

@router.post("/api/folders")
def create_new_folder(payload: CreateFolderRequest):
    """Create a new organizational folder."""
    clean_name = payload.name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Folder name is required")

    try:
        new_folder = database.create_folder(
            name=clean_name,
            description=payload.description or "",
            color=payload.color or "#C09543",
            icon=payload.icon or "folder"
        )
        return new_folder
    except Exception as e:
        if "UNIQUE" in str(e).upper():
            raise HTTPException(status_code=400, detail="A folder with this name already exists")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/folders/{folder_id}")
def delete_folder_by_id(folder_id: int):
    """Deletes folder, unlinking contained files safely."""
    folder = database.get_folder_by_id(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    database.delete_folder(folder_id)
    return {"message": f"Folder '{folder['name']}' deleted successfully", "id": folder_id}

@router.get("/api/tags")
def list_tags():
    """Retrieve all tags with usage counts for the sidebar tag cloud."""
    return database.get_all_tags_with_counts()
