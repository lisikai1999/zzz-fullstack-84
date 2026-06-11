import uuid
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Project
from schemas import ProjectCreate, ProjectResponse
from config import settings
from utils.audio import extract_audio_to_wav

router = APIRouter()


@router.post("", response_model=ProjectResponse)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(id=str(uuid.uuid4()), name=data.name, language=data.language)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_dir = settings.UPLOAD_DIR / project_id
    if project_dir.exists():
        shutil.rmtree(project_dir)
    await db.delete(project)
    await db.commit()
    return {"detail": "deleted"}


@router.post("/{project_id}/upload")
async def upload_files(
    project_id: str,
    audio: UploadFile = File(...),
    transcript: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_dir = settings.UPLOAD_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(audio.filename).suffix if audio.filename else ".wav"
    original_path = project_dir / f"original{suffix}"
    with open(original_path, "wb") as f:
        content = await audio.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        f.write(content)

    wav_path = project_dir / "audio_16k.wav"
    extract_audio_to_wav(original_path, wav_path)

    project.audio_path = str(wav_path)
    project.transcript = transcript
    project.status = "uploaded"
    await db.commit()

    return {"detail": "uploaded", "audio_path": str(wav_path)}
