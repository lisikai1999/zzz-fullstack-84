from datetime import datetime

from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    audio_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    transcript_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    subtitles: Mapped[list["SubtitleLine"]] = relationship(back_populates="project", cascade="all, delete-orphan")  # noqa: F821
    tasks: Mapped[list["AlignmentTask"]] = relationship(back_populates="project", cascade="all, delete-orphan")  # noqa: F821
