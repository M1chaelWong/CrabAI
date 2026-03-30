import mimetypes
import os
from typing import Any

from app.files import text_parser, image_parser, pdf_parser


def guess_mime(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def parse_file(data: bytes, filename: str, mime_type: str | None = None) -> dict[str, Any]:
    """Parse file content and return a result dict.

    Returns:
        {
            "type": "text" | "image" | "unsupported",
            "content": str | list,  # parsed content or content blocks
            "mime_type": str,
        }
    """
    if not mime_type:
        mime_type = guess_mime(filename)

    ext = os.path.splitext(filename)[1]

    if image_parser.can_handle(mime_type):
        return {
            "type": "image",
            "content": image_parser.parse(data, mime_type),
            "mime_type": mime_type,
        }

    if pdf_parser.can_handle(mime_type):
        return {
            "type": "text",
            "content": pdf_parser.parse(data, filename),
            "mime_type": mime_type,
        }

    if text_parser.can_handle(mime_type, ext):
        return {
            "type": "text",
            "content": text_parser.parse(data, filename),
            "mime_type": mime_type,
        }

    return {
        "type": "unsupported",
        "content": f"[File: {filename}] (unsupported file type: {mime_type})",
        "mime_type": mime_type,
    }
