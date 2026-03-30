from __future__ import annotations

import json
from typing import Any

from app.storage.repositories import MessageRepo, FileRepo


def _is_tool_result_content(data: Any) -> bool:
    """Validate that data is a list of well-formed tool_result blocks."""
    if not isinstance(data, list):
        return False
    if not data:
        return False
    for item in data:
        if not isinstance(item, dict):
            return False
        if item.get("type") not in ("tool_result", "tool_use", "text", "image"):
            return False
        # tool_result blocks must have tool_use_id
        if item.get("type") == "tool_result" and "tool_use_id" not in item:
            return False
    return True


class ConversationContext:
    MAX_MESSAGES = 100

    def __init__(self, message_repo: MessageRepo, file_repo: FileRepo | None = None):
        self.message_repo = message_repo
        self.file_repo = file_repo

    async def build_messages(self, conversation_id: str) -> list[dict[str, Any]]:
        db_messages = await self.message_repo.list_by_conversation(conversation_id)

        # Simple strategy: keep the most recent messages
        if len(db_messages) > self.MAX_MESSAGES:
            db_messages = db_messages[-self.MAX_MESSAGES:]

        messages: list[dict[str, Any]] = []
        for msg in db_messages:
            content = msg.content
            # Try to parse JSON content (for tool_use / tool_result blocks)
            try:
                parsed = json.loads(content)
                if _is_tool_result_content(parsed):
                    content = parsed
            except (json.JSONDecodeError, TypeError):
                pass

            messages.append({"role": msg.role, "content": content})

        return messages
