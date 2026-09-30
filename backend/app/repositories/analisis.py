"""Repositorio de acceso a datos para los análisis (AnalysisTemp)."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Select, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisTemp
from app.repositories.json_sql import json_texto, patron_contiene, sin_acentos


@dataclass(frozen=True)
class FiltrosHistorial:
    """Filtros opcionales del historial; siempre se aplican sobre los análisis
    completados del propio usuario."""

    nivel: str | None = None
    desde: datetime | None = None  # inclusive, con zona horaria
    hasta: datetime | None = None  # inclusive, con zona horaria
    texto: str | None = None  # en el fragmento de la política o el comentario; sin distinguir acentos


def _aplicar_filtros(consulta: Select, filtros: FiltrosHistorial | None) -> Select:
    if filtros is None:
        return consulta
    if filtros.nivel:
        nivel = json_texto(AnalysisTemp.resultado, "resumen_general", "nivel_riesgo_global")
        consulta = consulta.where(nivel == filtros.nivel)
    if filtros.desde:
        consulta = consulta.where(AnalysisTemp.created_at >= filtros.desde)
    if filtros.hasta:
        consulta = consulta.where(AnalysisTemp.created_at <= filtros.hasta)
    if filtros.texto:
        # Se quitan los acentos de ambos lados: "politica" encuentra "Política".
        patron = sin_acentos(literal(patron_contiene(filtros.texto)))
        comentario = json_texto(AnalysisTemp.resultado, "resumen_general", "comentario_breve")
        consulta = consulta.where(or_(
            sin_acentos(AnalysisTemp.texto_original).ilike(patron, escape="\\"),
            sin_acentos(comentario).ilike(patron, escape="\\"),
        ))
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

    async def guardar_metadatos_reporte(self, registro: AnalysisTemp, metadatos: dict) -> None:
        """Guarda los metadatos del reporte dentro de resultado. Se asigna un
        diccionario nuevo para que SQLAlchemy detecte el cambio en la columna JSON."""
        registro.resultado = {**(registro.resultado or {}), "metadatos_reporte": metadatos}
        await self.db.flush()

    async def listar_con_metadatos_reporte(self) -> list[AnalysisTemp]:
        """Análisis completados de todos los usuarios que ya generaron algún reporte.
        Solo para estadísticas internas (script fuera de la API)."""
        result = await self.db.execute(
            select(AnalysisTemp)
            .where(AnalysisTemp.estado == "completado")
            .order_by(AnalysisTemp.id)
        )
        return [
            r for r in result.scalars().all()
            if r.resultado and r.resultado.get("metadatos_reporte")
        ]

    async def eliminar(self, registro: AnalysisTemp) -> None:
        """Eliminación definitiva (no hay borrado lógico ni papelera)."""
        await self.db.delete(registro)
        await self.db.flush()

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
