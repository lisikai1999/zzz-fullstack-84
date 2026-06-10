from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.api.ws import router as ws_router
from app.database import engine, Base
from app.config import settings

app = FastAPI(title="Subtitle Alignment Tool")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(ws_router)
app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
