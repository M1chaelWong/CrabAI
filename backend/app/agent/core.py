from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator

import anthropic

from app.agent.context import ConversationContext
from app.agent.streaming import (
    SSEEvent,
    message_start,
    content_block_start,
    content_block_delta,
    content_block_stop,
    message_delta,
    message_stop,
    error_event,
)
from app.files.parser import parse_file
from app.storage.models import generate_uuid
from app.storage.repositories import MessageRepo, ConversationRepo, FileRepo
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 25
from app.config import settings
DEFAULT_MODEL = settings.DEFAULT_MODEL


class AgentRunner:
    def __init__(
        self,
        client: anthropic.AsyncAnthropic,
        tool_registry: ToolRegistry,
        message_repo: MessageRepo,
        conversation_repo: ConversationRepo,
        file_repo: FileRepo | None = None,
        context: ConversationContext | None = None,
    ):
        self.client = client
        self.tool_registry = tool_registry
        self.message_repo = message_repo
        self.conversation_repo = conversation_repo
        self.file_repo = file_repo
        self.context = context or ConversationContext(message_repo)

    async def run(
        self,
        conversation_id: str,
        user_content: str | list,
        model: str = DEFAULT_MODEL,
        file_ids: list[str] | None = None,
    ) -> AsyncGenerator[SSEEvent, None]:
        # Get conversation for system prompt
        conv = await self.conversation_repo.get(conversation_id)
        if not conv:
            yield error_event("Conversation not found")
            return

        # Get next sequence number
        existing = await self.message_repo.list_by_conversation(conversation_id)
        next_seq = (existing[-1].sequence_num + 1) if existing else 0

        # ----- File content injection (P0-2) -----
        if file_ids and self.file_repo:
            content_blocks: list[dict[str, Any]] = []
            # Original user text
            if isinstance(user_content, str):
                content_blocks.append({"type": "text", "text": user_content})
            elif isinstance(user_content, list):
                content_blocks.extend(user_content)

            for fid in file_ids:
                db_file = await self.file_repo.get(fid)
                if not db_file:
                    continue
                # Read file from disk
                try:
                    with open(db_file.file_path, "rb") as f:
                        data = f.read()
                except OSError:
                    content_blocks.append({"type": "text", "text": f"[File {db_file.original_name}: read error]"})
                    continue

                result = parse_file(data, db_file.original_name, db_file.mime_type)
                if result["type"] == "image" and isinstance(result["content"], list):
                    # image_parser returns content blocks (e.g. base64 image block)
                    content_blocks.extend(result["content"])
                elif result["type"] == "text":
                    content_blocks.append({
                        "type": "text",
                        "text": f"[File: {db_file.original_name}]\n{result['content']}",
                    })
                else:
                    content_blocks.append({
                        "type": "text",
                        "text": f"[File: {db_file.original_name}] (unsupported)",
                    })

            user_content = content_blocks

        # Persist user message
        content_str = user_content if isinstance(user_content, str) else json.dumps(user_content)
        await self.message_repo.create(
            conversation_id=conversation_id,
            role="user",
            content=content_str,
            sequence_num=next_seq,
        )

        # ----- Separate local tools from server tools (P0-3) -----
        local_tool_defs = [
            d for d in self.tool_registry.get_all_definitions()
            if d.get("type") != "server_tool"
        ]
        server_tool_defs = self.tool_registry.get_server_tool_definitions()

        # Agentic loop
        for iteration in range(MAX_ITERATIONS):
            messages = await self.context.build_messages(conversation_id)

            api_kwargs: dict[str, Any] = {
                "model": model,
                "max_tokens": 8192,
                "messages": messages,
            }
            # Local tools use "tools", server tools use "server_tools" (P0-3)
            all_tools = local_tool_defs + server_tool_defs
            if all_tools:
                api_kwargs["tools"] = all_tools
            # Build system prompt with current date
            from datetime import date
            date_str = date.today().isoformat()
            system_parts = [f"Current date: {date_str}."]
            if conv.system_prompt:
                system_parts.append(conv.system_prompt)
            api_kwargs["system"] = "\n\n".join(system_parts)

            # Stream the response
            assistant_message_id = generate_uuid()

            full_text = ""
            tool_uses: list[dict[str, Any]] = []
            stop_reason = ""
            usage_info: dict[str, Any] = {}
            block_index = 0

            try:
                async with self.client.messages.stream(**api_kwargs) as stream:
                    async for event in stream:
                        if event.type == "message_start":
                            if hasattr(event.message, "usage") and event.message.usage:
                                usage_info["input_tokens"] = event.message.usage.input_tokens
                            # Emit message_start with model info
                            yield message_start(assistant_message_id, model)

                        elif event.type == "content_block_start":
                            block = event.content_block
                            idx = event.index
                            block_index = idx

                            if block.type == "tool_use":
                                tool_uses.append({
                                    "id": block.id,
                                    "name": block.name,
                                    "input_json": "",
                                })
                                yield content_block_start(idx, {
                                    "type": "tool_use",
                                    "id": block.id,
                                    "name": block.name,
                                    "input": {},
                                })
                            elif block.type == "text":
                                yield content_block_start(idx, {
                                    "type": "text",
                                    "text": "",
                                })
                            elif block.type == "server_tool_use":
                                # Server tool block – forward as tool_use for UI
                                tool_uses.append({
                                    "id": block.id,
                                    "name": block.name,
                                    "input_json": "",
                                    "server": True,
                                })
                                yield content_block_start(idx, {
                                    "type": "tool_use",
                                    "id": block.id,
                                    "name": block.name,
                                    "input": {},
                                })

                        elif event.type == "content_block_delta":
                            delta = event.delta
                            idx = event.index
                            if delta.type == "text_delta":
                                full_text += delta.text
                                yield content_block_delta(idx, {
                                    "type": "text_delta",
                                    "text": delta.text,
                                })
                            elif delta.type == "input_json_delta":
                                if tool_uses:
                                    tool_uses[-1]["input_json"] += delta.partial_json
                                yield content_block_delta(idx, {
                                    "type": "input_json_delta",
                                    "partial_json": delta.partial_json,
                                })

                        elif event.type == "content_block_stop":
                            yield content_block_stop(event.index)

                        elif event.type == "message_delta":
                            stop_reason = event.delta.stop_reason or ""
                            if hasattr(event, "usage") and event.usage:
                                usage_info["output_tokens"] = event.usage.output_tokens

            except anthropic.APIError as e:
                yield error_event(f"API error: {e.message}")
                return

            # Build content blocks for persistence
            persist_blocks: list[dict[str, Any]] = []
            if full_text:
                persist_blocks.append({"type": "text", "text": full_text})
            for tu in tool_uses:
                try:
                    parsed_input = json.loads(tu["input_json"]) if tu["input_json"] else {}
                except json.JSONDecodeError:
                    parsed_input = {}
                persist_blocks.append({
                    "type": "tool_use",
                    "id": tu["id"],
                    "name": tu["name"],
                    "input": parsed_input,
                })

            # Persist assistant message
            next_seq += 1
            await self.message_repo.create(
                id=assistant_message_id,
                conversation_id=conversation_id,
                role="assistant",
                content=json.dumps(persist_blocks) if len(persist_blocks) > 1 or tool_uses else full_text,
                model=model,
                stop_reason=stop_reason,
                token_usage=json.dumps(usage_info) if usage_info else None,
                sequence_num=next_seq,
            )

            # Update conversation timestamp
            await self.conversation_repo.update(conversation_id)

            if stop_reason == "tool_use" and tool_uses:
                # Execute tools and continue loop
                tool_result_blocks: list[dict[str, Any]] = []
                for tu in tool_uses:
                    # Server tools are handled by the API – still need a tool_result
                    # placeholder so Claude sees the result in the conversation history.
                    if tu.get("server"):
                        # The API streams server tool results inline; no local
                        # execution needed, but we must NOT skip the tool_result
                        # or Claude will stall waiting for it.  Anthropic's streaming
                        # API already injects the result into the message history
                        # on the server side, so we simply skip persisting a
                        # duplicate tool_result for server tools.
                        continue

                    try:
                        parsed_input = json.loads(tu["input_json"]) if tu["input_json"] else {}
                    except json.JSONDecodeError:
                        parsed_input = {}

                    result_content = await self.tool_registry.execute(tu["name"], parsed_input)
                    result_str = result_content if isinstance(result_content, str) else json.dumps(result_content)
                    tool_result_blocks.append({
                        "type": "tool_result",
                        "tool_use_id": tu["id"],
                        "content": result_str,
                    })
                    # Emit tool_result SSE event so frontend can display output
                    yield SSEEvent(
                        event="tool_result",
                        data={
                            "type": "tool_result",
                            "tool_use_id": tu["id"],
                            "content": result_str,
                        },
                    )

                if tool_result_blocks:
                    # Persist tool results as a user message (Claude API format)
                    next_seq += 1
                    await self.message_repo.create(
                        conversation_id=conversation_id,
                        role="user",
                        content=json.dumps(tool_result_blocks),
                        sequence_num=next_seq,
                    )
                # Continue the loop
                yield message_delta(stop_reason)
                continue

            # end_turn or max_tokens - finish
            yield message_delta(stop_reason)
            yield message_stop()
            return

        # Safety: max iterations reached
        yield error_event("Maximum iterations reached")
        yield message_delta("max_iterations")
        yield message_stop()
