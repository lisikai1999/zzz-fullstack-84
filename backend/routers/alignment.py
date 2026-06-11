import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Project, AlignmentResult
from schemas import AlignmentResponse, AlignmentTriggerResponse
from services.alignment_service import check_stable_ts
from tasks.alignment_task import run_alignment_task, progress_store

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=2)


@router.get("/alignment/status")
async def alignment_engine_status():
    """Check whether the alignment engine (stable-ts + whisper) is installed."""
    available = check_stable_ts()
    if available:
        return {"available": True, "message": "对齐引擎就绪"}
    return {
        "available": False,
        "message": "对齐引擎未安装。请在后端服务器执行: pip install stable-ts openai-whisper",
    }


@router.post("/{project_id}/align", response_model=AlignmentTriggerResponse)
async def trigger_alignment(project_id: str, db: AsyncSession = Depends(get_db)):
    if not check_stable_ts():
        raise HTTPException(
            status_code=503,
            detail="对齐引擎未安装。请在后端执行: pip install stable-ts openai-whisper",
        )

    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.audio_path or not project.transcript:
        raise HTTPException(status_code=400, detail="Audio and transcript required")

    alignment = AlignmentResult(
        id=str(uuid.uuid4()),
        project_id=project_id,
        status="processing",
    )
    db.add(alignment)
    project.status = "aligning"
    await db.commit()

    executor.submit(
        run_alignment_task,
        alignment.id,
        project_id,
        project.audio_path,
        project.transcript,
        project.language,
    )

    return AlignmentTriggerResponse(
        id=alignment.id, status="processing", message="Alignment started"
    )


@router.get("/{project_id}/alignment", response_model=AlignmentResponse)
async def get_alignment(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AlignmentResult)
        .where(AlignmentResult.project_id == project_id)
        .order_by(AlignmentResult.created_at.desc())
    )
    alignment = result.scalars().first()
    if not alignment:
        raise HTTPException(status_code=404, detail="No alignment found")
    return alignment


@router.get("/{project_id}/alignment/progress")
async def get_alignment_progress(project_id: str):
    progress = progress_store.get(project_id)
    if not progress:
        return {"percent": 0, "stage": "unknown"}
    return progress


@router.get("/{project_id}/waveform")
async def get_waveform(project_id: str, db: AsyncSession = Depends(get_db)):
    from services.waveform_service import generate_waveform_peaks, get_waveform_metadata

    project = await db.get(Project, project_id)
    if not project or not project.audio_path:
        raise HTTPException(status_code=404, detail="Audio not found")

    metadata = get_waveform_metadata(project.audio_path)
    peaks = generate_waveform_peaks(project.audio_path)
    return {"metadata": metadata, "peaks": peaks}
