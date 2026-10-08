"""Configuración para el despliegue en Railway."""

import pytest

from app.config import Settings, normalizar_url_bd


@pytest.mark.parametrize(
    ("url", "esperada"),
    [
        ("postgresql://u:p@host:5432/db", "postgresql+asyncpg://u:p@host:5432/db"),
        ("postgres://u:p@host:5432/db", "postgresql+asyncpg://u:p@host:5432/db"),
        ("postgresql+asyncpg://u:p@db:5432/db", "postgresql+asyncpg://u:p@db:5432/db"),
    ],
)
def test_normaliza_la_url_de_la_base_al_controlador_asincrono(url, esperada):
    assert normalizar_url_bd(url) == esperada


def test_la_configuracion_acepta_la_url_que_entrega_railway(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@pgvector.railway.internal:5432/railway")
    assert Settings().database_url == "postgresql+asyncpg://u:p@pgvector.railway.internal:5432/railway"
