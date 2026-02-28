import uuid
from sqlalchemy import Column, Text, DateTime, Boolean, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.base import Base

class Resolution(Base):
    __tablename__ = "resolutions"

    resolution_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False)
    resolution_text = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=True)
    outcome = Column(Text, nullable=True)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    reasoning = Column(Text, nullable=True)
    is_final = Column(Boolean, default=False)
    is_kb = Column(Boolean, default=False)
    embedding = Column(Vector(1536), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    ticket = relationship("Ticket", back_populates="resolutions")
    creator = relationship("User", foreign_keys=[created_by])

# The HNSW index is already created in the database