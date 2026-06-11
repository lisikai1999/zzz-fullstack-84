from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from database import init_db
from routers import projects, alignment, subtitles, export, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(alignment.router, prefix="/api/projects", tags=["alignment"])
app.include_router(subtitles.router, prefix="/api/projects", tags=["subtitles"])
app.include_router(export.router, prefix="/api/projects", tags=["export"])
app.include_router(websocket.router, tags=["websocket"])

app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
