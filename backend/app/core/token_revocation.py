"""Lista de revocación de tokens JWT (jti) respaldada por Redis (TICKET-03).

El estado vive en Redis (compartido entre instancias), no en memoria del
proceso, para respetar el diseño stateless del servidor (RE-01). El TTL de
cada entrada es el tiempo restante de vigencia del token, así la lista se
limpia sola sin necesidad de un proceso periódico aparte.
"""

import redis.asyncio as redis

from app.config import settings

_PREFIX = "revoked_jti:"
_client: redis.Redis | None = None


def _get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def revocar_token(jti: str, ttl_segundos: int) -> None:
    """Marca un jti como revocado durante ttl_segundos (tiempo restante hasta su exp)."""
    if ttl_segundos <= 0:
        return
    await _get_client().set(f"{_PREFIX}{jti}", "1", ex=ttl_segundos)


async def token_esta_revocado(jti: str) -> bool:
    return await _get_client().exists(f"{_PREFIX}{jti}") == 1
