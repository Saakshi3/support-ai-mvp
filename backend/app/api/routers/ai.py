from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel

from app.deps import get_db
from app.auth.deps import get_current_user
from app.db.models.historical_incident import HistoricalIncident
from app.db.models.ai_audit_log import AIAuditLog
from app.mcp import tools

router = APIRouter(prefix="/ai", tags=["ai"])

class CreateHistoricalIncidentRequest(BaseModel):
    problem_text: str
    resolution_text: str
    root_cause: Optional[str] = None
    outcome: Optional[str] = None

class HistoricalIncidentResponse(BaseModel):
    incident_id: UUID
    problem_text: str
    resolution_text: str
    root_cause: Optional[str]
    outcome: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True

class SimilarIncidentsRequest(BaseModel):
    problem_text: str
    limit: int = 5

@router.post("/historical-incidents", response_model=HistoricalIncidentResponse)
def create_historical_incident(
    payload: CreateHistoricalIncidentRequest,
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    """Create a new historical incident for AI training"""
    if current["role"] != "SUPPORT":
        raise HTTPException(status_code=403, detail="Only SUPPORT can create historical incidents")
    
    try:
        incident = tools.create_historical_incident(
            db,
            problem_text=payload.problem_text,
            resolution_text=payload.resolution_text,
            root_cause=payload.root_cause,
            outcome=payload.outcome
        )
        return incident
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create incident: {str(e)}")

@router.get("/historical-incidents", response_model=List[HistoricalIncidentResponse])
def list_historical_incidents(
    limit: int = 20,
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    """List historical incidents"""
    if current["role"] != "SUPPORT":
        raise HTTPException(status_code=403, detail="Only SUPPORT can view historical incidents")
    
    incidents = db.query(HistoricalIncident).order_by(
        HistoricalIncident.created_at.desc()
    ).limit(limit).all()
    
    return incidents

@router.post("/similar-incidents", response_model=List[HistoricalIncidentResponse])
def find_similar_incidents(
    payload: SimilarIncidentsRequest,
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    """Find similar incidents using text search"""
    if current["role"] != "SUPPORT":
        raise HTTPException(status_code=403, detail="Only SUPPORT can search incidents")
    
    incidents = tools.get_similar_incidents(
        db,
        problem_text=payload.problem_text,
        limit=payload.limit
    )
    
    return incidents

@router.get("/audit-logs", response_model=List[dict])
def list_audit_logs(
    agent_name: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    """List AI audit logs for monitoring and compliance"""
    if current["role"] != "SUPPORT":
        raise HTTPException(status_code=403, detail="Only SUPPORT can view audit logs")
    
    query = db.query(AIAuditLog)
    
    if agent_name:
        query = query.filter(AIAuditLog.agent_name == agent_name)
    
    audit_logs = query.order_by(AIAuditLog.created_at.desc()).limit(limit).all()
    
    # Convert to dict format for API response
    result = []
    for log in audit_logs:
        result.append({
            "ai_event_id": log.ai_event_id,
            "ticket_id": log.ticket_id,
            "agent_name": log.agent_name,
            "model_name": log.model_name,
            "input_json": log.input_json,
            "output_json": log.output_json,
            "confidence_json": log.confidence_json,
            "supporting_incident_ids": log.supporting_incident_ids,
            "was_used": log.was_used,
            "created_at": log.created_at.isoformat()
        })
    
    return result

@router.get("/statistics")
def get_ai_statistics(
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    """Get AI usage statistics"""
    if current["role"] != "SUPPORT":
        raise HTTPException(status_code=403, detail="Only SUPPORT can view statistics")
    
    try:
        # Get basic counts
        total_incidents = db.query(HistoricalIncident).count()
        total_analyses = db.query(AIAuditLog).filter(
            AIAuditLog.agent_name == "InsightsBuddy"  
        ).count()
        total_emails = db.query(AIAuditLog).filter(
            AIAuditLog.agent_name == "CommCoach"
        ).count()
        
        # Get successful resolutions
        successful_resolutions = db.query(AIAuditLog).filter(
            AIAuditLog.was_used == True,
            AIAuditLog.confidence_json.contains({"resolution_success": True})
        ).count()
        
        # Calculate average confidence scores
        insights_logs = db.query(AIAuditLog).filter(
            AIAuditLog.agent_name == "InsightsBuddy",
            AIAuditLog.confidence_json.isnot(None)
        ).all()
        
        avg_confidence = 0.0
        if insights_logs:
            confidences = [
                log.confidence_json.get("avg_confidence", 0.0) 
                for log in insights_logs 
                if log.confidence_json.get("avg_confidence") is not None
            ]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
        
        return {
            "total_historical_incidents": total_incidents,
            "total_ai_analyses": total_analyses,
            "total_email_drafts": total_emails,
            "successful_resolutions": successful_resolutions,
            "average_confidence_score": round(avg_confidence, 3),
            "success_rate": round(successful_resolutions / max(total_analyses, 1) * 100, 1)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")