"""AI endpoints: summarise notes and draft a follow-up email for a lead."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import ai
from ..database import get_db
from ..schemas import AIResult, FollowUpRequest
from .leads import get_lead_or_404

router = APIRouter(prefix="/api/leads", tags=["ai"])


def _run(fn, *args) -> str:
    try:
        return fn(*args)
    except ai.AINotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ai.AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/{lead_id}/summarize", response_model=AIResult)
def summarize(lead_id: int, db: Session = Depends(get_db)):
    lead = get_lead_or_404(lead_id, db)
    if not lead.notes.strip():
        raise HTTPException(status_code=400, detail="This lead has no notes to summarise yet.")
    text = _run(ai.summarize_notes, lead)
    return AIResult(lead_id=lead.id, kind="summary", text=text)


@router.post("/{lead_id}/follow-up", response_model=AIResult)
def follow_up(lead_id: int, payload: FollowUpRequest | None = None, db: Session = Depends(get_db)):
    lead = get_lead_or_404(lead_id, db)
    options = payload or FollowUpRequest()
    text = _run(ai.draft_follow_up, lead, options.tone, options.sender_name)
    return AIResult(lead_id=lead.id, kind="follow_up", text=text)
