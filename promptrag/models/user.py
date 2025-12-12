# models/user.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from enum import Enum


class UserRole(str, Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


class UserLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    level: UserLevel = UserLevel.BEGINNER


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    id: str
    hashed_password: str
    role: UserRole = UserRole.STUDENT
    xp: int = 0
    streak_days: int = 0
    last_active: datetime
    created_at: datetime
    updated_at: datetime
    email_verified: bool = False
    is_active: bool = True

    class Config:
        from_attributes = True


class UserPublic(UserBase):
    id: str
    role: UserRole
    xp: int
    level: UserLevel
    streak_days: int
    created_at: datetime
