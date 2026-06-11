from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class WordAlignment(BaseModel):
    char: str
    start: float
    end: float
    confidence: float = 1.0


class AlignmentResponse(BaseModel):
    id: str
    project_id: str
    status: str
    word_alignments: Optional[List[WordAlignment]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlignmentTriggerResponse(BaseModel):
    id: str
    status: str
    message: str
