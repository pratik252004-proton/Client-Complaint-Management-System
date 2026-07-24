from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models.complaint import Complaint, ComplaintChatMessage, ChatRole
from app.services.document_parser import extract_text_from_upload
from app.services.extraction_agent import run_extraction
from app.services.chat_agent import run_chat

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/extract")
async def extract_complaint_fields(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Accepts either an uploaded document (PDF/DOCX/TXT/EML) or raw pasted
    text, runs it through the LangGraph extraction agent (Groq
    gemma2-9b-it), and returns structured fields the frontend can use to
    populate the complaint form.
    """
    if not file and not text:
        raise HTTPException(status_code=400, detail="Provide either a file upload or text.")

    if file:
        raw_text = await extract_text_from_upload(file, max_upload_mb=settings.max_upload_mb)
        source_label = file.filename
    else:
        raw_text = text
        source_label = "pasted text"

    if not raw_text or not raw_text.strip():
        raise HTTPException(status_code=422, detail="No readable text found in the input.")

    extracted = run_extraction(raw_text)

    return {"source": source_label, "extracted": extracted}


@router.post("/chat")
def chat_with_assistant(
    complaint_id: Optional[str] = Form(None),
    message: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Conversational Q&A over a complaint record, powered by Groq
    llama-3.3-70b-versatile. Persists both sides of the exchange for the
    QMS audit trail.
    """
    complaint_context = ""
    if complaint_id:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if complaint:
            complaint_context = (
                f"Product: {complaint.product_name}, Batch: {complaint.batch_lot_number}, "
                f"Type: {complaint.complaint_type}, Severity: {complaint.initial_severity}, "
                f"Priority: {complaint.priority}, Status: {complaint.status}.\n"
                f"Description: {complaint.detailed_description}"
            )

    history = []
    if complaint_id:
        past = (
            db.query(ComplaintChatMessage)
            .filter(ComplaintChatMessage.complaint_id == complaint_id)
            .order_by(ComplaintChatMessage.created_at.asc())
            .all()
        )
        history = [{"role": m.role.value, "content": m.content} for m in past]

    reply = run_chat(message, complaint_context=complaint_context, history=history)

    if complaint_id:
        db.add(ComplaintChatMessage(complaint_id=complaint_id, role=ChatRole.USER, content=message))
        db.add(ComplaintChatMessage(complaint_id=complaint_id, role=ChatRole.ASSISTANT, content=reply))
        db.commit()

    return {"reply": reply}
