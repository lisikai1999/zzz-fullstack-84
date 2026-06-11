from typing import List, Optional, Literal

from pydantic import BaseModel


class AnchorPoint(BaseModel):
    subtitle_index: int
    correct_start: float


class CorrectionRequest(BaseModel):
    mode: Literal["global_shift", "linear_scale", "single_cascade", "anchor_interpolation"]
    offset_ms: Optional[float] = None
    scale_factor: Optional[float] = None
    scale_offset: Optional[float] = None
    anchor_index: Optional[int] = None
    new_start: Optional[float] = None
    anchors: Optional[List[AnchorPoint]] = None
