"""Router de autenticación — registro, login, logout y perfil del usuario."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.limiter import limiter
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import authenticate_user, register_user

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("10/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Registra un nuevo usuario y devuelve un token JWT."""
    _, token = await register_user(db, body.nombre, body.email, body.password)
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
async def logout(current_user: User = Depends(get_current_user)):
    """Cierre de sesión — la invalidación del token es responsabilidad del cliente."""
    return {"message": "Sesión cerrada exitosamente."}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Devuelve la información del usuario autenticado actualmente."""
    return current_user
