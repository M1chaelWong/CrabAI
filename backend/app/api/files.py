import os
import uuid
from datetime import datetime

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.storage.database import get_session
from app.storage.repositories import FileRepo, ConversationRepo
from app.files.parser import parse_file, guess_mime

router = APIRouter(prefix="/files", tags=["files"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

ALLOWED_MIME_PREFIXES = (
    "text/",
    "image/",
    "application/pdf",
    "application/json",
    "application/javascript",
    "application/xml",
    "application/x-yaml",
    "application/csv",
)


class FileOut(BaseModel):
    id: str
    conversation_id: str
    message_id: str | None
    original_name: str
    mime_type: str
    file_size: int
    parsed_content: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("/upload", response_model=FileOut, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    conv_repo = ConversationRepo(session)
    conv = await conv_repo.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    data = await file.read()

    # P1-5: File size limit
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    filename = file.filename or "untitled"
    mime_type = file.content_type or guess_mime(filename)

    # P1-5: MIME type whitelist
    if not any(mime_type.startswith(prefix) for prefix in ALLOWED_MIME_PREFIXES):
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {mime_type}")

    # Save to disk (P2-8: async I/O)
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(filename)[1]
    stored_name = f"{file_id}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, stored_name)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(data)

    # Parse content
    result = parse_file(data, filename, mime_type)
    parsed_content = result["content"] if isinstance(result["content"], str) else None

    # Create DB record
    file_repo = FileRepo(session)
    db_file = await file_repo.create(
        id=file_id,
        conversation_id=conversation_id,
        original_name=filename,
        mime_type=mime_type,
        file_path=file_path,
        file_size=len(data),
        parsed_content=parsed_content,
    )
    return db_file


@router.get("/{file_id}")
async def get_file(
    file_id: str,
    conversation_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    file_repo = FileRepo(session)
    db_file = await file_repo.get(file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    # P1-6: Verify file belongs to the requested conversation
    if db_file.conversation_id != conversation_id:
        raise HTTPException(status_code=403, detail="File does not belong to this conversation")
    if not os.path.exists(db_file.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(
        path=db_file.file_path,
        filename=db_file.original_name,
        media_type=db_file.mime_type,
    )


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: str,
    conversation_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    file_repo = FileRepo(session)
    db_file = await file_repo.get(file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    # P1-6: Verify file belongs to the requested conversation
    if db_file.conversation_id != conversation_id:
        raise HTTPException(status_code=403, detail="File does not belong to this conversation")
    # Remove from disk
    if os.path.exists(db_file.file_path):
        os.remove(db_file.file_path)
    # Remove from DB
    await session.delete(db_file)
    await session.commit()
