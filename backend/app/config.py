from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./subtitle_aligner.db"
    upload_dir: Path = Path("uploads")
    max_upload_size_mb: int = 2048
    cors_origins: list[str] = ["http://localhost:5173"]
    aeneas_chunk_seconds: int = 60
    segmentation_max_chars: int = 18
    segmentation_min_pause: float = 0.3

    class Config:
        env_file = ".env"


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
