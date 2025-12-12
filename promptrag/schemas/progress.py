# schemas/progress.py
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class CourseProgressSchema(BaseModel):
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
    user_id: str
    total_courses: int
    completed_courses: int
    total_xp: int
    level: str
    streak_days: int
    enrolled_courses: List[CourseProgressSchema]


class AchievementSchema(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    xp_reward: int
    earned_at: Optional[datetime] = None
    progress: Optional[float] = None
