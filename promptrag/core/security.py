# core/security.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import logging

from config import settings
from models.user import UserInDB, UserRole
from core.password import verify_password, get_password_hash

logger = logging.getLogger(__name__)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False
)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[UserInDB]:
    """Get current user from JWT token"""
    if not token:
        return None

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        if payload.get("type") != "access":
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Import here to avoid circular import
        from services.user_service import UserService
        user_service = UserService()
        user = await user_service.get_user_by_id(user_id)

        if user is None or not user.is_active:
            raise credentials_exception

        return user

    except JWTError as e:
        logger.error(f"JWT error: {e}")
        raise credentials_exception


async def get_current_active_user(
    current_user: Optional[UserInDB] = Depends(get_current_user)
) -> UserInDB:
    """Get current active user (requires authentication)"""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return current_user


def require_role(required_role: str):
    """Dependency to require specific user role.

    Admin users are always allowed, otherwise the user's role must
    match the required role.
    """

    async def role_checker(
        current_user: UserInDB = Depends(get_current_active_user)
    ) -> UserInDB:
        # Normalize role values in case they are enums
        user_role = getattr(current_user.role, "value", current_user.role)
        admin_value = getattr(UserRole.ADMIN, "value", "admin")

        if user_role != required_role and user_role != admin_value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role",
            )
        return current_user

    return role_checker
