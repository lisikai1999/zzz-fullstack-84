import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Project, AlignmentResult, Subtitle
from schemas import SubtitleItem, SubtitleListResponse, SubtitleUpdate, SplitConfig
from schemas.correction import CorrectionRequest
from services.splitting_service import split_alignment_to_subtitles
from services.correction_service import apply_correction

router = APIRouter()


@router.post("/{project_id}/split", response_model=SubtitleListResponse)
async def split_subtitles(
    project_id: str,
    config: SplitConfig = SplitConfig(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlignmentResult)
        .where(AlignmentResult.project_id == project_id)
        .order_by(AlignmentResult.created_at.desc())
    )
    alignment = result.scalars().first()
    if not alignment or not alignment.word_alignments:
        raise HTTPException(status_code=400, detail="No alignment result available")

    subtitles_data = split_alignment_to_subtitles(
        alignment.word_alignments,
        max_chars=config.max_chars,
        pause_threshold_ms=config.pause_threshold_ms,
    )

    await db.execute(delete(Subtitle).where(Subtitle.project_id == project_id))

    subtitles = []
    for i, item in enumerate(subtitles_data):
        sub = Subtitle(
            id=str(uuid.uuid4()),
            project_id=project_id,
            index=i + 1,
            text=item["text"],
            start_time=item["start_time"],
            end_time=item["end_time"],
        )
        db.add(sub)
        subtitles.append(sub)

    project = await db.get(Project, project_id)
    if project:
        project.status = "split"
    await db.commit()

    return SubtitleListResponse(
        subtitles=[SubtitleItem.model_validate(s) for s in subtitles]
    )


@router.get("/{project_id}/subtitles", response_model=SubtitleListResponse)
async def get_subtitles(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subtitle)
        .where(Subtitle.project_id == project_id)
        .order_by(Subtitle.index)
    )
    subtitles = result.scalars().all()
    return SubtitleListResponse(
        subtitles=[SubtitleItem.model_validate(s) for s in subtitles]
    )


@router.put("/{project_id}/subtitles", response_model=SubtitleListResponse)
async def update_subtitles(
    project_id: str, data: SubtitleUpdate, db: AsyncSession = Depends(get_db)
):
    await db.execute(delete(Subtitle).where(Subtitle.project_id == project_id))

    subtitles = []
    for item in data.subtitles:
        sub = Subtitle(
            id=str(uuid.uuid4()),
            project_id=project_id,
            index=item.index,
            text=item.text,
            start_time=item.start_time,
            end_time=item.end_time,
        )
        db.add(sub)
        subtitles.append(sub)

    await db.commit()
    return SubtitleListResponse(
        subtitles=[SubtitleItem.model_validate(s) for s in subtitles]
    )


@router.post("/{project_id}/correct", response_model=SubtitleListResponse)
async def correct_subtitles(
    project_id: str, req: CorrectionRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Subtitle)
        .where(Subtitle.project_id == project_id)
        .order_by(Subtitle.index)
    )
    subtitles = result.scalars().all()
    if not subtitles:
        raise HTTPException(status_code=400, detail="No subtitles to correct")

    items = [
        {"index": s.index, "text": s.text, "start_time": s.start_time, "end_time": s.end_time}
        for s in subtitles
    ]
    corrected = apply_correction(items, req)

    await db.execute(delete(Subtitle).where(Subtitle.project_id == project_id))
    new_subs = []
    for item in corrected:
        sub = Subtitle(
            id=str(uuid.uuid4()),
            project_id=project_id,
            index=item["index"],
            text=item["text"],
            start_time=item["start_time"],
            end_time=item["end_time"],
        )
        db.add(sub)
        new_subs.append(sub)

    await db.commit()
    return SubtitleListResponse(
        subtitles=[SubtitleItem.model_validate(s) for s in new_subs]
    )
