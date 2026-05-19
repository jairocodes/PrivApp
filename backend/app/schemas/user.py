"""Schemas Pydantic para datos de usuario."""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    nombre: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
