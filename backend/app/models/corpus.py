"""Modelo SQLAlchemy del corpus normativo vectorial. Gestionado en Sprint 2."""

from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CorpusChunk(Base):
    __tablename__ = "corpus_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    documento_fuente: Mapped[str] = mapped_column(String(255), nullable=False)
    jurisdiccion: Mapped[str] = mapped_column(String(50), nullable=False)
    referencia: Mapped[str | None] = mapped_column(String(255))
    categoria_tematica: Mapped[str | None] = mapped_column(String(100))
    texto_original: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list] = mapped_column(Vector(768), nullable=False)
    metadatos: Mapped[dict | None] = mapped_column(JSONB)
    fecha_carga: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
