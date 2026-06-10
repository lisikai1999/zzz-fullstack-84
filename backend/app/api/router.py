from fastapi import APIRouter

from app.api.projects import router as projects_router
from app.api.upload import router as upload_router
from app.api.subtitles import router as subtitles_router
from app.api.alignment import router as alignment_router
from app.api.correction import router as correction_router
from app.services.export import router as export_router

api_router = APIRouter()
api_router.include_router(projects_router)
api_router.include_router(upload_router)
api_router.include_router(subtitles_router)
api_router.include_router(alignment_router)
api_router.include_router(correction_router)
api_router.include_router(export_router)
