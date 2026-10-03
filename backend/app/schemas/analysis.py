"""Schemas Pydantic para análisis de políticas de privacidad. Implementación en Sprint 4."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.utils.validacion_texto import MAX_CARACTERES_ENTRADA


class FuenteNormativa(BaseModel):
    documento: str
    referencia: str
    fragmento_relevante: str
    # La completa el servidor con la jurisdicción del fragmento del corpus.
    # None en los análisis anteriores, que la deducen del nombre del documento.
    jurisdiccion: str | None = None


# Lista cerrada del tipo de tratamiento de datos (RN-08). Los textos deben ser
# exactamente estos: el cuestionario posprueba usa cuatro de ellos.
TIPOS_TRATAMIENTO: tuple[str, ...] = (
    "Recopilación de datos personales",
    "Uso y finalidad de los datos",
    "Transferencia de datos a terceros",
    "Tiempo de conservación de los datos",
    "Seguridad de los datos",
    "Derechos del usuario sobre sus datos",
    "Cambios en la política",
    "Otro",
)
TIPO_TRATAMIENTO_OTRO = "Otro"

TipoTratamiento = Literal[
    "Recopilación de datos personales",
    "Uso y finalidad de los datos",
    "Transferencia de datos a terceros",
    "Tiempo de conservación de los datos",
    "Seguridad de los datos",
    "Derechos del usuario sobre sus datos",
    "Cambios en la política",
    "Otro",
]


class Hallazgo(BaseModel):
    tipo: Literal["riesgo", "transparencia", "neutral"]
    descripcion: str
    nivel: Literal["bajo", "medio", "alto"]
    fuentes_normativas: list[FuenteNormativa]
    # None solo en análisis realizados antes de incorporar la clasificación;
    # toda respuesta nueva del modelo debe traerlo (ver _parsear_seccion).
    tipo_tratamiento: TipoTratamiento | None = None
    # Código del criterio de la rúbrica que cumple la cláusula (A1–A10, M1–M5,
    # B1–B4); de él se derivan el nivel y el tipo. None en análisis anteriores
    # y en las secciones que no pudieron analizarse.
    criterio: str | None = None
    # True si ningún fragmento del corpus respalda el hallazgo (RN-06): se
    # muestra marcado y no suma al puntaje.
    sin_respaldo: bool = False


class SeccionAnalizada(BaseModel):
    categoria_opp115: str
    titulo: str
    texto_original: str
    hallazgos: list[Hallazgo]
    # False si la sección no pudo analizarse (respuesta inválida o error del
    # modelo): se muestra el aviso, pero no cuenta para el nivel ni la puntuación.
    analizada: bool = True


class ResumenGeneral(BaseModel):
    nivel_riesgo_global: Literal["bajo", "medio", "alto"]
    puntaje: int = Field(..., ge=0, le=100)
    comentario_breve: str


class AnalisisResponse(BaseModel):
    id_analisis: str
    fecha: datetime
    resumen_general: ResumenGeneral
    secciones_analizadas: list[SeccionAnalizada]
    recomendaciones: list[str]


class AnalisisHistorialItem(BaseModel):
    id_analisis: str
    fecha: datetime
    nivel_riesgo_global: Literal["bajo", "medio", "alto"]
    puntaje: int
    comentario_breve: str


class HistorialResponse(BaseModel):
    items: list[AnalisisHistorialItem]
    total: int
    page: int
    page_size: int


class DistribucionNiveles(BaseModel):
    bajo: int = 0
    medio: int = 0
    alto: int = 0


class EstadisticasResponse(BaseModel):
    total: int
    por_nivel: DistribucionNiveles
    # 0 cuando el usuario aún no tiene análisis.
    puntaje_promedio: float


class AnalisisIniciadoResponse(BaseModel):
    id_analisis: str
    estado: Literal["procesando"]


class AnalisisEstadoResponse(BaseModel):
    estado: Literal["procesando", "completado", "error"]
    seccion_actual: int
    secciones_total: int | None


class IngestaTextoRequest(BaseModel):
    # La longitud real (RN-01) se valida en el servicio, tras la limpieza.
    texto: str = Field(..., min_length=1, max_length=MAX_CARACTERES_ENTRADA)


class IngestaURLRequest(BaseModel):
    url: str = Field(..., min_length=10)
