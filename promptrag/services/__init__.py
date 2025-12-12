# services/__init__.py - Updated
import asyncio
from typing import Dict, Any


class ServiceFactory:
    """Factory for lazy-initialized services"""

    def __init__(self):
        self._services = {}
        self._initialized = False

    async def initialize(self):
        """Initialize all services"""
        if not self._initialized:
            from core.database import mongodb
            await mongodb.connect()
            self._initialized = True

    def get_service(self, service_class):
        """Get or create a service instance"""
        service_name = service_class.__name__

        if service_name not in self._services:
            # Create the service instance
            service = service_class()
            self._services[service_name] = service

        return self._services[service_name]


# Global service factory
service_factory = ServiceFactory()

# Lazy imports


def get_course_service():
    from .course_service import CourseService
    return service_factory.get_service(CourseService)


def get_lesson_service():
    from .lesson_service import LessonService
    return service_factory.get_service(LessonService)


def get_user_service():
    from .user_service import UserService
    return service_factory.get_service(UserService)


def get_progress_service():
    from .progress_service import ProgressService
    return service_factory.get_service(ProgressService)


__all__ = [
    "service_factory",
    "get_course_service",
    "get_lesson_service",
    "get_user_service",
    "get_progress_service"
]
