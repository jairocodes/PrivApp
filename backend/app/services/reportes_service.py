"""Generación de reportes PDF de análisis (HU-15).

Construye el documento en memoria con ReportLab a partir de un AnalisisResponse
ya persistido — no requiere archivos temporales ni acceso adicional a la BD.
La función es síncrona/CPU-bound: quien la invoque desde un endpoint async
debe ejecutarla en threadpool (ver app/api/v1/analisis.py).
"""

import io
import time
from xml.sax.saxutils import escape as _esc

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.schemas.analysis import AnalisisResponse

_HEX_NIVEL = {"bajo": "#16a34a", "medio": "#ca8a04", "alto": "#dc2626"}
_LABEL_NIVEL = {"bajo": "Riesgo Bajo", "medio": "Riesgo Medio", "alto": "Riesgo Alto"}
_LABEL_JURISDICCION = {
    "guatemala": "Guatemala",
    "internacional": "Internacional",
    "estandar_tecnico": "Estándar técnico",
}


def _inferir_jurisdiccion(documento: str) -> str:
    """Misma heurística de CitaNormativa.tsx (frontend), para que el PDF sea
    consistente con lo que el usuario ya vio en el panel de resultados."""
    d = documento.lower()
    if any(k in d for k in _CLAVES_GUATEMALA):
        return "guatemala"
    if any(k in d for k in _CLAVES_ESTANDAR):
        return "estandar_tecnico"
    return "internacional"


# Mismas claves que frontend/src/utils/jurisdiccion.ts.
_CLAVES_GUATEMALA = ("constituci", "laip", "guatemal", "decreto 57", "57-2008", "acceso a la informaci")
_CLAVES_ESTANDAR = ("opp", "tosdr", "tos;dr", "tos dr")


def _estilos() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("titulo", parent=base["Title"], fontSize=16, spaceAfter=4),
        "subtitulo": ParagraphStyle(
            "subtitulo", parent=base["Normal"], fontSize=9,
            textColor=colors.grey, alignment=TA_CENTER, spaceAfter=16,
        ),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=6),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontSize=11, spaceBefore=8, spaceAfter=4),
        "normal": ParagraphStyle("normal", parent=base["Normal"], fontSize=10, leading=14, spaceAfter=4),
        "cita": ParagraphStyle(
            "cita", parent=base["Normal"], fontSize=9, leading=12,
            textColor=colors.HexColor("#374151"), leftIndent=10, spaceAfter=4,
        ),
        "footer": ParagraphStyle("footer", parent=base["Normal"], fontSize=8, textColor=colors.grey, spaceBefore=18),
    }


def generar_pdf_analisis(analisis: AnalisisResponse) -> bytes:
    """Construye el reporte PDF completo de un análisis y devuelve sus bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    estilos = _estilos()
    story: list = []

    # Encabezado
    story.append(Paragraph("PrivApp — Reporte de Análisis de Política de Privacidad", estilos["titulo"]))
    story.append(Paragraph(
        f"Análisis generado el {analisis.fecha.strftime('%d/%m/%Y %H:%M')}", estilos["subtitulo"]
    ))

    # Resumen ejecutivo
    resumen = analisis.resumen_general
    hex_nivel = _HEX_NIVEL.get(resumen.nivel_riesgo_global, "#000000")
    label_nivel = _LABEL_NIVEL.get(resumen.nivel_riesgo_global, resumen.nivel_riesgo_global)
    story.append(Paragraph("Resumen ejecutivo", estilos["h2"]))
    story.append(Paragraph(
        f'<font color="{hex_nivel}"><b>{label_nivel}</b></font> — Puntaje: {resumen.puntaje}/100',
        estilos["normal"],
    ))
    story.append(Paragraph(_esc(resumen.comentario_breve), estilos["normal"]))
    story.append(Spacer(1, 10))

    # Secciones analizadas
    story.append(Paragraph("Secciones analizadas", estilos["h2"]))
    if not analisis.secciones_analizadas:
        story.append(Paragraph("No se analizaron secciones en esta política.", estilos["normal"]))

    for i, seccion in enumerate(analisis.secciones_analizadas, 1):
        story.append(Paragraph(
            f"{i}. {_esc(seccion.titulo)} ({_esc(seccion.categoria_opp115)})", estilos["h3"]
        ))
        if not seccion.hallazgos:
            story.append(Paragraph("No se identificaron hallazgos en esta sección.", estilos["normal"]))
            continue

        for hallazgo in seccion.hallazgos:
            hex_h = _HEX_NIVEL.get(hallazgo.nivel, "#000000")
            label_h = _LABEL_NIVEL.get(hallazgo.nivel, hallazgo.nivel)
            # Los análisis anteriores a la clasificación no tienen tipo de tratamiento.
            tratamiento = (
                f" · <i>Tipo de tratamiento: {_esc(hallazgo.tipo_tratamiento)}</i>"
                if hallazgo.tipo_tratamiento
                else ""
            )
            story.append(Paragraph(
                f'<font color="{hex_h}"><b>{label_h}</b></font> '
                f"({_esc(hallazgo.tipo)}){tratamiento} — {_esc(hallazgo.descripcion)}",
                estilos["normal"],
            ))
            if hallazgo.sin_respaldo:
                story.append(Paragraph(
                    "<i>Sin respaldo en el corpus normativo: no se cita ninguna norma y "
                    "no suma al puntaje de riesgo.</i>",
                    estilos["cita"],
                ))
            for fuente in hallazgo.fuentes_normativas:
                # Los análisis anteriores no guardan la jurisdicción de la cita.
                jurisdiccion = _LABEL_JURISDICCION.get(
                    fuente.jurisdiccion or _inferir_jurisdiccion(fuente.documento), "Internacional"
                )
                referencia = f" — {_esc(fuente.referencia)}" if fuente.referencia else ""
                story.append(Paragraph(
                    f"<b>[{jurisdiccion}]</b> {_esc(fuente.documento)}{referencia}: "
                    f"“{_esc(fuente.fragmento_relevante)}”",
                    estilos["cita"],
                ))
        story.append(Spacer(1, 6))

    # Recomendaciones
    story.append(Paragraph("Recomendaciones", estilos["h2"]))
    if analisis.recomendaciones:
        for i, rec in enumerate(analisis.recomendaciones, 1):
            story.append(Paragraph(f"{i}. {_esc(rec)}", estilos["normal"]))
    else:
        story.append(Paragraph("No se generaron recomendaciones para este análisis.", estilos["normal"]))

    # Aviso académico (mismo texto que el panel web)
    story.append(Paragraph(
        "Este análisis es orientativo y no constituye asesoría legal. Las referencias "
        "internacionales (RGPD, Principios OEA, etc.) son buenas prácticas, no normativa "
        "vigente en Guatemala. Para dudas legales, consulta a un profesional.",
        estilos["footer"],
    ))

    doc.build(story)
    return buffer.getvalue()


def generar_pdf_y_medir(analisis: AnalisisResponse) -> tuple[bytes, float]:
    """Genera el PDF y devuelve también los segundos que tardó su construcción
    (indicador de la Tabla 1). Se mide aquí, en el hilo que lo construye, para
    no incluir la espera en la cola de hilos."""
    inicio = time.perf_counter()
    contenido = generar_pdf_analisis(analisis)
    return contenido, time.perf_counter() - inicio


def resumir_tiempos(segundos: list[float]) -> dict:
    """Estadísticas de una lista de tiempos de generación, en segundos."""
    if not segundos:
        return {"mediciones": 0}
    ordenados = sorted(segundos)
    n = len(ordenados)
    mitad = n // 2
    mediana = ordenados[mitad] if n % 2 else (ordenados[mitad - 1] + ordenados[mitad]) / 2
    # Percentil 95 por el método del rango más cercano.
    p95 = ordenados[max(0, -(-95 * n // 100) - 1)]
    return {
        "mediciones": n,
        "promedio": sum(ordenados) / n,
        "mediana": mediana,
        "minimo": ordenados[0],
        "maximo": ordenados[-1],
        "p95": p95,
    }
