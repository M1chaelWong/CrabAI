SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".ts", ".jsx", ".tsx",
    ".html", ".css", ".json", ".yaml", ".yml", ".xml",
    ".csv", ".sql", ".sh", ".bash", ".zsh",
    ".java", ".c", ".cpp", ".h", ".hpp", ".go", ".rs",
    ".rb", ".php", ".swift", ".kt", ".scala", ".r",
    ".toml", ".ini", ".cfg", ".conf", ".env", ".log",
    ".gitignore", ".dockerfile",
}

SUPPORTED_MIMES = {
    "text/plain", "text/markdown", "text/html", "text/css",
    "text/csv", "text/xml",
    "application/json", "application/xml",
    "application/x-yaml", "application/x-sh",
    "application/javascript",
}


def can_handle(mime_type: str, extension: str) -> bool:
    return (
        mime_type.startswith("text/")
        or mime_type in SUPPORTED_MIMES
        or extension.lower() in SUPPORTED_EXTENSIONS
    )


def parse(data: bytes, filename: str) -> str:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
    return f"[File: {filename}]\n{text}"
