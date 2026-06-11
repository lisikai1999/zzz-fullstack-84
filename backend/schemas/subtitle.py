from typing import List, Optional

from pydantic import BaseModel


class SubtitleItem(BaseModel):
    id: Optional[str] = None
    index: int
    text: str
    start_time: float
    end_time: float

    class Config:
        from_attributes = True


class SubtitleListResponse(BaseModel):
    subtitles: List[SubtitleItem]


class SubtitleUpdate(BaseModel):
    subtitles: List[SubtitleItem]


class SplitConfig(BaseModel):
    max_chars: int = 20
    pause_threshold_ms: float = 300.0
