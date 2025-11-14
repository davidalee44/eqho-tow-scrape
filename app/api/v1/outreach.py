"""Outreach API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.schemas.outreach import (
    OutreachSequenceCreate,
    OutreachSequenceResponse,
    OutreachAssignmentCreate,
    OutreachHistoryResponse,
)
from app.services.outreach_service import OutreachService
from app.models.outreach import OutreachHistory
from app.auth.dependencies import get_current_user
from sqlalchemy import select

router = APIRouter()


@router.post("/sequences", response_model=OutreachSequenceResponse, status_code=201)
async def create_sequence(
    sequence_data: OutreachSequenceCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create an outreach sequence"""
    service = OutreachService()
    steps = [step.model_dump() for step in sequence_data.steps]
    sequence = await service.create_sequence(
        db,
        sequence_data.name,
        sequence_data.description,
        sequence_data.is_active,
        steps
    )
    return sequence


@router.get("/sequences", response_model=list[OutreachSequenceResponse])
async def list_sequences(
    is_active: bool = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List outreach sequences"""
    from app.models.outreach import OutreachSequence
    from sqlalchemy import select
    
    query = select(OutreachSequence)
    if is_active is not None:
        query = query.where(OutreachSequence.is_active == is_active)
    
    result = await db.execute(query)
    sequences = result.scalars().all()
    return sequences


@router.post("/assign")
async def assign_company(
    assignment_data: OutreachAssignmentCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Assign a company to an outreach sequence"""
    service = OutreachService()
    assignment = await service.assign_company_to_sequence(
        db,
        assignment_data.company_id,
        assignment_data.sequence_id
    )
    return {"status": "assigned", "assignment_id": str(assignment.id)}


@router.post("/send")
async def send_outreach(
    company_id: UUID,
    channel: str,
    message_template: str,
    subject: str = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send immediate outreach (bypass sequence)"""
    service = OutreachService()
    outreach = await service.send_outreach(
        db,
        company_id,
        channel,
        message_template,
        subject
    )
    return {"status": "sent", "outreach_id": str(outreach.id)}


@router.get("/history/{company_id}", response_model=list[OutreachHistoryResponse])
async def get_outreach_history(
    company_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get outreach history for a company"""
    result = await db.execute(
        select(OutreachHistory).where(OutreachHistory.company_id == company_id)
    )
    history = result.scalars().all()
    return history


@router.put("/assignments/{assignment_id}/pause")
async def pause_assignment(
    assignment_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Pause an outreach assignment"""
    from app.models.outreach import OutreachAssignment
    
    result = await db.execute(
        select(OutreachAssignment).where(OutreachAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    assignment.status = 'paused'
    await db.commit()
    return {"status": "paused"}


@router.put("/assignments/{assignment_id}/resume")
async def resume_assignment(
    assignment_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resume an outreach assignment"""
    from app.models.outreach import OutreachAssignment
    
    result = await db.execute(
        select(OutreachAssignment).where(OutreachAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    assignment.status = 'active'
    await db.commit()
    return {"status": "active"}

