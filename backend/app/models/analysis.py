"""Modelo SQLAlchemy para almacenamiento temporal de análisis. Implementado en Sprint 4."""

import json
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.database import Base


class JSONBCompat(TypeDecorator):
    """JSONB en PostgreSQL, TEXT en SQLite (para tests)."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is not None and dialect.name != "postgresql":
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and dialect.name != "postgresql":
            return json.loads(value)
        return value


class AnalysisTemp(Base):
    __tablename__ = "analysis_temp"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    texto_original: Mapped[str] = mapped_column(Text, nullable=False)
    resultado: Mapped[dict | None] = mapped_column(JSONBCompat)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    seccion_actual: Mapped[int] = mapped_column(Integer, default=0)
    secciones_total: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
