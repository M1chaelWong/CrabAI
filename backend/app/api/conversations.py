from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.database import get_session
from app.storage.repositories import ConversationRepo

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    title: str = "New Conversation"
    system_prompt: str | None = None


class ConversationUpdate(BaseModel):
    title: str | None = None
    system_prompt: str | None = None


class ConversationOut(BaseModel):
    id: str
    title: str
    system_prompt: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.post("", response_model=ConversationOut, status_code=201)
async def create_conversation(body: ConversationCreate, session: AsyncSession = Depends(get_session)):
    repo = ConversationRepo(session)
    conv = await repo.create(title=body.title, system_prompt=body.system_prompt)
    return conv


@router.get("", response_model=list[ConversationOut])
async def list_conversations(session: AsyncSession = Depends(get_session)):
    repo = ConversationRepo(session)
    return await repo.list_all()


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conversation(conversation_id: str, session: AsyncSession = Depends(get_session)):
    repo = ConversationRepo(session)
    conv = await repo.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.patch("/{conversation_id}", response_model=ConversationOut)
async def update_conversation(conversation_id: str, body: ConversationUpdate, session: AsyncSession = Depends(get_session)):
    repo = ConversationRepo(session)
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    conv = await repo.update(conversation_id, **updates)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str, session: AsyncSession = Depends(get_session)):
    repo = ConversationRepo(session)
    deleted = await repo.delete(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
