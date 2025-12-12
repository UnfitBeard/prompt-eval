# models/response.py
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel
from datetime import datetime

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.now()

    @classmethod
    def success(cls, data: T = None, message: str = None) -> "APIResponse":
        return cls(
            success=True,
            message=message,
            data=data
        )

    @classmethod
    def error(cls, error: str, message: str = None) -> "APIResponse":
        return cls(
            success=False,
            message=message,
            error=error
        )


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
