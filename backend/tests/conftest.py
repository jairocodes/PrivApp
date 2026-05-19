"""Configuración global de pytest con base de datos SQLite en memoria para tests."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.database import get_db
from app.main import app
from app.models.analysis import AnalysisTemp
from app.models.user import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
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
    )
    db_session.add(user)
    await db_session.flush()
    return user


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
