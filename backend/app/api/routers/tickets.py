from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.deps import get_db
from app.auth.deps import get_current_user
from app.schemas.ticket import (
    TicketCreate, 
    TicketOut, 
    TicketAssignRequest, 
    TicketStatusRequest,
    AnalysisResult,
    EmailDraftRequest,
    EmailDraft,
    ResolutionOption
)
from app.db.models.email import Email
from app.db.models.ai_audit_log import AIAuditLog
from app.mcp import tools

router = APIRouter(prefix="/tickets", tags=["tickets"])

@router.get("", response_model=list[TicketOut])
def list_tickets(
    status: str | None = None,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    return tools.list_tickets(db, role=current["role"], user_id=UUID(current["user_id"]), status=status)

@router.post("", response_model=TicketOut)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    if current["role"] != "REQUESTER":
        raise HTTPException(status_code=403, detail="Only REQUESTER can create tickets")
    return tools.create_ticket(
        db,
        title=payload.title,
        description=payload.description,
        created_by_user_id=UUID(current["user_id"]),
    )

@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: UUID, db: Session = Depends(get_db), current=Depends(get_current_user)):
    t = tools.get_ticket(db, ticket_id)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if current["role"] == "REQUESTER" and t.created_by != UUID(current["user_id"]):
        raise HTTPException(status_code=403, detail="Not allowed")

    return t

@router.post("/{ticket_id}/assign", response_model=TicketOut)
def assign_ticket(ticket_id: UUID, payload: TicketAssignRequest, db: Session = Depends(get_db), current=Depends(get_current_user)):
    if current["role"] != "SUPPORT":
        raise HTTPException(status_code=403, detail="Only SUPPORT can assign tickets")

    assignee = tools.get_user_by_email(db, payload.assigned_to_email)
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee user not found")

    t = tools.assign_ticket(db, ticket_id=ticket_id, assigned_to_user_id=assignee.user_id)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return t

@router.post("/{ticket_id}/status", response_model=TicketOut)
def update_status(ticket_id: UUID, payload: TicketStatusRequest, db: Session = Depends(get_db), current=Depends(get_current_user)):
    if current["role"] != "SUPPORT":
        raise HTTPException(status_code=403, detail="Only SUPPORT can update status")

    try:
        t = tools.set_ticket_status(db, ticket_id=ticket_id, status=payload.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return t

# NEW AI-POWERED ENDPOINTS

@router.get("/debug/{ticket_id}")
async def debug_ticket(
    ticket_id: UUID, 
    db: Session = Depends(get_db), 
    current=Depends(get_current_user)
):
    """Debug endpoint to check ticket existence"""
    ticket = tools.get_ticket(db, ticket_id)
    return {
        "ticket_exists": ticket is not None,
        "ticket_id_input": str(ticket_id),
        "user_role": current["role"],
        "ticket_details": {
            "title": ticket.title if ticket else None,
            "status": ticket.status if ticket else None
        } if ticket else None
    }

@router.post("/{ticket_id}/analyze", response_model=AnalysisResult)
async def analyze_ticket(
    ticket_id: UUID, 
    db: Session = Depends(get_db), 
    current=Depends(get_current_user)
):
    """Analyze ticket using InsightsBuddy AI agent"""
    if current["role"] != "SUPPORT":
        raise HTTPException(status_code=403, detail="Only SUPPORT can analyze tickets")
    
    # Debug: check if ticket exists first
    ticket = tools.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    
    try:
        result = await tools.analyze_ticket_with_ai(db, ticket_id=ticket_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/{ticket_id}/draft-email", response_model=EmailDraft)
async def draft_email_response(
    ticket_id: UUID,
    payload: EmailDraftRequest,
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    """Draft email response using CommCoach AI agent"""
    if current["role"] != "SUPPORT":
        raise HTTPException(status_code=403, detail="Only SUPPORT can draft emails")
    
    # Verify ticket exists and user has access
    ticket = tools.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    try:
        print(f"Drafting email for ticket {ticket_id} with payload: {payload}")
        email_draft = await tools.draft_email_response(
            db,
            ticket_id=ticket_id,
            email_type=payload.email_type,
            tone=payload.tone,
            recipient_context=payload.recipient_context,
            created_by_user_id=UUID(current["user_id"])
        )
        print(f"Email draft created successfully: {email_draft}")
        return email_draft
    except Exception as e:
        print(f"Email drafting error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Email drafting failed: {str(e)}")

# EMAIL COMMUNICATION ENDPOINTS

@router.post("/{ticket_id}/send-email/{email_id}")
async def send_email(
    ticket_id: UUID,
    email_id: UUID, 
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    """Send/approve a drafted email to customer"""
    if current["role"] != "SUPPORT":
        raise HTTPException(status_code=403, detail="Only SUPPORT can send emails")
    
    try:
        success = await tools.approve_and_send_email(db, email_id=email_id)
        if success:
            return {"status": "Email sent successfully", "email_id": email_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to send email")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Send email failed: {str(e)}")

@router.get("/{ticket_id}/emails")
async def get_ticket_emails(
    ticket_id: UUID,
    db: Session = Depends(get_db), 
    current=Depends(get_current_user)
):
    """Get all emails/communications for a ticket"""
    ticket = tools.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check permissions - REQUESTER can only see their own tickets
    if current["role"] == "REQUESTER" and ticket.created_by != UUID(current["user_id"]):
        raise HTTPException(status_code=403, detail="Not allowed to view this ticket")
    
    emails = tools.get_ticket_emails(db, ticket_id=ticket_id)
    return {
        "ticket_id": ticket_id,
        "emails": [
            {
                "email_id": email.email_id,
                "type": email.type,
                "subject": email.subject,
                "body": email.body,
                "created_at": email.created_at,
                "is_from_customer": email.type == "CUSTOMER_REPLY",
                "is_approved": getattr(email, 'is_approved', True)
            } for email in emails if email.type in ["CUSTOMER_REPLY", "SUPPORT_UPDATE"] or (email.type == "DRAFT" and getattr(email, 'is_approved', False))
        ]
    }

@router.post("/{ticket_id}/customer-reply")
async def customer_reply(
    ticket_id: UUID,
    payload: dict,  # {"reply_text": "Thank you, but I still have issues..."}
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    """Customer replies to support communications"""
    if current["role"] != "REQUESTER":
        raise HTTPException(status_code=403, detail="Only REQUESTER can reply as customer")
    
    ticket = tools.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    # Can only reply to own tickets
    if ticket.created_by != UUID(current["user_id"]):
        raise HTTPException(status_code=403, detail="Can only reply to your own tickets")
    
    try:
        reply_email = tools.create_customer_reply(
            db,
            ticket_id=ticket_id,
            reply_text=payload["reply_text"],
            customer_user_id=UUID(current["user_id"])
        )
        
        # Also reopen ticket if it was resolved
        if ticket.status == "RESOLVED":
            tools.set_ticket_status(db, ticket_id=ticket_id, status="ASSIGNED")
        
        return {
            "email_id": reply_email.email_id,
            "message": "Reply added successfully",
            "ticket_reopened": ticket.status == "RESOLVED"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reply failed: {str(e)}")

@router.post("/{ticket_id}/customer-approve-resolution")
async def customer_approve_resolution(
    ticket_id: UUID,
    payload: dict,  # {"approved": true, "feedback": "Works perfectly now!"}
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    """Customer approves resolution and closes ticket"""
    if current["role"] != "REQUESTER":
        raise HTTPException(status_code=403, detail="Only REQUESTER can approve resolution")
    
    ticket = tools.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    # Can only approve own tickets
    if ticket.created_by != UUID(current["user_id"]):
        raise HTTPException(status_code=403, detail="Can only approve your own tickets")
    
    try:
        if payload.get("approved", False):
            # Create customer approval email
            approval_email = tools.create_customer_reply(
                db,
                ticket_id=ticket_id,
                reply_text=f"✅ Resolution Approved: {payload.get('feedback', 'Thank you for resolving this issue!')}",
                customer_user_id=UUID(current["user_id"])
            )
            
            # Mark ticket as resolved
            tools.set_ticket_status(db, ticket_id=ticket_id, status="RESOLVED")
            
            return {
                "status": "Resolution approved", 
                "ticket_status": "RESOLVED",
                "feedback_email_id": approval_email.email_id
            }
        else:
            # Customer rejected resolution
            rejection_email = tools.create_customer_reply(
                db,
                ticket_id=ticket_id,
                reply_text=f"❌ Resolution Rejected: {payload.get('feedback', 'The issue is not fully resolved yet.')}",
                customer_user_id=UUID(current["user_id"])
            )
            
            # Reopen ticket
            tools.set_ticket_status(db, ticket_id=ticket_id, status="ASSIGNED")
            
            return {
                "status": "Resolution rejected",
                "ticket_status": "ASSIGNED", 
                "feedback_email_id": rejection_email.email_id
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approval failed: {str(e)}")

@router.get("/{ticket_id}/ai-audit-log")
async def get_ai_audit_log(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    """Get AI audit logs for a ticket"""
    if current["role"] != "SUPPORT":
        raise HTTPException(status_code=403, detail="Only SUPPORT can view audit logs")
    
    logs = tools.get_ai_audit_logs(db, ticket_id=ticket_id)
    return {
        "ticket_id": ticket_id,
        "audit_logs": [
            {
                "ai_event_id": log.ai_event_id,
                "agent_name": log.agent_name,
                "model_name": log.model_name,
                "confidence_json": log.confidence_json,
                "was_used": log.was_used,
                "created_at": log.created_at
            } for log in logs
        ]
    }

@router.get("/{ticket_id}/emails")
async def get_ticket_emails(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    """Get all email drafts and approved emails for a ticket"""
    # Verify ticket exists and user has access
    ticket = tools.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if current["role"] == "REQUESTER" and ticket.created_by != UUID(current["user_id"]):
        raise HTTPException(status_code=403, detail="Not allowed")
    
    emails = tools.get_ticket_emails(db, ticket_id=ticket_id)
    return emails

@router.post("/emails/{email_id}/approve")
async def approve_email(
    email_id: UUID,
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    """Approve and send email"""
    if current["role"] != "SUPPORT":
        raise HTTPException(status_code=403, detail="Only SUPPORT can approve emails")
    
    success = await tools.approve_and_send_email(db, email_id=email_id)
    if not success:
        raise HTTPException(status_code=404, detail="Email not found or approval failed")
    
    return {"message": "Email approved and sent successfully"}

@router.get("/{ticket_id}/audit-logs")
async def get_ticket_audit_logs(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    """Get AI audit logs for a ticket"""
    if current["role"] != "SUPPORT":
        raise HTTPException(status_code=403, detail="Only SUPPORT can view audit logs")
    
    # Verify ticket exists
    ticket = tools.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    audit_logs = tools.get_ai_audit_logs(db, ticket_id=ticket_id)
    return audit_logs

@router.post("/audit-logs/{audit_log_id}/mark-used")
async def mark_resolution_used(
    audit_log_id: UUID,
    was_successful: bool,
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    """Mark a resolution as used and track its success"""
    if current["role"] != "SUPPORT":
        raise HTTPException(status_code=403, detail="Only SUPPORT can update audit logs")
    
    success = await tools.mark_resolution_used(
        db, 
        audit_log_id=audit_log_id, 
        was_successful=was_successful
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    return {"message": "Resolution marked as used successfully"}