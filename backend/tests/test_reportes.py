"""Pruebas del Módulo 5 — Repositorio y generación de reportes (EP-07).

- TestEndpointHistorial: integración con GET /api/analisis (historial paginado, HU-14)
- TestEndpointPDF: integración con GET /api/analisis/{id}/pdf (reporte PDF, HU-15)
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.analysis import AnalysisTemp
from app.models.user import User


def _resultado(nivel="bajo", puntaje=10, comentario="Comentario de prueba"):
    return {
        "resumen_general": {
            "nivel_riesgo_global": nivel,
            "puntaje": puntaje,
            "comentario_breve": comentario,
        }
    }


def _resultado_completo(
    id_analisis="1",
    nivel="alto",
    puntaje=75,
    seccion_titulo="Recopilación de datos",
    documento_fuente="RGPD",
    fragmento="Los datos deben ser tratados con transparencia.",
):
    """Dict completo y válido de AnalisisResponse, para pruebas que pasan por
    obtener_analisis() (a diferencia de _resultado(), usado solo por historial)."""
    return {
        "id_analisis": id_analisis,
        "fecha": datetime.now(timezone.utc).isoformat(),
        "resumen_general": {
            "nivel_riesgo_global": nivel,
            "puntaje": puntaje,
            "comentario_breve": "Comentario de prueba para el resumen ejecutivo.",
        },
        "secciones_analizadas": [
            {
                "categoria_opp115": "First Party Collection/Use",
                "titulo": seccion_titulo,
                "texto_original": "Texto original de la sección.",
                "hallazgos": [
                    {
                        "tipo": "riesgo",
                        "descripcion": "Se comparten datos con terceros no identificados.",
                        "nivel": nivel,
                        "fuentes_normativas": [
                            {
                                "documento": documento_fuente,
                                "referencia": "Artículo 5",
                                "fragmento_relevante": fragmento,
                            }
                        ],
                    }
                ],
            }
        ],
        "recomendaciones": ["Revisa la sección de terceros antes de aceptar."],
    }


async def _crear_analisis(
    db_session: AsyncSession,
    user_id: int,
    estado: str = "completado",
    fecha: datetime | None = None,
    resultado: dict | None = None,
    **kwargs,
) -> AnalysisTemp:
    if resultado is None and estado == "completado":
        resultado = _resultado(**kwargs)

    registro = AnalysisTemp(
        user_id=user_id,
        texto_original="Texto de prueba",
        estado=estado,
        resultado=resultado,
    )
    if fecha is not None:
        registro.created_at = fecha
    db_session.add(registro)
    await db_session.flush()
    return registro


class TestEndpointHistorial:
    async def test_historial_sin_autenticacion_retorna_403(self, client):
        response = await client.get("/api/analisis")
        assert response.status_code == 403

    async def test_historial_vacio_retorna_lista_vacia(self, client):
        token = create_access_token("1")
        response = await client.get(
            "/api/analisis", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        datos = response.json()
        assert datos["items"] == []
        assert datos["total"] == 0

    async def test_historial_lista_solo_completados(self, client, db_session, seed_user):
        await _crear_analisis(db_session, seed_user.id, estado="completado")
        await _crear_analisis(db_session, seed_user.id, estado="procesando")

        token = create_access_token(str(seed_user.id))
        response = await client.get(
            "/api/analisis", headers={"Authorization": f"Bearer {token}"}
        )
        datos = response.json()
        assert datos["total"] == 1
        assert len(datos["items"]) == 1

    async def test_historial_orden_descendente_por_fecha(self, client, db_session, seed_user):
        ahora = datetime.now(timezone.utc)
        antiguo = await _crear_analisis(
            db_session, seed_user.id, fecha=ahora - timedelta(days=2), comentario="Antiguo"
        )
        reciente = await _crear_analisis(
            db_session, seed_user.id, fecha=ahora, comentario="Reciente"
        )

        token = create_access_token(str(seed_user.id))
        response = await client.get(
            "/api/analisis", headers={"Authorization": f"Bearer {token}"}
        )
        datos = response.json()
        ids = [item["id_analisis"] for item in datos["items"]]
        assert ids == [str(reciente.id), str(antiguo.id)]

    async def test_historial_paginacion_respeta_page_size(self, client, db_session, seed_user):
        for _ in range(5):
            await _crear_analisis(db_session, seed_user.id)

        token = create_access_token(str(seed_user.id))
        response = await client.get(
            "/api/analisis?page=1&page_size=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        datos = response.json()
        assert len(datos["items"]) == 2
        assert datos["total"] == 5
        assert datos["page"] == 1
        assert datos["page_size"] == 2

    async def test_historial_aisla_entre_usuarios(self, client, db_session, seed_user):
        otro_usuario = User(
            nombre="Otro Usuario",
            email="otro@privapp.test",
            hashed_password=hash_password("OtraPass123"),
            is_active=True,
        )
        db_session.add(otro_usuario)
        await db_session.flush()

        await _crear_analisis(db_session, seed_user.id, comentario="Del usuario 1")
        await _crear_analisis(db_session, otro_usuario.id, comentario="Del usuario 2")

        token = create_access_token(str(otro_usuario.id))
        response = await client.get(
            "/api/analisis", headers={"Authorization": f"Bearer {token}"}
        )
        datos = response.json()
        assert datos["total"] == 1
        assert datos["items"][0]["comentario_breve"] == "Del usuario 2"

    async def test_historial_page_invalido_retorna_422(self, client):
        token = create_access_token("1")
        response = await client.get(
            "/api/analisis?page=0", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 422

    async def test_historial_page_size_excede_maximo_retorna_422(self, client):
        token = create_access_token("1")
        response = await client.get(
            "/api/analisis?page_size=999", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 422


class TestEndpointPDF:
    async def test_pdf_sin_autenticacion_retorna_403(self, client):
        response = await client.get("/api/analisis/1/pdf")
        assert response.status_code == 403

    async def test_pdf_analisis_no_existente_retorna_404(self, client):
        token = create_access_token("1")
        response = await client.get(
            "/api/analisis/99999/pdf", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404

    async def test_pdf_de_otro_usuario_retorna_404(self, client, db_session, seed_user):
        otro_usuario = User(
            nombre="Otro Usuario",
            email="otro-pdf@privapp.test",
            hashed_password=hash_password("OtraPass123"),
            is_active=True,
        )
        db_session.add(otro_usuario)
        await db_session.flush()

        analisis = await _crear_analisis(
            db_session, otro_usuario.id, resultado=_resultado_completo()
        )

        token = create_access_token(str(seed_user.id))
        response = await client.get(
            f"/api/analisis/{analisis.id}/pdf", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404

    async def test_pdf_genera_documento_valido(self, client, db_session, seed_user):
        analisis = await _crear_analisis(
            db_session, seed_user.id, resultado=_resultado_completo()
        )

        token = create_access_token(str(seed_user.id))
        response = await client.get(
            f"/api/analisis/{analisis.id}/pdf", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF")

    async def test_pdf_contenido_incluye_datos_del_analisis(self, client, db_session, seed_user):
        from io import BytesIO

        from pypdf import PdfReader

        analisis = await _crear_analisis(
            db_session,
            seed_user.id,
            resultado=_resultado_completo(
                nivel="alto",
                puntaje=42,
                seccion_titulo="Compartición con terceros",
                documento_fuente="Constitución Política de Guatemala",
                fragmento="fragmento normativo verificable",
            ),
        )

        token = create_access_token(str(seed_user.id))
        response = await client.get(
            f"/api/analisis/{analisis.id}/pdf", headers={"Authorization": f"Bearer {token}"}
        )

        texto = "".join(
            pagina.extract_text() or "" for pagina in PdfReader(BytesIO(response.content)).pages
        )
        assert "42/100" in texto
        assert "Compartición con terceros" in texto
        assert "fragmento normativo verificable" in texto
        # La Constitución de Guatemala debe etiquetarse como jurisdicción "Guatemala"
        assert "Guatemala" in texto
