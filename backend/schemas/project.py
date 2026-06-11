from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    language: str = "zh"


class ProjectResponse(BaseModel):
    id: str
    name: str
    audio_path: Optional[str] = None
    transcript: Optional[str] = None
    language: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
