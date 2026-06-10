import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.config import settings

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(name=data.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    project_dir = settings.upload_dir / str(project.id)
    project_dir.mkdir(parents=True, exist_ok=True)
    return project


@router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if data.name is not None:
        project.name = data.name
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_dir = settings.upload_dir / str(project_id)
    if project_dir.exists():
        shutil.rmtree(project_dir)
    db.delete(project)
    db.commit()
    return {"detail": "deleted"}
