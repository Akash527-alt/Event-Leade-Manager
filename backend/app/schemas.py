"""Pydantic request/response schemas."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

Status = Literal["not_contacted", "contacted", "replied", "meeting_booked", "closed"]
Tone = Literal["friendly", "professional", "concise"]

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Company = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
Event = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)]


class LeadCreate(BaseModel):
    name: Name
    company: Company
    email: EmailStr
    event: Event
    notes: Notes = ""
    status: Status = "not_contacted"


class LeadUpdate(BaseModel):
    """Partial update: only fields that are sent get changed."""

    name: Name | None = None
    company: Company | None = None
    email: EmailStr | None = None
    event: Event | None = None
    notes: Notes | None = None
    status: Status | None = None


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company: str
    email: str
    event: str
    notes: str
    status: Status
    created_at: datetime
    updated_at: datetime


class LeadList(BaseModel):
    items: list[LeadOut]
    total: int


class FollowUpRequest(BaseModel):
    tone: Tone = "friendly"
    sender_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] = Field(
        default="", description="Optional name to sign the email with."
    )


class AIResult(BaseModel):
    lead_id: int
    kind: Literal["summary", "follow_up"]
    text: str
