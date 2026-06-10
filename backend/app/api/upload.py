from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.config import settings

router = APIRouter(prefix="/api/projects/{project_id}/upload", tags=["upload"])


@router.post("/audio")
async def upload_audio(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_dir = settings.upload_dir / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)

    file_path = project_dir / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    project.audio_path = str(file_path)
    db.commit()
    return {"path": str(file_path), "filename": file.filename}


@router.post("/transcript")
async def upload_transcript(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_dir = settings.upload_dir / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)

    file_path = project_dir / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    project.transcript_path = str(file_path)
    db.commit()
    return {"path": str(file_path), "filename": file.filename}
