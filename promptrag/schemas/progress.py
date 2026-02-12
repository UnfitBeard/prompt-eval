# schemas/progress.py
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class CourseProgressSchema(BaseModel):
    """Per-course aggregate progress for a user.

    This already powers /progress/summary and is reused by the
    dynamic dashboard to build course history.
    """

    course_id: str
    course_title: str
    completed_lessons: int
    total_lessons: int
    progress_percentage: float
    total_xp_earned: int
    current_lesson_id: Optional[str] = None
    started_at: datetime
    last_accessed: datetime


class UserProgressSummarySchema(BaseModel):
    """High-level progress summary for a single user."""

    user_id: str
    total_courses: int
    completed_courses: int
    total_xp: int
    level: str
    streak_days: int
    enrolled_courses: List[CourseProgressSchema]


class AchievementSchema(BaseModel):
    """Represents a badge-style achievement.

    NOTE: The `earned` flag is intentionally included so that both the
    legacy /progress/achievements endpoint and the new /user/badges
    endpoint can expose which badges the user has already unlocked.
    """

    id: str
    name: str
    description: str
    icon: str
    xp_reward: int
    earned: bool = False
    earned_at: Optional[datetime] = None
    progress: Optional[float] = None


class ModuleProgressSchema(BaseModel):
    """Per-module (lesson) progress within a course for a user.

    This is designed to map cleanly onto the frontend's
    `ModuleProgress` interface and static course/module definitions.
    """

    module_id: str
    course_id: str
    title: str
    order: int
    max_xp: int
    xp_earned: int
    status: str  # "not_started" | "in_progress" | "completed"
    score_percentage: Optional[float] = None
    completed_at: Optional[datetime] = None


class CertificateSchema(BaseModel):
    """Represents a user-visible course certificate.

    Backed by the `user_certificates` MongoDB collection (if present).
    The frontend treats `download_url` as a view / download link.
    """

    id: str
    user_id: str
    course_id: str
    title: str
    issued_at: datetime
    download_url: str
