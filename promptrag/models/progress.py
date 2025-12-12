# models/progress.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class AttemptStatus(str, Enum):
    PENDING = "pending"
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIAL = "partial"


class UserProgressBase(BaseModel):
    user_id: str
    course_id: str
    current_lesson_id: Optional[str] = None
    completed_lessons: List[str] = []
    total_xp_earned: int = 0
    started_at: datetime
    last_accessed: datetime
    completed: bool = False
    completed_at: Optional[datetime] = None


class LessonAttempt(BaseModel):
    id: str
    user_id: str
    lesson_id: str
    course_id: str
    answers: Dict[str, Any]  # Question ID -> answer
    xp_earned: int = 0
    status: AttemptStatus
    time_spent_seconds: int = 0
    feedback: Optional[str] = None
    created_at: datetime
