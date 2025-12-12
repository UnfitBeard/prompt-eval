# api/dependencies.py
from typing import Generator
from fastapi import Depends

from services.user_service import UserService
from services.course_service import CourseService
from services.lesson_service import LessonService
from services.progress_service import ProgressService


def get_user_service() -> Generator:
    """Dependency for UserService"""
    service = UserService()
    try:
        yield service
    finally:
        pass


def get_course_service() -> Generator:
    """Dependency for CourseService"""
    service = CourseService()
    try:
        yield service
    finally:
        pass


def get_lesson_service() -> Generator:
    """Dependency for LessonService"""
    service = LessonService()
    try:
        yield service
    finally:
        pass


def get_progress_service() -> Generator:
    """Dependency for ProgressService"""
    service = ProgressService()
    try:
        yield service
    finally:
        pass
