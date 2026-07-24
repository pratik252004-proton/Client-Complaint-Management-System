from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from app.models.complaint import ComplaintStatus, Severity, Priority


class ComplaintBase(BaseModel):
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None

    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_lot_number: Optional[str] = None
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    quantity_affected: Optional[Decimal] = None

    complaint_type: Optional[str] = None
    complaint_date: Optional[date] = None
    detailed_description: Optional[str] = None

    initial_severity: Optional[Severity] = None
    priority: Optional[Priority] = None


class ComplaintCreate(ComplaintBase):
    created_by: Optional[str] = None
    ai_populated_fields: Optional[List[str]] = []


class ComplaintUpdate(ComplaintBase):
    status: Optional[ComplaintStatus] = None
    ai_populated_fields: Optional[List[str]] = None


class ComplaintOut(ComplaintBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: ComplaintStatus
    ai_populated_fields: Optional[List[str]] = []
    created_at: datetime
    updated_at: datetime


class ComplaintListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    batch_lot_number: Optional[str] = None
    status: ComplaintStatus
    priority: Optional[Priority] = None
    initial_severity: Optional[Severity] = None
    created_at: datetime


class ChatMessageIn(BaseModel):
    complaint_id: Optional[str] = None
    message: str


class ChatMessageOut(BaseModel):
    role: str
    content: str
