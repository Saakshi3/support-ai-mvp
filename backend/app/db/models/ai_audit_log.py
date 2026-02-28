import uuid
from sqlalchemy import Column, Text, DateTime, ForeignKey, Boolean, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.base import Base

class AIAuditLog(Base):
    __tablename__ = "ai_audit_log"

    ai_event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.ticket_id", ondelete="SET NULL"), nullable=True)
    agent_name = Column(Text, nullable=False)  # InsightsBuddy | CommCoach
    model_name = Column(Text, nullable=True)
    input_json = Column(JSONB, nullable=False)
    output_json = Column(JSONB, nullable=False)
    confidence_json = Column(JSONB, nullable=True)
    supporting_incident_ids = Column(ARRAY(UUID), nullable=True)
    was_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)