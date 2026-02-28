import uuid
from sqlalchemy import Column, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.db.base import Base

class HistoricalIncident(Base):
    __tablename__ = "historical_incidents"

    incident_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_text = Column(Text, nullable=False)
    resolution_text = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=True)
    outcome = Column(Text, nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

# Create HNSW index for vector similarity search
Index(
    'historical_incidents_embedding_idx',
    HistoricalIncident.embedding,
    postgresql_using='hnsw',
    postgresql_with={'m': 16, 'ef_construction': 64},
    postgresql_ops={'embedding': 'vector_cosine_ops'}
)