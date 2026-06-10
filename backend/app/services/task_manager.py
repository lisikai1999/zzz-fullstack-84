import json
from datetime import datetime

from app.database import SessionLocal
from app.models.project import Project
from app.models.task import AlignmentTask
from app.models.subtitle import SubtitleLine
from app.services.alignment import align_transcript
from app.services.segmentation import segment_words
from app.config import settings

progress_store: dict[str, dict] = {}


def run_alignment(task_id: str, project_id: int):
    db = SessionLocal()
    try:
        task = db.query(AlignmentTask).filter(AlignmentTask.id == task_id).first()
        project = db.query(Project).filter(Project.id == project_id).first()

        task.status = "running"
        db.commit()
        progress_store[task_id] = {"progress": 0.0, "status": "running"}

        def on_progress(p: float):
            task.progress = p
            db.commit()
            progress_store[task_id] = {"progress": p, "status": "running"}

        words = align_transcript(project.audio_path, project.transcript_path, progress_callback=on_progress)

        segments = segment_words(
            words,
            max_chars=settings.segmentation_max_chars,
            min_pause=settings.segmentation_min_pause,
        )

        db.query(SubtitleLine).filter(SubtitleLine.project_id == project_id).delete()
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

        task.status = "completed"
        task.progress = 1.0
        task.completed_at = datetime.utcnow()
        project.status = "segmented"
        db.commit()
        progress_store[task_id] = {"progress": 1.0, "status": "completed"}

    except Exception as e:
        task.status = "failed"
        task.error_message = str(e)
        project.status = "error"
        db.commit()
        progress_store[task_id] = {"progress": 0, "status": "failed", "error": str(e)}
    finally:
        db.close()
