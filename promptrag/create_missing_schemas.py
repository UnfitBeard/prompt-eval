# create_missing_schemas.py
import os
import sys

# Create schemas directory if it doesn't exist
os.makedirs("schemas", exist_ok=True)

# List of schema files to create
schemas = {
    "course.py": """from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from models.course import CourseDifficulty, CourseStatus

class CourseCreateSchema(BaseModel):
    title: str
    slug: str
    description: str
    short_description: str
    difficulty: CourseDifficulty = CourseDifficulty.BEGINNER
    tags: List[str] = []
    estimated_hours: int = 1
    thumbnail_url: Optional[str] = None
    prerequisites: List[str] = []

class CourseUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    difficulty: Optional[CourseDifficulty] = None
    tags: Optional[List[str]] = None
    estimated_hours: Optional[int] = None
    thumbnail_url: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    status: Optional[CourseStatus] = None

class CourseResponseSchema(BaseModel):
    id: str
    title: str
    slug: str
    description: str
    short_description: str
    difficulty: CourseDifficulty
    tags: List[str]
    estimated_hours: int
    thumbnail_url: Optional[str] = None
    prerequisites: List[str]
    instructor_id: str
    instructor_name: str
    status: CourseStatus
    total_lessons: int
    total_xp: int
    enrolled_count: int
    avg_rating: Optional[float] = None
    review_count: int
    created_at: datetime
    progress_percentage: Optional[float] = None
    
    class Config:
        from_attributes = True

class CourseListResponseSchema(BaseModel):
    courses: List[CourseResponseSchema]
    total: int
    limit: int
    skip: int
""",

    "lesson.py": """from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel
from datetime import datetime

from models.lesson import LessonType, QuestionType

class QuestionOptionSchema(BaseModel):
    id: str
    text: str
    is_correct: bool = False
    explanation: Optional[str] = None

class LessonQuestionSchema(BaseModel):
    id: str
    type: QuestionType
    question: str
    description: Optional[str] = None
    options: Optional[List[QuestionOptionSchema]] = None
    correct_answer: Optional[Union[str, List[str]]] = None
    hint: Optional[str] = None
    explanation: Optional[str] = None
    xp_reward: int = 10
    code_template: Optional[str] = None
    test_cases: Optional[List[Dict]] = None
    difficulty: str = "easy"

class LessonContentSchema(BaseModel):
    type: LessonType
    content: Dict[str, Any]

class LessonCreateSchema(BaseModel):
    title: str
    slug: str
    description: str
    course_id: str
    order: int
    content: LessonContentSchema
    questions: List[LessonQuestionSchema] = []
    estimated_minutes: int = 15
    prerequisites: List[str] = []
    tags: List[str] = []

class LessonResponseSchema(BaseModel):
    id: str
    title: str
    slug: str
    description: str
    course_id: str
    order: int
    content: LessonContentSchema
    questions: List[LessonQuestionSchema]
    estimated_minutes: int
    prerequisites: List[str]
    tags: List[str]
    total_xp: int
    completed_count: int
    is_completed: Optional[bool] = None
    user_xp_earned: Optional[int] = None
    next_lesson_id: Optional[str] = None
    prev_lesson_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class LessonAttemptRequestSchema(BaseModel):
    answers: Dict[str, Any]
    time_spent_seconds: int = 0

class LessonAttemptResponseSchema(BaseModel):
    attempt_id: str
    correct_answers: int
    total_questions: int
    score_percentage: float
    xp_earned: int
    status: str
    feedback: List[str]
    next_lesson_id: Optional[str] = None
""",

    "progress.py": """from typing import Optional, List
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
""",

    "user.py": """from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from models.user import UserRole, UserLevel

class UserCreateSchema(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserLoginSchema(BaseModel):
    username: str
    password: str

class UserUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    level: Optional[UserLevel] = None

class UserResponseSchema(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    role: UserRole
    level: UserLevel
    xp: int
    streak_days: int
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponseSchema

class RefreshTokenSchema(BaseModel):
    refresh_token: str
"""
}

# Create each schema file
for filename, content in schemas.items():
    filepath = os.path.join("schemas", filename)

    # Check if file already exists
    if os.path.exists(filepath):
        print(f"⚠️ {filename} already exists, skipping...")
    else:
        with open(filepath, "w") as f:
            f.write(content)
        print(f"✅ Created {filename}")

# Create __init__.py for schemas
init_content = """from .user import (
    UserCreateSchema, UserLoginSchema, UserUpdateSchema,
    UserResponseSchema, TokenResponseSchema, RefreshTokenSchema
)
from .course import (
    CourseCreateSchema, CourseUpdateSchema, 
    CourseResponseSchema, CourseListResponseSchema
)
from .lesson import (
    LessonCreateSchema, LessonResponseSchema,
    LessonAttemptRequestSchema, LessonAttemptResponseSchema,
    LessonQuestionSchema, QuestionOptionSchema, LessonContentSchema
)
from .progress import (
    CourseProgressSchema, UserProgressSummarySchema,
    AchievementSchema
)
from .response import (
    APIResponse, PaginatedResponse, ErrorResponse, HealthResponse
)

__all__ = [
    # User schemas
    "UserCreateSchema", "UserLoginSchema", "UserUpdateSchema",
    "UserResponseSchema", "TokenResponseSchema", "RefreshTokenSchema",
    
    # Course schemas
    "CourseCreateSchema", "CourseUpdateSchema",
    "CourseResponseSchema", "CourseListResponseSchema",
    
    # Lesson schemas
    "LessonCreateSchema", "LessonResponseSchema",
    "LessonAttemptRequestSchema", "LessonAttemptResponseSchema",
    "LessonQuestionSchema", "QuestionOptionSchema", "LessonContentSchema",
    
    # Progress schemas
    "CourseProgressSchema", "UserProgressSummarySchema", "AchievementSchema",
    
    # Response schemas
    "APIResponse", "PaginatedResponse", "ErrorResponse", "HealthResponse"
]
"""

with open("schemas/__init__.py", "w") as f:
    f.write(init_content)

print("✅ Created schemas/__init__.py")
print("\n🎉 All schema files have been created!")
print("\nNow try running: uvicorn server:app --reload --port 8000")
