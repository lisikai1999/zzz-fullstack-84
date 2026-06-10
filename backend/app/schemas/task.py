from datetime import datetime
from pydantic import BaseModel


class TaskResponse(BaseModel):
    id: str
    project_id: int
    status: str
    progress: float
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
