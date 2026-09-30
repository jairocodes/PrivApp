"""Repositorio de acceso a datos para los usuarios (User)."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class RepositorioUsuarios:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def obtener_por_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def obtener_por_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    def agregar(self, user: User) -> None:
        self.db.add(user)

    async def invalidar_sesiones(self, user: User) -> None:
        """Invalida todas las sesiones del usuario: a partir de ahora solo se
        aceptan tokens emitidos después de este momento."""
        user.sessions_valid_from = datetime.now(timezone.utc)
        await self.db.flush()
