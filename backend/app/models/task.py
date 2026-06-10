from datetime import datetime

from sqlalchemy import Integer, Float, Text, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AlignmentTask(Base):
    __tablename__ = "alignment_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="tasks")  # noqa: F821
