"""CRUD, search and filter endpoints for leads."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Lead
from ..schemas import LeadCreate, LeadList, LeadOut, LeadUpdate, Status

router = APIRouter(prefix="/api", tags=["leads"])


def get_lead_or_404(lead_id: int, db: Session) -> Lead:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.get("/leads", response_model=LeadList)
def list_leads(
    search: str | None = Query(None, description="Matches name, company, email, event or notes"),
    status_filter: Status | None = Query(None, alias="status"),
    event: str | None = Query(None, description="Exact event name"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    conditions = []
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        conditions.append(
            or_(
                Lead.name.ilike(pattern),
                Lead.company.ilike(pattern),
                Lead.email.ilike(pattern),
                Lead.event.ilike(pattern),
                Lead.notes.ilike(pattern),
            )
        )
    if status_filter:
        conditions.append(Lead.status == status_filter)
    if event:
        conditions.append(Lead.event == event)

    total = db.scalar(select(func.count()).select_from(Lead).where(*conditions)) or 0
    items = db.scalars(
        select(Lead)
        .where(*conditions)
        .order_by(Lead.created_at.desc(), Lead.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return LeadList(items=items, total=total)


@router.get("/events", response_model=list[str])
def list_events(db: Session = Depends(get_db)):
    """Distinct event names, used to populate the event filter."""
    return db.scalars(select(Lead.event).distinct().order_by(Lead.event)).all()


@router.post("/leads", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    lead = Lead(**payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/leads/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    return get_lead_or_404(lead_id, db)


@router.put("/leads/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db)):
    lead = get_lead_or_404(lead_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is None:
            raise HTTPException(status_code=422, detail=f"'{field}' cannot be null")
        setattr(lead, field, value)
    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = get_lead_or_404(lead_id, db)
    db.delete(lead)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
