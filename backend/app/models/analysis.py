"""Modelo SQLAlchemy para almacenamiento temporal de análisis. Implementado en Sprint 4."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AnalysisTemp(Base):
    __tablename__ = "analysis_temp"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    texto_original: Mapped[str] = mapped_column(Text, nullable=False)
    resultado: Mapped[dict | None] = mapped_column(JSONB)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
