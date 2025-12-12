# schemas/lesson.py
from typing import Optional, List, Dict, Any, Union
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
