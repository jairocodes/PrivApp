"""Modelo SQLAlchemy del usuario del sistema. Implementado en Sprint 1."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

ROL_USUARIO = "usuario"
ROL_ADMINISTRADOR = "administrador"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('usuario', 'administrador')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ROL_USUARIO, server_default=ROL_USUARIO
    )
    privacy_accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sessions_valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
