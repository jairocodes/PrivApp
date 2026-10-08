"""Tests de la eliminación definitiva de análisis (DELETE /api/analisis/{id})."""

from sqlalchemy import func, select

from app.models.analysis import AnalysisTemp
from tests.test_historial_filtros import _auth, _otro_usuario
from tests.test_reportes import _crear_analisis


async def _existe(db_session, analisis_id: int) -> bool:
    total = await db_session.scalar(
        select(func.count()).select_from(AnalysisTemp).where(AnalysisTemp.id == analisis_id)
    )
    return total == 1


class TestEliminacionDeAnalisis:
    async def test_elimina_un_analisis_propio_de_forma_definitiva(self, client, db_session, seed_user):
        analisis = await _crear_analisis(db_session, seed_user.id, comentario="Para borrar")

        r = await client.delete(f"/api/analisis/{analisis.id}", headers=_auth(seed_user))

        assert r.status_code == 204
        assert r.content == b""
        assert not await _existe(db_session, analisis.id)

    async def test_el_analisis_eliminado_desaparece_del_historial_y_del_detalle(
        self, client, db_session, seed_user
    ):
        conservado = await _crear_analisis(db_session, seed_user.id, comentario="Conservado")
        borrado = await _crear_analisis(db_session, seed_user.id, comentario="Borrado")

        await client.delete(f"/api/analisis/{borrado.id}", headers=_auth(seed_user))

        historial = (await client.get("/api/analisis", headers=_auth(seed_user))).json()
        assert [i["id_analisis"] for i in historial["items"]] == [str(conservado.id)]
        assert historial["total"] == 1
        assert (await client.get(f"/api/analisis/{borrado.id}", headers=_auth(seed_user))).status_code == 404
        assert (await client.get(f"/api/analisis/{borrado.id}/pdf", headers=_auth(seed_user))).status_code == 404

    async def test_eliminar_un_analisis_ajeno_se_rechaza_sin_borrarlo(self, client, db_session, seed_user):
        otro = await _otro_usuario(db_session)
        ajeno = await _crear_analisis(db_session, otro.id, comentario="Ajeno")

        r = await client.delete(f"/api/analisis/{ajeno.id}", headers=_auth(seed_user))

        assert r.status_code == 404
        assert await _existe(db_session, ajeno.id)

    async def test_analisis_inexistente_devuelve_404(self, client, seed_user):
        r = await client.delete("/api/analisis/99999", headers=_auth(seed_user))
        assert r.status_code == 404

    async def test_un_analisis_en_curso_no_se_elimina(self, client, db_session, seed_user):
        en_curso = await _crear_analisis(db_session, seed_user.id, estado="procesando")

        r = await client.delete(f"/api/analisis/{en_curso.id}", headers=_auth(seed_user))

        assert r.status_code == 409
        assert await _existe(db_session, en_curso.id)

    async def test_un_analisis_con_error_se_puede_eliminar(self, client, db_session, seed_user):
        fallido = await _crear_analisis(db_session, seed_user.id, estado="error")

        r = await client.delete(f"/api/analisis/{fallido.id}", headers=_auth(seed_user))

        assert r.status_code == 204
        assert not await _existe(db_session, fallido.id)

    async def test_requiere_sesion(self, client, db_session, seed_user):
        analisis = await _crear_analisis(db_session, seed_user.id)
        r = await client.delete(f"/api/analisis/{analisis.id}")
        assert r.status_code == 403
