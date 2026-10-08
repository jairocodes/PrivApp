"""Router de autenticación — registro, login, logout, perfil, cambio de contraseña y
eliminación de la propia cuenta."""

import time

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_token_payload, get_current_user
from app.core.limiter import limiter
from app.core.token_revocation import revocar_token
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    ActualizarPerfilRequest,
    CambioPasswordRequest,
    EliminarCuentaRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    actualizar_perfil,
    authenticate_user,
    cambiar_password,
    eliminar_cuenta,
    register_user,
)

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("10/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Registra un nuevo usuario y devuelve un token JWT."""
    _, token = await register_user(
        db, body.nombre, body.email, body.password, body.acepta_aviso, body.declara_edad
    )
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Autentica al usuario y devuelve un token JWT."""
    _, token = await authenticate_user(db, body.email, body.password)
    return TokenResponse(access_token=token)


@router.post("/logout")
async def logout(
    payload: dict = Depends(get_current_token_payload),
    current_user: User = Depends(get_current_user),
):
    """Cierra la sesión revocando el token actual (jti) hasta su expiración natural."""
    jti = payload.get("jti")
    if jti is not None:
        ttl_segundos = max(1, int(payload["exp"] - time.time()))
        await revocar_token(jti, ttl_segundos)
    return {"message": "Sesión cerrada exitosamente."}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Devuelve la información del usuario autenticado actualmente."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def editar_perfil(
    body: ActualizarPerfilRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza el nombre del usuario autenticado; el correo no es editable."""
    return await actualizar_perfil(db, current_user, body.nombre)


@router.delete("/me", status_code=204)
@limiter.limit("5/minute")
async def eliminar_mi_cuenta(
    request: Request,
    body: EliminarCuentaRequest,
    payload: dict = Depends(get_current_token_payload),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Elimina de forma definitiva la cuenta del usuario autenticado y todos sus
    análisis. Los demás tokens dejan de servir porque la cuenta ya no existe; el
    actual se revoca además de forma explícita."""
    await eliminar_cuenta(db, current_user, body.password)
    await db.commit()
    jti = payload.get("jti")
    if jti is not None:
        await revocar_token(jti, max(1, int(payload["exp"] - time.time())))
    return Response(status_code=204)


@router.post("/change-password", response_model=TokenResponse)
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    body: CambioPasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cambia la contraseña: cierra todas las sesiones y devuelve un token nuevo
    para la sesión actual."""
    token = await cambiar_password(db, current_user, body.password_actual, body.password_nueva)
    return TokenResponse(access_token=token)
