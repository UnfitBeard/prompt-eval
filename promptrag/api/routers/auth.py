# api/routers/auth.py - FIXED
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from jose import JWTError, jwt
import logging

from config import settings
from schemas.user import (
    UserCreateSchema,
    UserResponseSchema,
    TokenResponseSchema,
    RefreshTokenSchema
)
from schemas.response import APIResponse  # Make sure this exists
from services.user_service import UserService
from models.user import UserInDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Define oauth2_scheme here
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False
)


@router.post("/register", response_model=APIResponse[UserResponseSchema])
async def register(
    user_data: UserCreateSchema,
    user_service: UserService = Depends()
):
    """Register a new user"""
    try:
        user = await user_service.create_user(user_data)

        return APIResponse(
            success=True,
            data=UserResponseSchema.from_orm(user),
            message="Registration successful"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Registration failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) if settings.DEBUG else "Registration failed"
        )


@router.post("/login", response_model=APIResponse[TokenResponseSchema])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends()
):
    """Login and get access token"""
    user = await user_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens using user_service method
    access_token, refresh_token = user_service.create_tokens_for_user(user)

    return APIResponse(
        success=True,
        data=TokenResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponseSchema.from_orm(user)
        ),
        message="Login successful"
    )
