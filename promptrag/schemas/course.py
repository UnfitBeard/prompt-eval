# schemas/course.py - UPDATED TO MATCH CoursePublic
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from models.course import CourseDifficulty, CourseStatus, CourseCategory


class CourseCreateSchema(BaseModel):
    title: str
    slug: str
    description: str
    short_description: str
    difficulty: CourseDifficulty = CourseDifficulty.BEGINNER
    tags: List[str] = []
    total_duration: float = 1.0  # Changed from estimated_hours
    thumbnail_url: Optional[str] = None
    prerequisites: List[str] = []


class CourseUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    difficulty: Optional[CourseDifficulty] = None
    tags: Optional[List[str]] = None
    total_duration: Optional[float] = None  # Changed from estimated_hours
    thumbnail_url: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    status: Optional[CourseStatus] = None


class CourseResponseSchema(BaseModel):
    id: str
    title: str
    slug: str
    description: str
    short_description: str
    difficulty: str
    status: str
    category: str
    instructor_id: str
    instructor_name: str
    language: str = "english"
    thumbnail_url: Optional[str] = None
    total_lessons: int
    total_duration: float  # Changed from estimated_hours
    enrolled_count: int
    review_count: int
    average_rating: float  # Changed from avg_rating
    xp_reward: int  # Changed from total_xp
    tags: List[str]
    learning_outcomes: List[str] = []
    prerequisites: List[str]
    price: float = 0.0
    created_at: datetime
    updated_at: datetime
    lesson_order: List[str] = []
    progress_percentage: Optional[float] = None

    class Config:
        from_attributes = True


class CourseListResponseSchema(BaseModel):
    courses: List[CourseResponseSchema]
    total: int
    limit: int
    skip: int
