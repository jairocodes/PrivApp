"""Repositorio de acceso a datos para los análisis (AnalysisTemp)."""

from dataclasses import dataclass

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisTemp
from app.repositories.json_sql import json_texto


@dataclass(frozen=True)
class FiltrosHistorial:
    """Filtros opcionales del historial; siempre se aplican sobre los análisis
    completados del propio usuario."""

    nivel: str | None = None


def _aplicar_filtros(consulta: Select, filtros: FiltrosHistorial | None) -> Select:
    if filtros is None:
        return consulta
    if filtros.nivel:
        nivel = json_texto(AnalysisTemp.resultado, "resumen_general", "nivel_riesgo_global")
        consulta = consulta.where(nivel == filtros.nivel)
    return consulta


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

    async def contar_completados_de_usuario(
        self, user_id: int, filtros: FiltrosHistorial | None = None
    ) -> int:
        consulta = (
            select(func.count())
            .select_from(AnalysisTemp)
            .where(AnalysisTemp.user_id == user_id, AnalysisTemp.estado == "completado")
        )
        result = await self.db.execute(_aplicar_filtros(consulta, filtros))
        return result.scalar_one()

    async def listar_completados_de_usuario(
        self, user_id: int, limit: int, offset: int, filtros: FiltrosHistorial | None = None
    ) -> list[AnalysisTemp]:
        consulta = select(AnalysisTemp).where(
            AnalysisTemp.user_id == user_id, AnalysisTemp.estado == "completado"
        )
        result = await self.db.execute(
            _aplicar_filtros(consulta, filtros)
            .order_by(AnalysisTemp.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
