"""Servicio del corpus normativo: consulta, estado y carga de documentos fuente.

La carga reutiliza el mismo proceso que scripts/cargar_corpus.py (segmentación,
representaciones vectoriales y deduplicación por hash de cada fragmento).
"""

import hashlib
import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import (
    ArchivoDemasiadoGrandeError,
    ArchivoNoPermitidoError,
    DocumentoCorpusDuplicadoError,
    DocumentoCorpusNoEncontradoError,
    DocumentoCorpusSinTextoError,
)
from app.models.corpus import CorpusChunk
from app.repositories.corpus import RepositorioCorpusNormativo
from app.schemas.corpus import DocumentoCargadoResponse, DocumentoCorpus, ListadoCorpusResponse
from app.services.ingesta_service import (
    TAMANO_MAXIMO_ARCHIVO,
    TIPOS_ARCHIVO_PERMITIDOS,
    decodificar_txt,
)
from app.utils.chunking import chunk_texto
from app.utils.embeddings import encode_batch
from app.utils.pdf_extractor import extraer_texto_pdf_bytes

logger = logging.getLogger(__name__)

JURISDICCIONES = ("guatemala", "internacional", "estandar_tecnico")
MIN_PALABRAS_DOCUMENTO = 50

CATEGORIA_KEYWORDS: list[tuple[list[str], str]] = [
    (["constitucion", "constitution", "derechos_fundamentales"], "derechos_fundamentales"),
    (["rgpd", "gdpr", "lopdp", "proteccion_datos", "datos_personales"], "proteccion_datos"),
    (["laip", "acceso_informacion", "transparencia"], "acceso_informacion"),
    (["opp", "taxonomia", "ontologia"], "taxonomia_privacidad"),
    (["tosdr", "terminos_servicio", "tos"], "terminos_servicio"),
    (["oea", "parlatino", "principios"], "principios_internacionales"),
]


def inferir_categoria(nombre: str) -> str:
    nombre_lower = nombre.lower().replace(" ", "_").replace("-", "_")
    for palabras_clave, categoria in CATEGORIA_KEYWORDS:
        if any(kw in nombre_lower for kw in palabras_clave):
            return categoria
    return "general"


def hash_chunk(documento: str, texto: str) -> str:
    contenido = f"{documento}::{texto}"
    return hashlib.md5(contenido.encode("utf-8")).hexdigest()


def referencia_desde_nombre(nombre: str) -> str:
    return Path(nombre).stem.replace("_", " ").replace("-", " ").title()


async def insertar_fragmentos(
    db: AsyncSession,
    documento_fuente: str,
    texto: str,
    jurisdiccion: str,
    metadatos_extra: dict | None = None,
) -> tuple[int, int]:
    """Segmenta el texto, descarta los fragmentos ya existentes (por hash),
    genera las representaciones de los nuevos y los agrega a la sesión.
    Devuelve (insertados, duplicados). No confirma la transacción."""
    chunks = chunk_texto(texto)
    if not chunks:
        return 0, 0

    repo = RepositorioCorpusNormativo(db)
    por_hash = {hash_chunk(documento_fuente, c): c for c in chunks}
    existentes = await repo.hashes_existentes(list(por_hash))
    nuevos = [(h, t) for h, t in por_hash.items() if h not in existentes]
    if not nuevos:
        return 0, len(por_hash)

    # Generar las representaciones es costoso en CPU: fuera del bucle de eventos.
    embeddings = await run_in_threadpool(encode_batch, [t for _, t in nuevos])
    categoria = inferir_categoria(Path(documento_fuente).stem)
    referencia = referencia_desde_nombre(documento_fuente)
    for (chunk_hash, chunk_text), embedding in zip(nuevos, embeddings):
        repo.agregar(CorpusChunk(
            documento_fuente=documento_fuente,
            jurisdiccion=jurisdiccion,
            referencia=referencia,
            categoria_tematica=categoria,
            texto_original=chunk_text,
            embedding=embedding,
            metadatos={"hash": chunk_hash, **(metadatos_extra or {})},
        ))
    await db.flush()
    return len(nuevos), len(por_hash) - len(nuevos)


async def listar_documentos(db: AsyncSession) -> ListadoCorpusResponse:
    filas = await RepositorioCorpusNormativo(db).listar_documentos()
    return ListadoCorpusResponse(documentos=[DocumentoCorpus(**dict(f)) for f in filas])


async def cambiar_estado_documento(
    db: AsyncSession, documento_fuente: str, activo: bool
) -> DocumentoCorpus:
    """Activa o desactiva el documento completo. No modifica el texto ni las
    representaciones vectoriales de sus fragmentos."""
    repo = RepositorioCorpusNormativo(db)
    if await repo.cambiar_estado_documento(documento_fuente, activo) == 0:
        raise DocumentoCorpusNoEncontradoError()
    logger.info("Documento del corpus '%s' marcado como activo=%s.", documento_fuente, activo)
    return DocumentoCorpus(**dict(await repo.obtener_documento(documento_fuente)))


def _extraer_texto_documento(nombre: str, tipo_contenido: str | None, contenido: bytes) -> str:
    extension = Path(nombre).suffix.lower()
    tipo = (tipo_contenido or "").split(";")[0].strip().lower()
    if extension not in TIPOS_ARCHIVO_PERMITIDOS or tipo not in TIPOS_ARCHIVO_PERMITIDOS[extension]:
        raise ArchivoNoPermitidoError()
    if len(contenido) > TAMANO_MAXIMO_ARCHIVO:
        raise ArchivoDemasiadoGrandeError()
    if extension == ".pdf":
        if not contenido.startswith(b"%PDF-"):
            raise ArchivoNoPermitidoError()
        return extraer_texto_pdf_bytes(contenido, nombre)
    return decodificar_txt(contenido)


async def cargar_documento(
    db: AsyncSession,
    nombre: str,
    tipo_contenido: str | None,
    contenido: bytes,
    jurisdiccion: str,
) -> DocumentoCargadoResponse:
    """Incorpora un documento normativo nuevo al corpus. Solo se conservan los
    fragmentos de texto y sus representaciones; el archivo original se descarta."""
    texto = _extraer_texto_documento(nombre, tipo_contenido, contenido)
    if len(texto.split()) < MIN_PALABRAS_DOCUMENTO:
        raise DocumentoCorpusSinTextoError()

    repo = RepositorioCorpusNormativo(db)
    if await repo.obtener_documento(nombre) is not None:
        raise DocumentoCorpusDuplicadoError()

    insertados, duplicados = await insertar_fragmentos(
        db, nombre, texto, jurisdiccion, {"origen": "carga_administrador"}
    )
    if insertados == 0:
        raise DocumentoCorpusSinTextoError()
    logger.info("Documento '%s' incorporado al corpus: %d fragmentos.", nombre, insertados)
    resumen = DocumentoCorpus(**dict(await repo.obtener_documento(nombre)))
    return DocumentoCargadoResponse(
        **resumen.model_dump(), fragmentos_insertados=insertados, fragmentos_duplicados=duplicados
    )
