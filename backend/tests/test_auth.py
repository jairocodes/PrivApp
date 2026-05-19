"""Tests del módulo de autenticación. Implementación completa en Sprint 1."""

import pytest


@pytest.mark.asyncio
async def test_healthcheck(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# TODO Sprint 1: implementar tests
# - test_registro_exitoso
# - test_registro_email_duplicado
# - test_login_exitoso
# - test_login_credenciales_invalidas
# - test_ruta_protegida_sin_token
# - test_ruta_protegida_con_token_valido
