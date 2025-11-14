"""Outreach schemas"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class OutreachSequenceStep(BaseModel):
    channel: str  # 'email', 'sms', 'phone'
    delay_hours: int
    template: str
    subject: Optional[str] = None


class OutreachSequenceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    steps: List[OutreachSequenceStep]


class OutreachSequenceResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    steps: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OutreachAssignmentCreate(BaseModel):
    company_id: UUID
    sequence_id: UUID


class OutreachHistoryResponse(BaseModel):
    id: UUID
    company_id: UUID
    channel: str
    status: str
    message_content: str
    external_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    outreach_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

