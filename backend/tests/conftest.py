"""Configuración global de pytest con base de datos SQLite en memoria para tests."""

from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.limiter import limiter
from app.core.security import hash_password
from app.database import get_db
from app.main import app
from app.models.analysis import AnalysisTemp
from app.models.user import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def test_engine(monkeypatch):
    # StaticPool: una sola conexión física compartida por todas las sesiones
    # de la prueba, para que la sesión independiente que abre la tarea de
    # fondo (app.database.AsyncSessionLocal, ver HU-13) vea la misma base en
    # memoria que la sesión de la request (sin esto, cada sesión nueva sobre
    # sqlite ":memory:" obtendría una base vacía y aislada).
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=StaticPool)
    monkeypatch.setattr(
        "app.database.AsyncSessionLocal",
        async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False),
    )
    async with engine.begin() as conn:
        # corpus_chunks usa pgvector (incompatible con SQLite), se omite
        await conn.run_sync(User.__table__.create, checkfirst=True)
        await conn.run_sync(AnalysisTemp.__table__.create, checkfirst=True)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(AnalysisTemp.__table__.drop, checkfirst=True)
        await conn.run_sync(User.__table__.drop, checkfirst=True)
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine):
    session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture(scope="function")
async def seed_user(db_session: AsyncSession) -> User:
    """Inserta el usuario de prueba con id=1 para tests que usan create_access_token('1')."""
    user = User(
        nombre="Test User",
        email="test@privapp.test",
        hashed_password=hash_password("TestPass123"),
        is_active=True,
        privacy_accepted_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.flush()
    return user


class FakeRedis:
    """Redis en memoria para tests: solo lo mínimo que usa token_revocation.py."""

    def __init__(self):
        self._store: dict[str, str] = {}

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value

    async def exists(self, key: str) -> int:
        return 1 if key in self._store else 0


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    monkeypatch.setattr("app.core.token_revocation._client", FakeRedis())


@pytest.fixture(autouse=True)
def dns_publico(monkeypatch):
    # Las pruebas no consultan el DNS real: todo sitio resuelve a una IP pública
    # de documentación. Las pruebas de direcciones internas lo sustituyen.
    monkeypatch.setattr("app.services.ingesta_service._resolver_ips", lambda host: ["93.184.216.34"])


@pytest.fixture(autouse=True)
def version_corpus_fija(monkeypatch):
    # La huella del corpus consulta corpus_chunks, que no existe en SQLite; las
    # pruebas de reutilización la cambian para simular un corpus distinto.
    async def _version(db):
        return "corpus-de-prueba"

    monkeypatch.setattr("app.services.analisis_service._version_corpus", _version)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    # El limiter (slowapi) es un singleton en memoria compartido por toda la
    # sesión de pytest; sin este reset, las pruebas que llaman a endpoints
    # limitados (ej. /api/auth/register) acumulan conteo entre tests y
    # pueden empezar a fallar con 429 según el orden/cantidad de pruebas.
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession, seed_user: User):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
