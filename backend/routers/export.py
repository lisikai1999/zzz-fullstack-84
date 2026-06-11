from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Subtitle
from services.export_service import export_srt, export_vtt, export_ass

router = APIRouter()


@router.get("/{project_id}/export")
async def export_subtitles(
    project_id: str,
    format: str = Query(default="srt", pattern="^(srt|vtt|ass)$"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subtitle)
        .where(Subtitle.project_id == project_id)
        .order_by(Subtitle.index)
    )
    subtitles = result.scalars().all()
    if not subtitles:
        raise HTTPException(status_code=404, detail="No subtitles found")

    items = [
        {"index": s.index, "text": s.text, "start_time": s.start_time, "end_time": s.end_time}
        for s in subtitles
    ]

    if format == "srt":
        content = export_srt(items)
        media_type = "application/x-subrip"
    elif format == "vtt":
        content = export_vtt(items)
        media_type = "text/vtt"
    else:
        content = export_ass(items)
        media_type = "text/x-ssa"

    return PlainTextResponse(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=subtitles.{format}"},
    )
