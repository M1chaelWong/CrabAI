import base64

SUPPORTED_MIMES = {
    "image/png": "png",
    "image/jpeg": "jpeg",
    "image/gif": "gif",
    "image/webp": "webp",
}


def can_handle(mime_type: str) -> bool:
    return mime_type in SUPPORTED_MIMES


def parse(data: bytes, mime_type: str) -> list[dict]:
    """Return a Claude API image content block."""
    media_type = mime_type if mime_type in SUPPORTED_MIMES else "image/png"
    b64 = base64.b64encode(data).decode("ascii")
    return [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": b64,
            },
        }
    ]
