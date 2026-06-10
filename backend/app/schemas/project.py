from datetime import datetime
from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str


class ProjectUpdate(BaseModel):
    name: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    audio_path: str | None
    transcript_path: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
