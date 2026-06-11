import uuid

from sqlalchemy import Column, String, Integer, Text, Float, ForeignKey
from database import Base


class Subtitle(Base):
    __tablename__ = "subtitles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
