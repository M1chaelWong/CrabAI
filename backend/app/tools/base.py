from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    def get_definition(self) -> dict[str, Any]:
        """Return the Anthropic tool schema dict."""
        ...

    @abstractmethod
    async def execute(self, tool_input: dict[str, Any]) -> str | list:
        """Execute the tool and return the result."""
        ...
