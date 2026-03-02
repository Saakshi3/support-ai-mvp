from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime
from app.db.models.user import User
from app.db.models.ticket import Ticket
from app.db.models.historical_incident import HistoricalIncident
from app.db.models.email import Email
from app.db.models.ai_audit_log import AIAuditLog
from app.agents.insights_buddy import insights_buddy
from app.agents.comm_coach import comm_coach
from app.schemas.ticket import (
    TicketAnalysisRequest, 
    EmailDraftRequest, 
    ResolutionOption,
    AnalysisResult,
    EmailDraft
)

ALLOWED_TICKET_STATUSES = {"NEW", "ASSIGNED", "RESOLVED"}

# Existing user and ticket management functions
def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def ensure_user(db: Session, *, email: str, display_name: str, role: str) -> User:
    # role must match DB constraint: REQUESTER|SUPPORT
    u = get_user_by_email(db, email)
    if u:
        return u
    u = User(email=email, display_name=display_name, role=role)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

def create_ticket(db: Session, *, title: str, description: str, created_by_user_id):
    t = Ticket(title=title, description=description, status="NEW", created_by=created_by_user_id)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

def list_tickets(db: Session, *, role: str, user_id, status: str | None = None):
    q = db.query(Ticket)
    if role == "REQUESTER":
        q = q.filter(Ticket.created_by == user_id)
    if status:
        q = q.filter(Ticket.status == status)
    return q.order_by(Ticket.created_at.desc()).all()

def get_ticket(db: Session, ticket_id):
    return db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()

def assign_ticket(db: Session, *, ticket_id, assigned_to_user_id):
    t = get_ticket(db, ticket_id)
    if not t:
        return None
    t.assigned_to = assigned_to_user_id
    t.status = "ASSIGNED"
    db.commit()
    db.refresh(t)
    return t

def set_ticket_status(db: Session, *, ticket_id, status: str):
    if status not in ALLOWED_TICKET_STATUSES:
        raise ValueError(f"Invalid status. Allowed: {sorted(ALLOWED_TICKET_STATUSES)}")
    t = get_ticket(db, ticket_id)
    if not t:
        return None
    t.status = status
    db.commit()
    db.refresh(t)
    return t

# New AI-powered MCP tools
async def analyze_ticket_with_ai(db: Session, *, ticket_id: uuid.UUID) -> AnalysisResult:
    """
    MCP Tool: Analyze a ticket using InsightsBuddy AI agent
    Returns resolution suggestions based on historical incidents
    """
    try:
        # Get the ticket
        ticket = get_ticket(db, ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        # Create analysis request
        analysis_request = TicketAnalysisRequest(
            ticket_id=ticket.ticket_id,
            title=ticket.title,
            description=ticket.description
        )
        
        # Rollback any pending transaction to start fresh
        try:
            db.rollback()
        except:
            pass
            
        # Run AI analysis
        result = await insights_buddy.analyze_ticket(analysis_request, db)
        return result
        
    except Exception as e:
        print(f"Error in analyze_ticket_with_ai: {str(e)}")
        # Make sure to rollback on any error
        try:
            db.rollback()
        except:
            pass
        raise e

async def draft_email_response(db: Session, *, 
                             ticket_id: uuid.UUID,
                             email_type: str,
                             tone: str = "professional",
                             recipient_context: str = "customer",
                             created_by_user_id: uuid.UUID) -> EmailDraft:
    """
    MCP Tool: Draft an email response using CommCoach AI agent
    Returns a professional email draft based on ticket analysis
    """
    try:
        # Get the ticket
        ticket = get_ticket(db, ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        # Create email draft request
        draft_request = EmailDraftRequest(
            email_type=email_type,
            tone=tone,
            recipient_context=recipient_context
        )
        
        # Generate email draft
        email_draft = await comm_coach.draft_email(
            ticket, draft_request, created_by_user_id, db
        )
        
        return email_draft
        
    except Exception as e:
        print(f"Error in draft_email_response: {str(e)}")
        raise e

async def approve_and_send_email(db: Session, *, email_id: uuid.UUID) -> bool:
    """
    MCP Tool: Approve and send an email draft
    Marks the email as approved and triggers sending (integration point for email service)
    """
    try:
        return await comm_coach.approve_and_send_email(email_id, db)
    except Exception as e:
        print(f"Error in approve_and_send_email: {str(e)}")
        return False

def get_ticket_emails(db: Session, *, ticket_id: uuid.UUID) -> List[Email]:
    """
    MCP Tool: Get all emails for a ticket
    Returns both draft and approved emails
    """
    try:
        return db.query(Email).filter(Email.ticket_id == ticket_id).order_by(Email.created_at.desc()).all()
    except Exception as e:
        print(f"Error in get_ticket_emails: {str(e)}")
        return []

def create_customer_reply(
    db: Session, 
    *, 
    ticket_id: uuid.UUID, 
    reply_text: str, 
    customer_user_id: uuid.UUID
) -> Email:
    """
    MCP Tool: Create customer reply email
    """
    try:
        # Create email object for customer reply
        customer_email = Email(
            email_id=uuid.uuid4(),
            ticket_id=ticket_id,
            type="CUSTOMER_REPLY",
            subject=f"Re: Support Ticket #{str(ticket_id)[:8]}",
            body=reply_text,
            tone="customer",
            audience="support_team",
            is_approved=True,  # Customer replies are auto-approved
            created_by=customer_user_id,
            approved_by=None
        )
        
        db.add(customer_email)
        db.commit()
        db.refresh(customer_email)
        
        return customer_email
        
    except Exception as e:
        db.rollback()
        print(f"Error in create_customer_reply: {str(e)}")
        raise e

def set_ticket_status(db: Session, *, ticket_id: uuid.UUID, status: str) -> bool:
    """
    MCP Tool: Update ticket status
    """
    try:
        ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if ticket:
            ticket.status = status
            ticket.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error in set_ticket_status: {str(e)}")
        return False

def get_ai_audit_logs(db: Session, *, 
                     ticket_id: Optional[uuid.UUID] = None,
                     agent_name: Optional[str] = None) -> List[AIAuditLog]:
    """
    MCP Tool: Get AI audit logs for monitoring and compliance
    Can filter by ticket_id and/or agent_name
    """
    try:
        query = db.query(AIAuditLog)
        
        if ticket_id:
            query = query.filter(AIAuditLog.ticket_id == ticket_id)
        
        if agent_name:
            query = query.filter(AIAuditLog.agent_name == agent_name)
        
        return query.order_by(AIAuditLog.created_at.desc()).all()
        
    except Exception as e:
        print(f"Error in get_ai_audit_logs: {str(e)}")
        return []

def create_historical_incident(db: Session, *, 
                             problem_text: str,
                             resolution_text: str,
                             root_cause: Optional[str] = None,
                             outcome: Optional[str] = None) -> HistoricalIncident:
    """
    MCP Tool: Create a historical incident for future AI training
    This would typically be called when a ticket is resolved successfully
    """
    try:
        incident = HistoricalIncident(
            problem_text=problem_text,
            resolution_text=resolution_text,
            root_cause=root_cause,
            outcome=outcome
            # embedding will be generated separately via background job
        )
        
        db.add(incident)
        db.commit()
        db.refresh(incident)
        
        return incident
        
    except Exception as e:
        print(f"Error in create_historical_incident: {str(e)}")
        db.rollback()
        raise e

def get_similar_incidents(db: Session, *, 
                         problem_text: str,
                         limit: int = 5) -> List[HistoricalIncident]:
    """
    MCP Tool: Find similar historical incidents using text-based search
    This is a simpler version that doesn't require embeddings
    """
    try:
        # Simple text-based search using PostgreSQL full-text search
        from sqlalchemy import func
        
        query = db.query(HistoricalIncident).filter(
            func.lower(HistoricalIncident.problem_text).contains(func.lower(problem_text))
        ).limit(limit)
        
        return query.all()
        
    except Exception as e:
        print(f"Error in get_similar_incidents: {str(e)}")
        return []

async def mark_resolution_used(db: Session, *, 
                             audit_log_id: uuid.UUID,
                             was_successful: bool) -> bool:
    """
    MCP Tool: Mark a resolution as used and track its success
    This helps improve AI recommendations over time
    """
    try:
        audit_log = db.query(AIAuditLog).filter(AIAuditLog.ai_event_id == audit_log_id).first()
        if not audit_log:
            return False
        
        audit_log.was_used = True
        if audit_log.confidence_json is None:
            audit_log.confidence_json = {}
        
        audit_log.confidence_json["resolution_success"] = was_successful
        
        db.commit()
        return True
        
    except Exception as e:
        print(f"Error in mark_resolution_used: {str(e)}")
        db.rollback()
        return False