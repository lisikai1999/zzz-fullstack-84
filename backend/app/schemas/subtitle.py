from datetime import datetime
from pydantic import BaseModel


class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float


class SubtitleResponse(BaseModel):
    id: int
    project_id: int
    index: int
    text: str
    start_time: float
    end_time: float
    words: list[WordTimestamp] | None = None

    model_config = {"from_attributes": True}


class SubtitleUpdate(BaseModel):
    text: str | None = None
    start_time: float | None = None
    end_time: float | None = None


class SubtitleBulkUpdate(BaseModel):
    subtitles: list[dict]


class SegmentationParams(BaseModel):
    max_chars: int = 18
    min_pause: float = 0.3
