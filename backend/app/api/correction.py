import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.subtitle import SubtitleLine
from app.schemas.correction import ShiftRequest, ScaleRequest, PropagateRequest
from app.schemas.subtitle import SubtitleResponse, WordTimestamp
from app.services.correction import apply_global_shift, apply_linear_scale, adjust_with_propagation

router = APIRouter(prefix="/api/projects/{project_id}/correct", tags=["correction"])


def _to_response(sub: SubtitleLine) -> SubtitleResponse:
    words = None
    if sub.words_json:
        words = [WordTimestamp(**w) for w in json.loads(sub.words_json)]
    return SubtitleResponse(
        id=sub.id,
        project_id=sub.project_id,
        index=sub.index,
        text=sub.text,
        start_time=sub.start_time,
        end_time=sub.end_time,
        words=words,
    )


@router.post("/shift", response_model=list[SubtitleResponse])
def shift_subtitles(project_id: int, data: ShiftRequest, db: Session = Depends(get_db)):
    subs = db.query(SubtitleLine).filter(
        SubtitleLine.project_id == project_id
    ).order_by(SubtitleLine.index).all()
    if not subs:
        raise HTTPException(status_code=404, detail="No subtitles found")

    apply_global_shift(subs, data.offset_ms / 1000.0)
    db.commit()
    return [_to_response(s) for s in subs]


@router.post("/scale", response_model=list[SubtitleResponse])
def scale_subtitles(project_id: int, data: ScaleRequest, db: Session = Depends(get_db)):
    subs = db.query(SubtitleLine).filter(
        SubtitleLine.project_id == project_id
    ).order_by(SubtitleLine.index).all()
    if not subs:
        raise HTTPException(status_code=404, detail="No subtitles found")

    apply_linear_scale(subs, data.factor, data.anchor_time)
    db.commit()
    return [_to_response(s) for s in subs]


@router.post("/propagate", response_model=list[SubtitleResponse])
def propagate_adjustment(project_id: int, data: PropagateRequest, db: Session = Depends(get_db)):
    subs = db.query(SubtitleLine).filter(
        SubtitleLine.project_id == project_id
    ).order_by(SubtitleLine.index).all()
    if not subs:
        raise HTTPException(status_code=404, detail="No subtitles found")

    adjust_with_propagation(subs, data.line_id, data.new_start, data.new_end)
    db.commit()
    return [_to_response(s) for s in subs]
