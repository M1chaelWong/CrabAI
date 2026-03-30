import json
import os

from app.tools.base import BaseTool
from app.storage.repositories import FileRepo
from app.files.parser import parse_file


class FileReaderTool(BaseTool):
    name = "file_reader"
    description = "Read the parsed content of an uploaded file by its ID."

    def __init__(self, file_repo: FileRepo):
        self.repo = file_repo

    def get_definition(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "The ID of the uploaded file to read",
                    },
                },
                "required": ["file_id"],
            },
        }

    async def execute(self, input: dict) -> str | list:
        file_id = input.get("file_id", "")
        if not file_id:
            return "Error: 'file_id' is required"

        db_file = await self.repo.get(file_id)
        if not db_file:
            return f"Error: file '{file_id}' not found"

        # Return cached parsed content if available (text files)
        if db_file.parsed_content:
            return db_file.parsed_content

        # Re-parse from disk (e.g. for images that need content blocks)
        if not os.path.exists(db_file.file_path):
            return f"Error: file data not found on disk for '{file_id}'"

        with open(db_file.file_path, "rb") as f:
            data = f.read()

        result = parse_file(data, db_file.original_name, db_file.mime_type)
        if result["type"] == "image":
            return result["content"]  # list of content blocks
        return result["content"]
