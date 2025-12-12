# models/lesson.py
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class LessonType(str, Enum):
    THEORY = "theory"
    PRACTICE = "practice"
    PROJECT = "project"
    QUIZ = "quiz"


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SINGLE_CHOICE = "single_choice"
    CODE = "code"
    TEXT = "text"
    TRUE_FALSE = "true_false"


class LessonContent(BaseModel):
    type: LessonType
    content: Dict[str, Any]  # Flexible content structure


class QuestionOption(BaseModel):
    id: str
    text: str
    is_correct: bool = False
    explanation: Optional[str] = None


class LessonQuestion(BaseModel):
    id: str
    type: QuestionType
    question: str
    description: Optional[str] = None
    options: Optional[List[QuestionOption]] = None
    correct_answer: Optional[Union[str, List[str]]] = None
    hint: Optional[str] = None
    explanation: Optional[str] = None
    xp_reward: int = 10
    code_template: Optional[str] = None  # For code questions
    test_cases: Optional[List[Dict]] = None  # For code questions
    difficulty: str = "easy"


class LessonBase(BaseModel):
    title: str
    slug: str
    description: str
    course_id: str
    order: int  # Order within course
    content: LessonContent
    questions: List[LessonQuestion] = []
    estimated_minutes: int = 15
    prerequisites: List[str] = []  # Previous lesson IDs
    tags: List[str] = []


class LessonCreate(LessonBase):
    pass


class LessonInDB(LessonBase):
    id: str
    total_xp: int = Field(default_factory=lambda: sum(
        q.xp_reward for q in LessonBase().questions))
    completed_count: int = 0
    avg_completion_time: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    published: bool = True

    class Config:
        from_attributes = True


class LessonPublic(LessonBase):
    id: str
    total_xp: int
    completed_count: int
    is_completed: Optional[bool] = None
    user_xp_earned: Optional[int] = None
    next_lesson_id: Optional[str] = None
    prev_lesson_id: Optional[str] = None
