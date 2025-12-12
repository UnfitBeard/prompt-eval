# api/routers/courses.py - FIXED WITH CORRECT APIResponse USAGE
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import logging

from core.security import get_current_user
from models.user import UserInDB
from schemas.course import CourseCreateSchema, CourseResponseSchema, CourseListResponseSchema
from schemas.response import APIResponse
from services.course_service import CourseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses", tags=["courses"])
course_service = CourseService()


@router.get("/", response_model=APIResponse[CourseListResponseSchema])
async def get_courses(
    difficulty: Optional[str] = Query(
        None, description="Filter by difficulty"),
    limit: int = Query(12, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: Optional[UserInDB] = Depends(get_current_user)
):
    """Get list of courses"""
    try:
        courses = await course_service.get_courses(
            difficulty=difficulty,
            limit=limit,
            skip=skip,
            user_id=str(current_user.id) if current_user else None
        )

        # Use the count_courses method instead of accessing collection directly
        total = await course_service.count_courses(difficulty=difficulty)

        # Create APIResponse instance directly
        return APIResponse(
            success=True,
            message="Courses fetched successfully",
            data={
                "courses": courses,
                "total": total,
                "limit": limit,
                "skip": skip
            }
        )
    except Exception as e:
        logger.error(f"Error in get_courses endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching courses: {str(e)}"
        )


@router.get("/{course_id}", response_model=APIResponse[CourseResponseSchema])
async def get_course(
    course_id: str,
    current_user: Optional[UserInDB] = Depends(get_current_user)
):
    """Get course by ID"""
    try:
        course = await course_service.get_course(
            course_id,
            user_id=str(current_user.id) if current_user else None
        )

        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )

        # Create APIResponse instance directly
        return APIResponse(
            success=True,
            message="Course fetched successfully",
            data=course
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_course endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching course: {str(e)}"
        )


@router.post("/{course_id}/enroll", response_model=APIResponse[dict])
async def enroll_in_course(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Enroll current user in a course"""
    if current_user.role not in ["student", "instructor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students and instructors can enroll in courses"
        )

    success = await course_service.enroll_user(course_id, str(current_user.id))

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to enroll in course"
        )

    # Create APIResponse instance directly
    return APIResponse(
        success=True,
        message="Enrollment successful",
        data={"message": "Successfully enrolled in course"}
    )


@router.get("/{course_id}/progress", response_model=APIResponse[dict])
async def get_course_progress(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get user's progress in a course"""
    try:
        # Get progress collection
        progress_col = await course_service.progress_collection
        progress = await progress_col.find_one({
            "user_id": str(current_user.id),
            "course_id": course_id
        })

        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not enrolled in this course"
            )

        # Get course details
        course = await course_service.get_course(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )

        # Calculate progress
        total_lessons = course.total_lessons
        completed_lessons = len(progress.get("completed_lessons", []))

        # Create APIResponse instance directly
        return APIResponse(
            success=True,
            data={
                "course_id": course_id,
                "course_title": course.title,
                "completed_lessons": completed_lessons,
                "total_lessons": total_lessons,
                "progress_percentage": (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0,
                "total_xp_earned": progress.get("total_xp_earned", 0),
                "current_lesson_id": progress.get("current_lesson_id"),
                "started_at": progress.get("started_at"),
                "last_accessed": progress.get("last_accessed")
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting course progress: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching course progress: {str(e)}"
        )
