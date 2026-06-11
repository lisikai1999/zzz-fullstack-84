import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Enum
from database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    audio_path = Column(String(500), nullable=True)
    transcript = Column(Text, nullable=True)
    language = Column(String(10), default="zh")
    status = Column(String(20), default="created")
    created_at = Column(DateTime, default=datetime.utcnow)
