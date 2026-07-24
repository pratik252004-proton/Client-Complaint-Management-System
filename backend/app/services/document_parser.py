"""
Turns an uploaded complaint document (PDF, DOCX, TXT, EML) into plain text
that can be handed to the LangGraph extraction agent.
"""

import email
from email import policy
from io import BytesIO

from fastapi import UploadFile, HTTPException

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".eml"}


def _extract_pdf_text(raw: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(raw))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx_text(raw: bytes) -> str:
    import docx

    document = docx.Document(BytesIO(raw))
    return "\n".join(p.text for p in document.paragraphs)


def _extract_eml_text(raw: bytes) -> str:
    msg = email.message_from_bytes(raw, policy=policy.default)
    parts = [f"Subject: {msg.get('subject', '')}", f"From: {msg.get('from', '')}"]
    body = msg.get_body(preferencelist=("plain", "html"))
    if body is not None:
        parts.append(body.get_content())
    return "\n".join(parts)


async def extract_text_from_upload(file: UploadFile, max_upload_mb: int = 10) -> str:
    filename = (file.filename or "").lower()
    ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported formats: PDF, DOCX, TXT, EML.",
        )

    raw = await file.read()
    if len(raw) > max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {max_upload_mb}MB limit.")

    try:
        if ext == ".pdf":
            return _extract_pdf_text(raw)
        if ext == ".docx":
            return _extract_docx_text(raw)
        if ext == ".eml":
            return _extract_eml_text(raw)
        # .txt
        return raw.decode("utf-8", errors="ignore")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Could not parse file: {exc}") from exc
