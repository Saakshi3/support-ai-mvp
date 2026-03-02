from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class TicketCreate(BaseModel):
    title: str
    description: str

class TicketOut(BaseModel):
    ticket_id: UUID
    title: str
    description: str
    status: str
    created_by: Optional[UUID]
    assigned_to: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TicketAssignRequest(BaseModel):
    assigned_to_email: str

class TicketStatusRequest(BaseModel):
    status: str  # NEW|ASSIGNED|RESOLVED

# AI Analysis Schemas
class TicketAnalysisRequest(BaseModel):
    ticket_id: UUID
    title: str
    description: str

class ResolutionOption(BaseModel):
    title: str
    description: str
    confidence_score: float
    reasoning: str
    estimated_time: str
    risk_level: str  # low|medium|high

class AnalysisResult(BaseModel):
    ticket_id: UUID
    category: Optional[str] = "general_support"
    reasoning: Optional[str] = "Analysis completed using pattern matching"
    confidence_score: float = 0.8
    resolution_options: List[ResolutionOption]
    similar_incidents_count: int
    escalation_recommended: bool = False
    analysis_timestamp: datetime
    audit_log_id: Optional[UUID] = None

class EmailDraftRequest(BaseModel):
    email_type: str  # UPDATE | RESOLUTION | ESCALATION
    tone: str = "professional"  # professional | friendly | formal
    recipient_context: str = "customer"  # customer | internal | executive
    
class EmailDraft(BaseModel):
    email_id: Optional[UUID] = None
    subject: str
    body: str
    confidence_score: float
    draft_reasoning: str