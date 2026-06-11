import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from database import Base


class AlignmentResult(Base):
    __tablename__ = "alignment_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="pending")
    word_alignments = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
