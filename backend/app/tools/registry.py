from __future__ import annotations

from typing import Any

from app.tools.base import BaseTool


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._server_tools: list[dict[str, Any]] = []

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def register_server_tool(self, definition: dict[str, Any]) -> None:
        self._server_tools.append(definition)

    def get_all_definitions(self) -> list[dict[str, Any]]:
        local = [t.get_definition() for t in self._tools.values()]
        return local + self._server_tools

    def get_server_tool_definitions(self) -> list[dict[str, Any]]:
        return list(self._server_tools)

    async def execute(self, name: str, tool_input: dict[str, Any]) -> str | list:
        tool = self._tools.get(name)
        if not tool:
            return f"Error: unknown tool '{name}'"
        return await tool.execute(tool_input)

    def is_server_tool(self, name: str) -> bool:
        return any(d.get("name") == name for d in self._server_tools)
