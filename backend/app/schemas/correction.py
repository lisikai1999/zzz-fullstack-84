from pydantic import BaseModel


class ShiftRequest(BaseModel):
    offset_ms: float


class ScaleRequest(BaseModel):
    factor: float
    anchor_time: float = 0.0


class PropagateRequest(BaseModel):
    line_id: int
    new_start: float
    new_end: float
