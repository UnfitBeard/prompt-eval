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
from core.security import require_role, get_current_active_user

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


@router.get("/me", response_model=APIResponse[UserResponseSchema])
async def me(current_user: UserInDB = Depends(get_current_active_user)):
    """Return the current authenticated user.

    The Angular frontend calls this on page load to hydrate the user session.
    """

    return APIResponse(
        success=True,
        data=UserResponseSchema.from_orm(current_user),
    )


@router.post("/refresh", response_model=APIResponse[TokenResponseSchema])
async def refresh(
    payload: RefreshTokenSchema,
    user_service: UserService = Depends(),
):
    """Exchange a refresh token for a new access token (and refresh token).

    The Angular app stores the refresh token in localStorage and posts it here.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        decoded = jwt.decode(
            payload.refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if decoded.get("type") != "refresh":
            raise credentials_exception

        user_id: str = decoded.get("sub")
        if not user_id:
            raise credentials_exception

        user = await user_service.get_user_by_id(user_id)
        if user is None or not user.is_active:
            raise credentials_exception

        access_token, refresh_token = user_service.create_tokens_for_user(user)

        return APIResponse(
            success=True,
            data=TokenResponseSchema(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=UserResponseSchema.from_orm(user),
            ),
            message="Token refreshed",
        )

    except JWTError:
        raise credentials_exception


@router.get("/admin/bootstrap", response_model=APIResponse[dict])
async def admin_bootstrap_status(user_service: UserService = Depends()):
    """Return whether the system is in "bootstrap" mode.

    Bootstrap mode is enabled only when *no* admin user exists yet.
    """

    enabled = not await user_service.any_admin_exists()
    return APIResponse(success=True, data={"enabled": enabled})


@router.post("/admin/bootstrap", response_model=APIResponse[UserResponseSchema])
async def bootstrap_admin(
    user_data: UserCreateSchema,
    user_service: UserService = Depends(),
):
    """Create the first admin user.

    This endpoint is intentionally unauthenticated, but only works when there are
    zero admins. Once an admin exists, it returns 403.
    """

    if await user_service.any_admin_exists():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin already exists; bootstrap disabled",
        )

    try:
        user = await user_service.create_admin_user(user_data)

        return APIResponse(
            success=True,
            data=UserResponseSchema.from_orm(user),
            message="Admin bootstrap successful",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception:
        logger.exception("Admin bootstrap failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin bootstrap failed" if not settings.DEBUG else "Admin bootstrap failed",
        )


@router.post("/admin/register", response_model=APIResponse[UserResponseSchema])
async def register_admin(
    user_data: UserCreateSchema,
    _: UserInDB = Depends(require_role("admin")),
    user_service: UserService = Depends(),
):
    """Register a new admin user (admin-only)."""
    try:
        user = await user_service.create_admin_user(user_data)

        return APIResponse(
            success=True,
            data=UserResponseSchema.from_orm(user),
            message="Admin registration successful",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Admin registration failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) if settings.DEBUG else "Admin registration failed",
        )
