"""
Files Router for Index.
Handles file upload, listing, details, download, deletion, folder assignment,
and manual/AI tagging.
"""

import os
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app import database, text_extractor, ai_service, config

router = APIRouter(prefix="/api/files", tags=["files"])

class FolderAssignRequest(BaseModel):
    folder_id: Optional[int] = None

class AddTagRequest(BaseModel):
    tag_name: str

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    folder_id: Optional[int] = Form(None)
):
    """
    Accepts one or more uploaded files.
    Saves to local disk, extracts text, performs AI auto-tagging and summarization,
    and inserts into SQLite.
    """
    results = []

    for file in files:
        original_name = file.filename or "untitled"
        extension = Path(original_name).suffix.lower()
        
        # Unique disk filename to avoid collisions
        unique_disk_name = f"{uuid.uuid4().hex}_{original_name}"
        save_path = config.UPLOAD_DIR / unique_disk_name

        # Save file to disk
        try:
            content_bytes = await file.read()
            file_size = len(content_bytes)

            with open(save_path, "wb") as f_out:
                f_out.write(content_bytes)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save {original_name}: {str(e)}")

        # 1. Extract text from file
        mime_type = file.content_type or "application/octet-stream"
        extracted_text, is_text_based = text_extractor.extract_text_from_file(str(save_path), extension)

        # 2. AI Auto-tagging & Summarization
        ai_data = await ai_service.generate_file_tags_and_summary(
            filename=original_name,
            extension=extension,
            content=extracted_text
        )

        summary = ai_data.get("summary", "")
        generated_tags = ai_data.get("tags", [])

        # 3. Insert into database
        file_id = database.insert_file(
            filename=unique_disk_name,
            original_name=original_name,
            file_path=str(save_path),
            file_size=file_size,
            mime_type=mime_type,
            extension=extension,
            folder_id=folder_id if folder_id and folder_id > 0 else None,
            summary=summary,
            extracted_text=extracted_text
        )

        # 4. Associate AI generated tags
        for t in generated_tags:
            database.add_tag_to_file(file_id, t, is_ai_generated=True)

        full_file_record = database.get_file_by_id(file_id)
        results.append(full_file_record)

    return {"uploaded": results, "count": len(results)}

@router.get("")
def list_files(
    folder_id: Optional[int] = Query(None, description="Filter by folder ID (0 for uncategorized)"),
    tag: Optional[str] = Query(None, description="Filter by tag name"),
    search: Optional[str] = Query(None, description="Standard keyword search"),
    sort_by: str = Query("newest", description="Sorting: newest, oldest, name, size")
):
    """List files with optional filtering and sorting."""
    return database.get_all_files(
        folder_id=folder_id,
        tag=tag,
        search=search,
        sort_by=sort_by
    )

@router.get("/{file_id}")
def get_file_details(file_id: int):
    """Retrieve full file record including tags and preview."""
    record = database.get_file_by_id(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    return record

@router.get("/{file_id}/download")
def download_file(file_id: int):
    """Download the actual physical file from storage."""
    record = database.get_file_by_id(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = Path(record["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Physical file missing on server disk")

    return FileResponse(
        path=str(file_path),
        filename=record["original_name"],
        media_type=record["mime_type"]
    )

@router.delete("/{file_id}")
def delete_file(file_id: int):
    """Deletes the file record from database and removes it from disk."""
    record = database.delete_file_record(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    # Remove physical file on disk
    file_path = Path(record["file_path"])
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            print(f"[Warning] Failed to delete disk file {file_path}: {e}")

    return {"message": "File deleted successfully", "id": file_id}

@router.put("/{file_id}/folder")
def update_folder_assignment(file_id: int, payload: FolderAssignRequest):
    """Move file to another folder or uncategorize."""
    record = database.get_file_by_id(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    target_folder_id = payload.folder_id if payload.folder_id and payload.folder_id > 0 else None
    if target_folder_id is not None:
        folder = database.get_folder_by_id(target_folder_id)
        if not folder:
            raise HTTPException(status_code=400, detail="Target folder does not exist")

    database.update_file_folder(file_id, target_folder_id)
    return database.get_file_by_id(file_id)

@router.post("/{file_id}/tags")
def add_tag(file_id: int, payload: AddTagRequest):
    """Manually add a tag to a file."""
    record = database.get_file_by_id(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    clean_tag = payload.tag_name.strip()
    if not clean_tag:
        raise HTTPException(status_code=400, detail="Tag name cannot be empty")

    database.add_tag_to_file(file_id, clean_tag, is_ai_generated=False)
    return {"message": "Tag added", "tags": database.get_tags_for_file(file_id)}

@router.delete("/{file_id}/tags/{tag_id}")
def remove_tag(file_id: int, tag_id: int):
    """Remove a tag from a file."""
    record = database.get_file_by_id(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    success = database.remove_tag_from_file(file_id, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not associated with this file")

    return {"message": "Tag removed", "tags": database.get_tags_for_file(file_id)}

@router.post("/{file_id}/reprocess-ai")
async def reprocess_file_with_ai(file_id: int):
    """Re-runs AI summarization and auto-tagging on an existing file."""
    record = database.get_file_by_id(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    ai_data = await ai_service.generate_file_tags_and_summary(
        filename=record["original_name"],
        extension=record["extension"],
        content=record["extracted_text"]
    )

    summary = ai_data.get("summary", "")
    database.update_file_ai_data(file_id, summary)

    # Add any newly generated tags
    for t in ai_data.get("tags", []):
        database.add_tag_to_file(file_id, t, is_ai_generated=True)

    return database.get_file_by_id(file_id)
