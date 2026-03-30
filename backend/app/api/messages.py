import json

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.storage.database import get_session
from app.storage.repositories import ConversationRepo, MessageRepo, MemoryRepo, FileRepo
from app.agent.core import AgentRunner
from app.tools.registry import ToolRegistry
from app.tools.web_search import WebSearchTool
from app.tools.code_execution import CodeExecutionTool
from app.tools.memory_tool import MemoryTool

router = APIRouter(prefix="/conversations", tags=["messages"])


class SendMessage(BaseModel):
    content: str | list
    model: str = "claude-sonnet-4-20250514"
    file_ids: list[str] | None = None


def build_tool_registry(memory_repo: MemoryRepo) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(WebSearchTool())
    registry.register(CodeExecutionTool())
    registry.register(MemoryTool(memory_repo))
    return registry


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    session: AsyncSession = Depends(get_session),
):
    conv_repo = ConversationRepo(session)
    conv = await conv_repo.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msg_repo = MessageRepo(session)
    messages = await msg_repo.list_by_conversation(conversation_id)
    def parse_content(raw: str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        return raw

    result = []
    for m in messages:
        content = parse_content(m.content)
        # Skip tool_result messages (role=user with tool_result blocks)
        if m.role == "user" and isinstance(content, list) and content and isinstance(content[0], dict) and content[0].get("type") == "tool_result":
            continue
        # Merge consecutive assistant messages into one
        if m.role == "assistant" and result and result[-1]["role"] == "assistant":
            prev = result[-1]["content"]
            # Ensure both are lists
            prev_blocks = prev if isinstance(prev, list) else [{"type": "text", "text": prev}]
            new_blocks = content if isinstance(content, list) else [{"type": "text", "text": content}]
            result[-1]["content"] = prev_blocks + new_blocks
            result[-1]["stop_reason"] = m.stop_reason
            continue
        result.append({
            "id": m.id,
            "conversation_id": m.conversation_id,
            "role": m.role,
            "content": content,
            "model": m.model,
            "stop_reason": m.stop_reason,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })
    return result


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    body: SendMessage,
    session: AsyncSession = Depends(get_session),
):
    conv_repo = ConversationRepo(session)
    conv = await conv_repo.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    client_kwargs = {"api_key": settings.ANTHROPIC_API_KEY}
    if settings.LLM_BASE_URL:
        client_kwargs["base_url"] = settings.LLM_BASE_URL
    client = anthropic.AsyncAnthropic(**client_kwargs)
    msg_repo = MessageRepo(session)
    memory_repo = MemoryRepo(session)
    file_repo = FileRepo(session)

    registry = build_tool_registry(memory_repo)

    runner = AgentRunner(
        client=client,
        tool_registry=registry,
        message_repo=msg_repo,
        conversation_repo=conv_repo,
        file_repo=file_repo,
    )

    async def event_generator():
        async for event in runner.run(
            conversation_id,
            body.content,
            model=body.model,
            file_ids=body.file_ids,
        ):
            yield {"event": event.event, "data": json.dumps(event.data)}

    return EventSourceResponse(event_generator())
