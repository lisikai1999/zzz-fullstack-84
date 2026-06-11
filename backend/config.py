from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Subtitle Aligner"
    DATABASE_URL: str = "sqlite+aiosqlite:///./subtitle_aligner.db"
    UPLOAD_DIR: Path = Path(__file__).parent / "uploads"
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    WHISPER_MODEL: str = "medium"
    DEFAULT_LANGUAGE: str = "zh"
    MAX_CHARS_PER_LINE: int = 20
    PAUSE_THRESHOLD_MS: float = 300.0
    MIN_SUBTITLE_DURATION_MS: float = 500.0

    class Config:
        env_file = ".env"


settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
