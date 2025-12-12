# api/routers/lessons.py - FIXED
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import List, Optional, Dict, Any
from bson import ObjectId

from core.security import get_current_user
from models.user import UserInDB
from schemas.lesson import LessonResponseSchema, LessonAttemptRequestSchema, LessonAttemptResponseSchema
from schemas.response import APIResponse
from services.lesson_service import LessonService

router = APIRouter(prefix="/lessons", tags=["lessons"])
lesson_service = LessonService()


@router.get("/{lesson_id}", response_model=APIResponse[LessonResponseSchema])
async def get_lesson(
    lesson_id: str,
    current_user: Optional[UserInDB] = Depends(get_current_user)
):
    """Get lesson by ID"""
    lesson = await lesson_service.get_lesson(
        lesson_id,
        user_id=str(current_user.id) if current_user else None
    )

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    return APIResponse.success(data=lesson)


@router.post("/{lesson_id}/attempt", response_model=APIResponse[LessonAttemptResponseSchema])
async def submit_lesson_attempt(
    lesson_id: str,
    attempt: LessonAttemptRequestSchema,
    current_user: UserInDB = Depends(get_current_user)
):
    """Submit lesson attempt and get results"""
    try:
        result = await lesson_service.submit_lesson_attempt(
            lesson_id=lesson_id,
            user_id=str(current_user.id),
            answers=attempt.answers,
            time_spent=attempt.time_spent_seconds
        )

        return APIResponse.success(
            data=result,
            message="Lesson attempt submitted successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting attempt: {str(e)}"
        )


@router.get("/{lesson_id}/attempts", response_model=APIResponse[List[Dict]])
async def get_lesson_attempts(
    lesson_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get user's attempts for a lesson"""
    await lesson_service._ensure_connected()

    attempts = await lesson_service.attempts_collection.find({
        "user_id": str(current_user.id),
        "lesson_id": lesson_id
    }).sort("created_at", -1).limit(limit).to_list(length=limit)

    # Convert ObjectId to string
    for attempt in attempts:
        attempt["id"] = str(attempt["_id"])
        del attempt["_id"]

    return APIResponse.success(data=attempts)


@router.post("/{lesson_id}/complete", response_model=APIResponse[dict])
async def mark_lesson_completed(
    lesson_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Manually mark lesson as completed (for theory lessons without questions)"""
    await lesson_service._ensure_connected()

    # Get lesson to check if it's a theory lesson
    lesson = await lesson_service.collection.find_one({"_id": ObjectId(lesson_id)})
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    # Only allow marking theory lessons as completed
    if lesson.get("content", {}).get("type") != "theory":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only theory lessons can be manually completed"
        )

    # Mark as completed with minimal XP
    await lesson_service._mark_lesson_completed(
        user_id=str(current_user.id),
        course_id=lesson["course_id"],
        lesson_id=lesson_id,
        xp_earned=5  # Small reward for reading
    )

    return APIResponse.success(
        data={"message": "Lesson marked as completed"},
        message="Lesson completed!"
    )
