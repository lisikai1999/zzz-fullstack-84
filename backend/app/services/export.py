import json
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.subtitle import SubtitleLine


router = APIRouter(tags=["export"])


@router.get("/api/projects/{project_id}/export")
def export_subtitles(project_id: int, format: str = "srt", db: Session = Depends(get_db)):
    subs = db.query(SubtitleLine).filter(
        SubtitleLine.project_id == project_id
    ).order_by(SubtitleLine.index).all()

    if not subs:
        raise HTTPException(status_code=404, detail="No subtitles to export")

    if format == "srt":
        content = generate_srt(subs)
        media_type = "text/plain"
        filename = "subtitles.srt"
    elif format == "ass":
        content = generate_ass(subs)
        media_type = "text/plain"
        filename = "subtitles.ass"
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'srt' or 'ass'.")

    return StreamingResponse(
        StringIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def generate_srt(subtitles: list) -> str:
    lines = []
    for sub in subtitles:
        lines.append(str(sub.index))
        lines.append(f"{_format_srt_time(sub.start_time)} --> {_format_srt_time(sub.end_time)}")
        lines.append(sub.text)
        lines.append("")
    return "\n".join(lines)


def generate_ass(subtitles: list) -> str:
    header = """[Script Info]
Title: Subtitle Alignment Tool Export
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei,56,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header.strip()]
    for sub in subtitles:
        start = _format_ass_time(sub.start_time)
        end = _format_ass_time(sub.end_time)
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{sub.text}")
    return "\n".join(lines) + "\n"


def _format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
