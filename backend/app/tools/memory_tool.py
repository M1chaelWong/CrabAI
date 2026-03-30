import json

from app.tools.base import BaseTool
from app.storage.repositories import MemoryRepo


class MemoryTool(BaseTool):
    name = "memory"
    description = "Store, retrieve, and list persistent memories across conversations."

    def __init__(self, memory_repo: MemoryRepo):
        self.repo = memory_repo

    def get_definition(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["store", "retrieve", "list", "delete"],
                        "description": "The action to perform",
                    },
                    "key": {
                        "type": "string",
                        "description": "The memory key (required for store, retrieve, delete)",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to store (required for store)",
                    },
                },
                "required": ["action"],
            },
        }

    async def execute(self, input: dict) -> str:
        action = input.get("action")
        key = input.get("key", "")
        content = input.get("content", "")

        if action == "store":
            if not key or not content:
                return "Error: 'key' and 'content' are required for store"
            mem = await self.repo.upsert(key=key, content=content, source="agent")
            return f"Stored memory '{key}'"

        elif action == "retrieve":
            if not key:
                return "Error: 'key' is required for retrieve"
            mem = await self.repo.get(key)
            if not mem:
                return f"No memory found for key '{key}'"
            return mem.content

        elif action == "list":
            memories = await self.repo.list_all()
            if not memories:
                return "No memories stored"
            items = [{"key": m.key, "content": m.content[:100]} for m in memories]
            return json.dumps(items)

        elif action == "delete":
            if not key:
                return "Error: 'key' is required for delete"
            deleted = await self.repo.delete(key)
            return f"Deleted memory '{key}'" if deleted else f"No memory found for key '{key}'"

        return f"Error: Unknown action '{action}'"
