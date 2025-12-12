# models/course.py - CORRECTED VERSION
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from bson import ObjectId


class CourseDifficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CourseStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class CourseCategory(str, Enum):
    AI = "ai"
    PROGRAMMING = "programming"
    DATA_SCIENCE = "data_science"
    WEB_DEV = "web_dev"
    MOBILE = "mobile"
    GAME_DEV = "game_dev"
    OTHER = "other"


class CourseBase(BaseModel):
    title: str
    slug: str
    description: str
    short_description: str
    difficulty: CourseDifficulty
    status: CourseStatus = CourseStatus.DRAFT
    category: CourseCategory = CourseCategory.AI
    instructor_id: str
    language: str = "english"
    thumbnail_url: Optional[str] = None
    total_lessons: int = 0
    total_duration: float = 0.0  # MongoDB field name (not estimated_hours)
    enrolled_count: int = 0
    review_count: int = 0
    average_rating: float = 0.0
    xp_reward: int = 0  # MongoDB field name (not total_xp)
    tags: List[str] = []
    learning_outcomes: List[str] = []
    prerequisites: List[str] = []
    price: float = 0.0


class CourseCreate(CourseBase):
    pass


class CourseInDB(CourseBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    lesson_order: List[str] = []

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str
        }


class CoursePublic(BaseModel):
    id: str
    title: str
    slug: str
    description: str
    short_description: str
    difficulty: str
    status: str
    category: str
    instructor_id: str
    instructor_name: Optional[str] = "Unknown"
    language: str
    thumbnail_url: Optional[str] = None
    total_lessons: int
    total_duration: float  # Use this field name (not estimated_hours)
    enrolled_count: int
    review_count: int
    average_rating: float
    xp_reward: int  # Use this field name (not total_xp)
    tags: List[str]
    learning_outcomes: List[str]
    prerequisites: List[str]
    price: float
    created_at: datetime
    updated_at: datetime
    lesson_order: List[str] = []
    progress_percentage: Optional[float] = None

    class Config:
        allow_population_by_field_name = True

    @validator('difficulty', 'status', 'category', pre=True)
    def convert_enum_to_string(cls, v):
        if isinstance(v, Enum):
            return v.value
        return v
