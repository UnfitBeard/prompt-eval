# schemas/user.py
from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from models.user import UserRole, UserLevel


class UserCreateSchema(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserLoginSchema(BaseModel):
    username: str
    password: str


class UserUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    level: Optional[UserLevel] = None


class UserResponseSchema(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    role: UserRole
    level: UserLevel
    xp: int
    streak_days: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponseSchema


class RefreshTokenSchema(BaseModel):
    refresh_token: str
