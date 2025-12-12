# api/routers/progress.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List

from core.security import get_current_active_user
from schemas.response import APIResponse
from schemas.progress import UserProgressSummarySchema, AchievementSchema
from services.progress_service import ProgressService
from models.user import UserInDB

router = APIRouter(prefix="/progress", tags=["progress"])
progress_service = ProgressService()


@router.get("/summary", response_model=APIResponse[UserProgressSummarySchema])
async def get_progress_summary(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get user's progress summary"""
    try:
        summary = await progress_service.get_user_progress_summary(str(current_user.id))
        return APIResponse.success(data=summary)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting progress summary: {str(e)}"
        )


@router.get("/activity", response_model=APIResponse[List[dict]])
async def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get user's recent learning activity"""
    activity = await progress_service.get_recent_activity(str(current_user.id), limit)
    return APIResponse.success(data=activity)


@router.get("/streak", response_model=APIResponse[dict])
async def get_streak_data(
    days: int = Query(30, ge=7, le=365),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get user's streak data"""
    streak_data = await progress_service.get_streak_data(str(current_user.id), days)
    return APIResponse.success(data=streak_data)


@router.get("/achievements", response_model=APIResponse[List[AchievementSchema]])
async def get_achievements(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get user's achievements"""
    achievements = await progress_service.get_achievements(str(current_user.id))
    return APIResponse.success(data=achievements)


@router.get("/leaderboard", response_model=APIResponse[List[dict]])
async def get_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get global leaderboard"""
    from services.user_service import UserService
    user_service = UserService()

    leaderboard = await user_service.get_leaderboard(limit)

    # Add user's rank if not in top N
    if current_user:
        all_users = await user_service.collection.find(
            {"is_active": True},
            {"_id": 1, "xp": 1}
        ).sort("xp", -1).to_list(length=None)

        user_rank = next(
            (i + 1 for i, user in enumerate(all_users)
             if str(user["_id"]) == str(current_user.id)),
            None
        )

        if user_rank and user_rank > limit:
            user_data = await user_service.get_user_by_id(str(current_user.id))
            leaderboard.append({
                "rank": user_rank,
                "user_id": str(current_user.id),
                "username": user_data.username,
                "xp": user_data.xp,
                "level": user_data.level.value,
                "streak_days": user_data.streak_days,
                "avatar_url": user_data.avatar_url,
                "is_current_user": True
            })

    return APIResponse.success(data=leaderboard)
