"""
Chat Router for Index.
Handles per-file interactive AI inquiries and conversation history.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from app import database, ai_service

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatMessageRequest(BaseModel):
    message: str

@router.get("/{file_id}/history")
def get_file_chat_history(file_id: int):
    """Retrieve full conversation history for a given document."""
    file_record = database.get_file_by_id(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    messages = database.get_chat_history(file_id)
    return {
        "file_id": file_id,
        "filename": file_record["original_name"],
        "messages": messages
    }

@router.post("/{file_id}/message")
async def send_chat_message(file_id: int, payload: ChatMessageRequest):
    """
    Submits a user inquiry about the document content.
    Persists user message, queries AI service with context, saves assistant reply.
    """
    user_text = payload.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    file_record = database.get_file_by_id(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # 1. Save user turn to database
    database.add_chat_message(file_id=file_id, role="user", content=user_text)

    # 2. Retrieve recent turns for context
    history = database.get_chat_history(file_id)

    # 3. Call AI Chat service
    ai_response = await ai_service.chat_with_file(
        filename=file_record["original_name"],
        content=file_record["extracted_text"],
        user_prompt=user_text,
        history=history
    )

    assistant_reply = ai_response.get("reply", "No response could be generated.")
    provider = ai_response.get("provider", "local")

    # 4. Save assistant reply to database
    assistant_record = database.add_chat_message(
        file_id=file_id,
        role="assistant",
        content=assistant_reply
    )

    return {
        "message": assistant_record,
        "provider": provider
    }

@router.delete("/{file_id}/history")
def clear_file_chat(file_id: int):
    """Clears conversation history for the document."""
    file_record = database.get_file_by_id(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    database.clear_chat_history(file_id)
    return {"message": "Chat history cleared successfully", "file_id": file_id}
