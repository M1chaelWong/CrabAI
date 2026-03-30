import fitz  # pymupdf


def can_handle(mime_type: str) -> bool:
    return mime_type == "application/pdf"


def parse(data: bytes, filename: str) -> str:
    """Extract text from PDF, with page separators."""
    doc = fitz.open(stream=data, filetype="pdf")
    pages: list[str] = []
    for i, page in enumerate(doc, 1):
        text = page.get_text().strip()
        if text:
            pages.append(f"--- Page {i} ---\n{text}")
    doc.close()
    if not pages:
        return f"[File: {filename}]\n(No extractable text found in PDF)"
    return f"[File: {filename}]\n" + "\n\n".join(pages)
