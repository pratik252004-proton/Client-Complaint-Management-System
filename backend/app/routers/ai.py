from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models.complaint import Complaint, ComplaintChatMessage, ChatRole
from app.services.document_parser import extract_text_from_upload
from app.services.extraction_agent import run_extraction
from app.services.chat_agent import run_chat
from app.services.risk_agent import run_risk_assessment

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/extract")
async def extract_complaint_fields(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
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
    Conversational Q&A over a complaint record. Also detects when the
    message is asking to add/edit specific complaint fields (Addon 2 & 3)
    and returns those in `form_updates` so the frontend can apply them to
    the form — same mechanism as document extraction, just triggered from
    chat instead of an upload.
    """
    complaint = None
    if complaint_id:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    valid_complaint_id = complaint.id if complaint else None

    complaint_context = ""
    if complaint:
        complaint_context = (
            f"Product: {complaint.product_name}, Batch: {complaint.batch_lot_number}, "
            f"Type: {complaint.complaint_type}, Severity: {complaint.initial_severity}, "
            f"Priority: {complaint.priority}, Status: {complaint.status}.\n"
            f"Description: {complaint.detailed_description}"
        )

    history = []
    if valid_complaint_id:
        past = (
            db.query(ComplaintChatMessage)
            .filter(ComplaintChatMessage.complaint_id == valid_complaint_id)
            .order_by(ComplaintChatMessage.created_at.asc())
            .all()
        )
        history = [{"role": m.role.value, "content": m.content} for m in past]

    result = run_chat(message, complaint_context=complaint_context, history=history)
    reply = result["reply"]
    form_updates = result["form_updates"]

    if valid_complaint_id:
        db.add(ComplaintChatMessage(complaint_id=valid_complaint_id, role=ChatRole.USER, content=message))
        db.add(ComplaintChatMessage(complaint_id=valid_complaint_id, role=ChatRole.ASSISTANT, content=reply))
        db.commit()

    return {"reply": reply, "form_updates": form_updates}


@router.post("/risk-assessment")
async def generate_risk_assessment(
    complaint_id: Optional[str] = Form(None),
    fields_json: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Addon 1 — AI risk assessment. Accepts either a saved complaint_id, or
    a JSON string of the current (possibly unsaved) form fields via
    `fields_json`, so this works before the complaint has even been saved.
    """
    import json as _json

    complaint_fields = {}

    if complaint_id:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")
        complaint_fields = {
            "product_name": complaint.product_name,
            "product_strength": complaint.product_strength,
            "batch_lot_number": complaint.batch_lot_number,
            "quantity_affected": str(complaint.quantity_affected) if complaint.quantity_affected else None,
            "complaint_type": complaint.complaint_type,
            "detailed_description": complaint.detailed_description,
            "initial_severity": complaint.initial_severity,
            "priority": complaint.priority,
        }
    elif fields_json:
        try:
            complaint_fields = _json.loads(fields_json)
        except _json.JSONDecodeError:
            raise HTTPException(status_code=422, detail="fields_json must be valid JSON.")
    else:
        raise HTTPException(status_code=400, detail="Provide either complaint_id or fields_json.")

    assessment = run_risk_assessment(complaint_fields)
    return {"assessment": assessment}
