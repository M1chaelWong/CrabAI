from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SSEEvent:
    """Server-Sent Event that carries a typed JSON payload.

    The frontend reads only the `data:` line and expects a JSON object with a
    `type` field that matches one of the StreamEvent discriminants defined in
    frontend/src/types/index.ts.  The SSE `event:` name is kept for debugging
    but is NOT used by the frontend parser.
    """

    event: str
    data: dict[str, Any] = field(default_factory=dict)

    def encode(self) -> str:
        return f"event: {self.event}\ndata: {json.dumps(self.data)}\n\n"


# ---------------------------------------------------------------------------
# Event constructors – each returns data matching a frontend StreamEvent type
# ---------------------------------------------------------------------------

def message_start(message_id: str, model: str) -> SSEEvent:
    return SSEEvent(
        event="message_start",
        data={
            "type": "message_start",
            "message": {
                "id": message_id,
                "role": "assistant",
                "model": model,
            },
        },
    )


def content_block_start(index: int, content_block: dict[str, Any]) -> SSEEvent:
    return SSEEvent(
        event="content_block_start",
        data={
            "type": "content_block_start",
            "index": index,
            "content_block": content_block,
        },
    )


def content_block_delta(index: int, delta: dict[str, Any]) -> SSEEvent:
    return SSEEvent(
        event="content_block_delta",
        data={
            "type": "content_block_delta",
            "index": index,
            "delta": delta,
        },
    )


def content_block_stop(index: int) -> SSEEvent:
    return SSEEvent(
        event="content_block_stop",
        data={
            "type": "content_block_stop",
            "index": index,
        },
    )


def message_delta(stop_reason: str) -> SSEEvent:
    return SSEEvent(
        event="message_delta",
        data={
            "type": "message_delta",
            "delta": {
                "stop_reason": stop_reason,
            },
        },
    )


def message_stop() -> SSEEvent:
    return SSEEvent(event="message_stop", data={"type": "message_stop"})


def error_event(message: str) -> SSEEvent:
    return SSEEvent(
        event="error",
        data={
            "type": "error",
            "error": {
                "type": "server_error",
                "message": message,
            },
        },
    )
