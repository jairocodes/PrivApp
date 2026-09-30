"""Tests del registro del tiempo de generación del reporte PDF (Tabla 1)."""

from unittest.mock import patch

import pytest

from app.core.limiter import limiter
from app.services.analisis_service import MAX_GENERACIONES_REGISTRADAS
from app.services.reportes_service import generar_pdf_y_medir
from app.schemas.analysis import AnalisisResponse
from tests.test_historial_filtros import _auth
from tests.test_reportes import _crear_analisis, _resultado_completo


async def _descargar(client, user, analisis_id):
    r = await client.get(f"/api/analisis/{analisis_id}/pdf", headers=_auth(user))
    assert r.status_code == 200
    return r


class TestTiempoDeGeneracion:
    def test_generar_y_medir_devuelve_el_pdf_y_los_segundos(self):
        contenido, segundos = generar_pdf_y_medir(AnalisisResponse(**_resultado_completo()))
        assert contenido.startswith(b"%PDF")
        assert 0 < segundos < 30

    async def test_al_generar_un_reporte_queda_registrado_su_tiempo(self, client, db_session, seed_user):
        analisis = await _crear_analisis(db_session, seed_user.id, resultado=_resultado_completo())

        await _descargar(client, seed_user, analisis.id)

        await db_session.refresh(analisis)
        metadatos = analisis.resultado["metadatos_reporte"]
        assert metadatos["ultima_generacion_segundos"] > 0
        assert metadatos["ultima_generacion_en"]
        assert metadatos["total_generaciones"] == 1
        assert metadatos["generaciones"] == [
            {"fecha": metadatos["ultima_generacion_en"], "segundos": metadatos["ultima_generacion_segundos"]}
        ]

    async def test_cada_descarga_suma_una_medicion(self, client, db_session, seed_user):
        analisis = await _crear_analisis(db_session, seed_user.id, resultado=_resultado_completo())

        for _ in range(3):
            await _descargar(client, seed_user, analisis.id)

        await db_session.refresh(analisis)
        metadatos = analisis.resultado["metadatos_reporte"]
        assert metadatos["total_generaciones"] == 3
        assert len(metadatos["generaciones"]) == 3

    async def test_conserva_solo_las_ultimas_mediciones(self, client, db_session, seed_user):
        analisis = await _crear_analisis(db_session, seed_user.id, resultado=_resultado_completo())
        tiempos = [0.1 * (i + 1) for i in range(MAX_GENERACIONES_REGISTRADAS + 2)]

        with patch("app.api.v1.analisis.generar_pdf_y_medir", side_effect=[(b"%PDF-1.4", t) for t in tiempos]):
            for _ in tiempos:
                limiter.reset()  # más descargas que el límite de 10 por minuto
                await _descargar(client, seed_user, analisis.id)

        await db_session.refresh(analisis)
        metadatos = analisis.resultado["metadatos_reporte"]
        assert metadatos["total_generaciones"] == len(tiempos)
        assert [g["segundos"] for g in metadatos["generaciones"]] == pytest.approx(tiempos[-MAX_GENERACIONES_REGISTRADAS:])
        assert metadatos["ultima_generacion_segundos"] == pytest.approx(tiempos[-1])

    async def test_el_resultado_del_analisis_se_sigue_mostrando(self, client, db_session, seed_user):
        analisis = await _crear_analisis(db_session, seed_user.id, resultado=_resultado_completo())
        await _descargar(client, seed_user, analisis.id)

        r = await client.get(f"/api/analisis/{analisis.id}", headers=_auth(seed_user))

        assert r.status_code == 200
        assert "metadatos_reporte" not in r.json()

    async def test_si_falla_el_registro_el_pdf_se_entrega_igual(self, client, db_session, seed_user):
        analisis = await _crear_analisis(db_session, seed_user.id, resultado=_resultado_completo())

        with patch("app.api.v1.analisis.registrar_generacion_reporte", side_effect=RuntimeError("fallo")):
            r = await _descargar(client, seed_user, analisis.id)

        assert r.content.startswith(b"%PDF")


class TestEstadisticasDeTiempos:
    def test_resumen_de_una_lista_de_tiempos(self):
        from app.services.reportes_service import resumir_tiempos

        resumen = resumir_tiempos([0.4, 0.1, 0.3, 0.2])

        assert resumen["mediciones"] == 4
        assert resumen["promedio"] == pytest.approx(0.25)
        assert resumen["mediana"] == pytest.approx(0.25)
        assert (resumen["minimo"], resumen["maximo"]) == (0.1, 0.4)
        assert resumen["p95"] == 0.4

    def test_percentil_95_con_muchas_mediciones(self):
        from app.services.reportes_service import resumir_tiempos

        resumen = resumir_tiempos([float(i) for i in range(1, 101)])

        assert resumen["p95"] == 95.0
        assert resumen["mediana"] == pytest.approx(50.5)

    def test_sin_mediciones(self):
        from app.services.reportes_service import resumir_tiempos

        assert resumir_tiempos([]) == {"mediciones": 0}

    async def test_estadisticas_de_todos_los_analisis_con_reporte(self, client, db_session, seed_user):
        from app.services.analisis_service import estadisticas_tiempos_reporte

        con_reporte = await _crear_analisis(db_session, seed_user.id, resultado=_resultado_completo())
        await _crear_analisis(db_session, seed_user.id, resultado=_resultado_completo())  # sin descargar
        with patch("app.api.v1.analisis.generar_pdf_y_medir", side_effect=[(b"%PDF", 0.2), (b"%PDF", 0.4)]):
            await _descargar(client, seed_user, con_reporte.id)
            await _descargar(client, seed_user, con_reporte.id)

        datos = await estadisticas_tiempos_reporte(db_session)

        assert datos["analisis_con_reporte"] == 1
        assert datos["total_generaciones"] == 2
        assert datos["resumen"]["promedio"] == pytest.approx(0.3)
        assert datos["por_analisis"][0]["id"] == con_reporte.id
        assert datos["por_analisis"][0]["ultima_generacion_segundos"] == pytest.approx(0.4)

    async def test_el_script_imprime_el_resumen(self, client, db_session, seed_user, capsys, monkeypatch):
        import importlib

        from sqlalchemy.ext.asyncio import async_sessionmaker

        analisis = await _crear_analisis(db_session, seed_user.id, resultado=_resultado_completo())
        with patch("app.api.v1.analisis.generar_pdf_y_medir", return_value=(b"%PDF", 0.25)):
            await _descargar(client, seed_user, analisis.id)
        await db_session.commit()

        script = importlib.import_module("scripts.tiempos_reporte")
        monkeypatch.setattr(script, "AsyncSessionLocal", async_sessionmaker(bind=db_session.bind))
        codigo = await script.main(detalle=True)

        salida = capsys.readouterr().out
        assert codigo == 0
        assert "Reportes generados      : 1" in salida
        assert "Promedio                : 0.2500 s" in salida
        assert f"{analisis.id:>8}" in salida
