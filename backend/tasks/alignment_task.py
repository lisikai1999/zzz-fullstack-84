import logging
from typing import Dict

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from services.alignment_service import align_audio_with_text

logger = logging.getLogger(__name__)

progress_store: Dict[str, Dict] = {}

sync_engine = create_engine(settings.DATABASE_URL.replace("+aiosqlite", ""))
SyncSession = sessionmaker(bind=sync_engine)


def run_alignment_task(
    alignment_id: str,
    project_id: str,
    audio_path: str,
    transcript: str,
    language: str,
):
    """Run alignment in a background thread. Updates progress_store and DB."""
    try:
        progress_store[project_id] = {"percent": 5, "stage": "loading_model"}

        progress_store[project_id] = {"percent": 20, "stage": "aligning"}
        word_alignments = align_audio_with_text(audio_path, transcript, language)

        progress_store[project_id] = {"percent": 90, "stage": "saving"}

        session = SyncSession()
        try:
            from models.alignment import AlignmentResult
            from models.project import Project

            alignment = session.get(AlignmentResult, alignment_id)
            if alignment:
                alignment.word_alignments = word_alignments
                alignment.status = "completed"

            project = session.get(Project, project_id)
            if project:
                project.status = "aligned"

            session.commit()
        finally:
            session.close()

        progress_store[project_id] = {"percent": 100, "stage": "done"}

    except Exception as e:
        logger.error(f"Alignment failed for {project_id}: {e}")
        progress_store[project_id] = {"percent": -1, "stage": "error", "error": str(e)}

        session = SyncSession()
        try:
            from models.alignment import AlignmentResult
            alignment = session.get(AlignmentResult, alignment_id)
            if alignment:
                alignment.status = "failed"
            session.commit()
        finally:
            session.close()
