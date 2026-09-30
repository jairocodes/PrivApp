"""El correo no distingue mayúsculas: se guarda y se busca en minúsculas."""

from sqlalchemy import select

from app.models.user import User

REGISTRO = {
    "nombre": "Ana López",
    "email": "  Ana.Lopez@Ejemplo.COM ",
    "password": "Segura123",
    "acepta_aviso": True,
    "declara_edad": True,
}


class TestCorreoSinMayusculas:
    async def test_el_registro_guarda_el_correo_en_minusculas(self, client, db_session):
        r = await client.post("/api/auth/register", json={**REGISTRO, "email": "Ana.Lopez@Ejemplo.COM"})
        assert r.status_code == 201

        user = (await db_session.execute(select(User).where(User.nombre == "Ana López"))).scalar_one()
        assert user.email == "ana.lopez@ejemplo.com"

    async def test_se_inicia_sesion_con_cualquier_combinacion_de_mayusculas(self, client):
        await client.post("/api/auth/register", json={**REGISTRO, "email": "ana.lopez@ejemplo.com"})

        for email in ("ANA.LOPEZ@EJEMPLO.COM", "Ana.Lopez@ejemplo.com"):
            r = await client.post("/api/auth/login", json={"email": email, "password": "Segura123"})
            assert r.status_code == 200, email

    async def test_no_se_puede_registrar_el_mismo_correo_con_otras_mayusculas(self, client):
        primero = await client.post("/api/auth/register", json={**REGISTRO, "email": "ana.lopez@ejemplo.com"})
        segundo = await client.post("/api/auth/register", json={**REGISTRO, "email": "ANA.LOPEZ@ejemplo.com"})

        assert primero.status_code == 201
        assert segundo.status_code == 409

    async def test_promover_administrador_no_distingue_mayusculas(self, client, db_session):
        from app.models.user import ROL_ADMINISTRADOR
        from app.services.auth_service import promover_a_administrador

        await client.post("/api/auth/register", json={**REGISTRO, "email": "ana.lopez@ejemplo.com"})

        user = await promover_a_administrador(db_session, "Ana.Lopez@Ejemplo.com")

        assert user.role == ROL_ADMINISTRADOR


class TestNormalizar:
    def test_quita_espacios_y_mayusculas(self):
        from app.services.auth_service import normalizar_email

        assert normalizar_email("  Ana.Lopez@Ejemplo.COM ") == "ana.lopez@ejemplo.com"
