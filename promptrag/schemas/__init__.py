# schemas/__init__.py
from .user import (
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
