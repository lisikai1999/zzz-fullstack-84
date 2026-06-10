import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.task import AlignmentTask
from app.schemas.task import TaskResponse
from app.services.task_manager import run_alignment

router = APIRouter(tags=["alignment"])


@router.post("/api/projects/{project_id}/align", response_model=TaskResponse)
def start_alignment(project_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.audio_path:
        raise HTTPException(status_code=400, detail="No audio file uploaded")
    if not project.transcript_path:
        raise HTTPException(status_code=400, detail="No transcript file uploaded")

    task_id = str(uuid.uuid4())
    task = AlignmentTask(id=task_id, project_id=project_id, status="pending")
    db.add(task)
    project.status = "aligning"
    db.commit()
    db.refresh(task)

    background_tasks.add_task(run_alignment, task_id, project_id)
    return task


@router.get("/api/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(AlignmentTask).filter(AlignmentTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
