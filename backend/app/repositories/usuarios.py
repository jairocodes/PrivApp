"""Repositorio de acceso a datos para los usuarios (User)."""

from datetime import datetime, timezone

from sqlalchemy import Select, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.json_sql import patron_contiene, sin_acentos


class RepositorioUsuarios:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def obtener_por_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def obtener_por_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    def _filtrar(consulta: Select, busqueda: str | None) -> Select:
        if busqueda:
            # Sin distinguir acentos ni mayúsculas: "perez" encuentra "Pérez".
            patron = sin_acentos(literal(patron_contiene(busqueda)))
            consulta = consulta.where(or_(
                sin_acentos(User.nombre).ilike(patron, escape="\\"),
                sin_acentos(User.email).ilike(patron, escape="\\"),
            ))
        return consulta

    async def contar(self, busqueda: str | None = None) -> int:
        consulta = self._filtrar(select(func.count()).select_from(User), busqueda)
        result = await self.db.execute(consulta)
        return result.scalar_one()

    async def listar(self, limit: int, offset: int, busqueda: str | None = None) -> list[User]:
        """Usuarios ordenados por id; la búsqueda filtra por nombre o correo."""
        consulta = self._filtrar(select(User), busqueda).order_by(User.id).limit(limit).offset(offset)
        result = await self.db.execute(consulta)
        return list(result.scalars().all())

    def agregar(self, user: User) -> None:
        self.db.add(user)

    async def actualizar_perfil(self, user: User, nombre: str) -> None:
        user.nombre = nombre
        await self.db.flush()

    async def actualizar_password(self, user: User, hashed_password: str) -> None:
        user.hashed_password = hashed_password
        await self.db.flush()

    async def cambiar_estado(self, user: User, activo: bool) -> None:
        user.is_active = activo
        await self.db.flush()

    async def invalidar_sesiones(self, user: User) -> None:
        """Invalida todas las sesiones del usuario: a partir de ahora solo se
        aceptan tokens emitidos después de este momento."""
        user.sessions_valid_from = datetime.now(timezone.utc)
        await self.db.flush()
