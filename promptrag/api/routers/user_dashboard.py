# api/routers/user_dashboard.py
"""User-centric dashboard endpoints.

These endpoints are designed specifically for the dynamic user progress
dashboard in the Angular frontend. They wrap existing progress logic
and expose:

- Overall progress + course history
- Per-course module (lesson) progress
- Badge-style achievements ("badges")
- Certificates (if any exist)
"""

from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from core.security import get_current_active_user
from models.user import UserInDB
from schemas.response import APIResponse
from schemas.progress import (
    UserProgressSummarySchema,
    ModuleProgressSchema,
    AchievementSchema,
    CertificateSchema,
)
from services.progress_service import ProgressService


router = APIRouter(prefix="/user", tags=["user-dashboard"])
progress_service = ProgressService()


@router.get("/progress", response_model=APIResponse[Dict[str, Any]])
async def get_user_progress(current_user: UserInDB = Depends(get_current_active_user)):
    """Return high-level progress summary for the current user.

    The payload intentionally wraps the existing UserProgressSummarySchema
    under a `summary` key so the frontend can both:
    - reuse this structure, and
    - compute additional inferred statistics on the client side.
    """

    try:
        summary: UserProgressSummarySchema = await progress_service.get_user_progress_summary(
            str(current_user.id)
        )
        # Construct APIResponse directly to avoid relying on the classmethod,
        # which conflicts with the `success` field name in Pydantic v2.
        return APIResponse(
            success=True,
            data={"summary": summary},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user progress: {str(e)}",
        )


@router.get(
    "/courses/{course_id}/modules",
    response_model=APIResponse[List[ModuleProgressSchema]],
)
async def get_course_modules(
    course_id: str, current_user: UserInDB = Depends(get_current_active_user)
):
    """Return per-module progress for the given course.

    A "module" in the dashboard corresponds to a `lesson` document in
    the MongoDB `lessons` collection.
    """

    try:
        modules = await progress_service.get_course_modules_for_user(
            user_id=str(current_user.id), course_id=course_id
        )
        return APIResponse(
            success=True,
            data=modules,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting course modules: {str(e)}",
        )


@router.get("/badges", response_model=APIResponse[List[AchievementSchema]])
async def get_user_badges(current_user: UserInDB = Depends(get_current_active_user)):
    """Expose achievements as badge-like objects for the dashboard UI."""

    achievements = await progress_service.get_achievements(str(current_user.id))
    # get_achievements already returns a list of dicts with the same
    # shape as AchievementSchema (plus some extra keys which Pydantic
    # will ignore on output).
    return APIResponse(
        success=True,
        data=achievements,
    )


@router.get("/certificates", response_model=APIResponse[List[CertificateSchema]])
async def get_user_certificates(
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Return certificates for the current user, if any.

    If the `user_certificates` collection is empty, this simply
    returns an empty list so the frontend can show a helpful
    "no certificates yet" message.
    """

    try:
        certificates = await progress_service.get_user_certificates(
            str(current_user.id)
        )
        return APIResponse(
            success=True,
            data=certificates,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting certificates: {str(e)}",
        )
