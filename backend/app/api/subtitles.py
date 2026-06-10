import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.subtitle import SubtitleLine
from app.schemas.subtitle import SubtitleResponse, SubtitleUpdate, SubtitleBulkUpdate, SegmentationParams, WordTimestamp
from app.services.segmentation import segment_words

router = APIRouter(prefix="/api/projects/{project_id}/subtitles", tags=["subtitles"])


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


@router.get("", response_model=list[SubtitleResponse])
def get_subtitles(project_id: int, db: Session = Depends(get_db)):
    subs = db.query(SubtitleLine).filter(
        SubtitleLine.project_id == project_id
    ).order_by(SubtitleLine.index).all()
    return [_to_response(s) for s in subs]


@router.put("/{line_id}", response_model=SubtitleResponse)
def update_subtitle(project_id: int, line_id: int, data: SubtitleUpdate, db: Session = Depends(get_db)):
    sub = db.query(SubtitleLine).filter(
        SubtitleLine.id == line_id, SubtitleLine.project_id == project_id
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subtitle not found")
    if data.text is not None:
        sub.text = data.text
    if data.start_time is not None:
        sub.start_time = data.start_time
    if data.end_time is not None:
        sub.end_time = data.end_time
    db.commit()
    db.refresh(sub)
    return _to_response(sub)


@router.put("/bulk", response_model=list[SubtitleResponse])
def bulk_update_subtitles(project_id: int, data: SubtitleBulkUpdate, db: Session = Depends(get_db)):
    results = []
    for item in data.subtitles:
        sub = db.query(SubtitleLine).filter(
            SubtitleLine.id == item["id"], SubtitleLine.project_id == project_id
        ).first()
        if sub:
            if "text" in item:
                sub.text = item["text"]
            if "start_time" in item:
                sub.start_time = item["start_time"]
            if "end_time" in item:
                sub.end_time = item["end_time"]
            results.append(sub)
    db.commit()
    return [_to_response(s) for s in results]


@router.post("/segment", response_model=list[SubtitleResponse])
def resegment(project_id: int, params: SegmentationParams, db: Session = Depends(get_db)):
    subs = db.query(SubtitleLine).filter(
        SubtitleLine.project_id == project_id
    ).order_by(SubtitleLine.index).all()

    all_words = []
    for sub in subs:
        if sub.words_json:
            all_words.extend(json.loads(sub.words_json))

    if not all_words:
        raise HTTPException(status_code=400, detail="No word-level data available for re-segmentation")

    segments = segment_words(all_words, max_chars=params.max_chars, min_pause=params.min_pause)

    db.query(SubtitleLine).filter(SubtitleLine.project_id == project_id).delete()

    new_subs = []
    for i, seg in enumerate(segments, 1):
        sub = SubtitleLine(
            project_id=project_id,
            index=i,
            text=seg["text"],
            start_time=seg["start_time"],
            end_time=seg["end_time"],
            words_json=json.dumps(seg["words"], ensure_ascii=False),
        )
        db.add(sub)
        new_subs.append(sub)

    db.commit()
    for s in new_subs:
        db.refresh(s)
    return [_to_response(s) for s in new_subs]
