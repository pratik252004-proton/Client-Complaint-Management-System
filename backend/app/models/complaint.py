import enum
import uuid
from datetime import datetime, date

from sqlalchemy import Column, String, Text, Date, DateTime, Enum, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship

from app.db.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


def _enum_column(enum_cls, **kwargs):
    """SQLAlchemy stores a Python Enum's *member name* by default (e.g.
    'PENDING_TRIAGE'). We want the human-readable *value* stored instead
    (e.g. 'Pending Triage'), since that's what the frontend sends/expects
    and it makes ad-hoc SQL/reporting readable."""
    return Column(Enum(enum_cls, values_callable=lambda obj: [e.value for e in obj]), **kwargs)


class ComplaintStatus(str, enum.Enum):
    PENDING_TRIAGE = "Pending Triage"
    UNDER_REVIEW = "Under Review"
    INVESTIGATION = "Investigation"
    CAPA_INITIATED = "CAPA Initiated"
    CLOSED = "Closed"


class Severity(str, enum.Enum):
    CRITICAL = "Critical"
    MAJOR = "Major"
    MINOR = "Minor"


class Priority(str, enum.Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String(36), primary_key=True, default=gen_uuid)

    # 1. Origin & Customer Details
    complaint_source = Column(String(255))
    customer_name = Column(String(255))

    # 2. Product & Batch Identification
    product_name = Column(String(255))
    product_strength = Column(String(100))
    batch_lot_number = Column(String(100), index=True)
    manufacturing_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    quantity_affected = Column(Numeric(12, 2), nullable=True)

    # 3. Complaint Details
    complaint_type = Column(String(255))
    complaint_date = Column(Date, nullable=True)
    detailed_description = Column(Text)

    # 4. Initial Assessment & Priority
    initial_severity = _enum_column(Severity, nullable=True)
    priority = _enum_column(Priority, nullable=True)

    status = _enum_column(ComplaintStatus, default=ComplaintStatus.PENDING_TRIAGE, nullable=False)

    # AI provenance: which fields were populated by the AI extraction agent,
    # kept for QMS audit trail / data-integrity review
    ai_populated_fields = Column(JSON, default=list)
    ai_extraction_confidence = Column(JSON, nullable=True)  # per-field confidence scores

    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    attachments = relationship(
        "ComplaintAttachment", back_populates="complaint", cascade="all, delete-orphan"
    )
    chat_messages = relationship(
        "ComplaintChatMessage", back_populates="complaint", cascade="all, delete-orphan"
    )


class ComplaintAttachment(Base):
    __tablename__ = "complaint_attachments"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    complaint_id = Column(String(36), ForeignKey("complaints.id"), nullable=False)
    filename = Column(String(500))
    file_path = Column(String(1000))
    mime_type = Column(String(100))
    extracted_text = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="attachments")


class ChatRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ComplaintChatMessage(Base):
    __tablename__ = "complaint_chat_messages"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    complaint_id = Column(String(36), ForeignKey("complaints.id"), nullable=True)
    role = _enum_column(ChatRole, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="chat_messages")
