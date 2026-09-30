"""Coherencia de los resultados y de los mensajes de error de la API."""

from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.models.analysis import AnalysisTemp


def _auth(user) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


class TestSeccionesSinAnalizar:
    def _seccion(self, nivel):
        from app.schemas.analysis import Hallazgo, SeccionAnalizada

        return SeccionAnalizada(
            categoria_opp115="General", titulo="S", texto_original="t",
            hallazgos=[Hallazgo(tipo="riesgo", descripcion="d", nivel=nivel, fuentes_normativas=[
                {"documento": "RGPD", "referencia": "", "fragmento_relevante": "f"}
            ])],
        )

    def test_una_seccion_que_no_se_pudo_analizar_no_baja_la_puntuacion(self):
        from app.services.analisis_service import _calcular_resumen, _seccion_fallback

        solo_altos = _calcular_resumen([self._seccion("alto"), self._seccion("alto")])
        con_fallo = _calcular_resumen([self._seccion("alto"), self._seccion("alto"), _seccion_fallback("texto", 3)])

        assert con_fallo.puntaje == solo_altos.puntaje == 100
        assert con_fallo.nivel_riesgo_global == "alto"

    def test_la_seccion_de_respaldo_queda_marcada(self):
        from app.services.analisis_service import _seccion_fallback

        seccion = _seccion_fallback("texto", 2)
        assert seccion.analizada is False
        assert seccion.hallazgos[0].descripcion == "No fue posible analizar esta sección automáticamente."

    def test_los_analisis_antiguos_se_consideran_analizados(self):
        from app.schemas.analysis import SeccionAnalizada

        seccion = SeccionAnalizada(categoria_opp115="G", titulo="S", texto_original="t", hallazgos=[])
        assert seccion.analizada is True


class TestAnalisisInterrumpidos:
    async def test_al_arrancar_se_marcan_como_error(self, db_session, seed_user):
        from app.services.analisis_service import marcar_analisis_interrumpidos

        for estado in ("procesando", "procesando", "completado"):
            db_session.add(AnalysisTemp(user_id=seed_user.id, texto_original="t", estado=estado))
        await db_session.commit()

        assert await marcar_analisis_interrumpidos() == 2

        estados = sorted((await db_session.execute(select(AnalysisTemp.estado))).scalars().all())
        assert estados == ["completado", "error", "error"]

    async def test_despues_ya_se_puede_eliminar_la_cuenta(self, client: AsyncClient, db_session, seed_user):
        from app.services.analisis_service import marcar_analisis_interrumpidos

        db_session.add(AnalysisTemp(user_id=seed_user.id, texto_original="t", estado="procesando"))
        await db_session.commit()
        await marcar_analisis_interrumpidos()

        r = await client.request("DELETE", "/api/auth/me", json={"password": "TestPass123"}, headers=_auth(seed_user))
        assert r.status_code == 204


class TestDetalleSegunEstado:
    async def _crear(self, db_session, user, estado):
        registro = AnalysisTemp(user_id=user.id, texto_original="t", estado=estado)
        db_session.add(registro)
        await db_session.flush()
        return registro

    async def test_en_proceso(self, client, db_session, seed_user):
        registro = await self._crear(db_session, seed_user, "procesando")
        for ruta in (f"/api/analisis/{registro.id}", f"/api/analisis/{registro.id}/pdf"):
            r = await client.get(ruta, headers=_auth(seed_user))
            assert r.status_code == 409, ruta
            assert r.json()["detail"] == "El análisis todavía se está procesando."

    async def test_con_error(self, client, db_session, seed_user):
        registro = await self._crear(db_session, seed_user, "error")
        r = await client.get(f"/api/analisis/{registro.id}", headers=_auth(seed_user))
        assert r.status_code == 409
        assert "no pudo completarse" in r.json()["detail"]

    async def test_inexistente_sigue_siendo_404(self, client, seed_user):
        r = await client.get("/api/analisis/999999", headers=_auth(seed_user))
        assert r.status_code == 404


class TestMensajesDeError:
    async def test_el_limite_superado_responde_en_espanol_con_detail(self, client: AsyncClient):
        cuerpo = {"email": "nadie@ejemplo.com", "password": "Otra12345"}
        for _ in range(5):
            await client.post("/api/auth/login", json=cuerpo)
        r = await client.post("/api/auth/login", json=cuerpo)

        assert r.status_code == 429
        assert r.json() == {"detail": "Demasiadas solicitudes. Espera un minuto antes de volver a intentarlo."}

    async def test_las_validaciones_propias_no_llevan_el_prefijo_de_pydantic(self, client: AsyncClient):
        r = await client.post("/api/auth/register", json={
            "nombre": "Ana", "email": "ana@ejemplo.com", "password": "Segura123",
            "acepta_aviso": False, "declara_edad": True,
        })

        assert r.status_code == 422
        mensajes = [e["msg"] for e in r.json()["detail"]]
        assert "Debes aceptar el aviso de privacidad para registrarte." in mensajes
        assert not any(m.startswith("Value error") for m in mensajes)

    async def test_las_validaciones_de_pydantic_conservan_su_formato(self, client: AsyncClient):
        r = await client.post("/api/auth/login", json={"email": "no-es-correo"})
        assert r.status_code == 422
        assert {e["loc"][-1] for e in r.json()["detail"]} >= {"email", "password"}


class TestVersion:
    async def test_health_informa_la_version_de_entrega(self, client: AsyncClient):
        from app.main import VERSION_API

        r = await client.get("/health")
        assert r.json()["version"] == VERSION_API == "2.0.0"
