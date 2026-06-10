from datetime import datetime

from sqlalchemy import Integer, Float, Text, String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SubtitleLine(Base):
    __tablename__ = "subtitle_lines"
    __table_args__ = (UniqueConstraint("project_id", "index", name="uq_project_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    start_time: Mapped[float] = mapped_column(Float)
    end_time: Mapped[float] = mapped_column(Float)
    words_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="subtitles")  # noqa: F821
