"""Enrichment schemas"""
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
from uuid import UUID


class EnrichmentSnapshotResponse(BaseModel):
    id: UUID
    company_id: UUID
    snapshot_data: Dict[str, Any]
    enrichment_source: str
    created_at: datetime

    class Config:
        from_attributes = True

