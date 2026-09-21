"""Repositorio de acceso a datos para los análisis (AnalysisTemp)."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisTemp


class RepositorioAnalisis:
    def __init__(self, db: AsyncSession):
        self.db = db

    def agregar(self, registro: AnalysisTemp) -> None:
        self.db.add(registro)

    async def obtener_por_id(self, analisis_id: int) -> AnalysisTemp | None:
        result = await self.db.execute(
            select(AnalysisTemp).where(AnalysisTemp.id == analisis_id)
        )
        return result.scalar_one_or_none()

    async def obtener_por_id_y_usuario(self, analisis_id: int, user_id: int) -> AnalysisTemp | None:
        result = await self.db.execute(
            select(AnalysisTemp).where(
                AnalysisTemp.id == analisis_id,
                AnalysisTemp.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def contar_completados_de_usuario(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(AnalysisTemp)
            .where(AnalysisTemp.user_id == user_id, AnalysisTemp.estado == "completado")
        )
        return result.scalar_one()

    async def listar_completados_de_usuario(
        self, user_id: int, limit: int, offset: int
    ) -> list[AnalysisTemp]:
        result = await self.db.execute(
            select(AnalysisTemp)
            .where(AnalysisTemp.user_id == user_id, AnalysisTemp.estado == "completado")
            .order_by(AnalysisTemp.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
