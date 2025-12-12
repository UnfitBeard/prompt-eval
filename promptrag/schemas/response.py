# schemas/response.py
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    error_message: Optional[str] = Field(None, alias="error")  # Use alias
    timestamp: datetime = datetime.now()

    class Config:
        # This allows you to use 'error' as field name in API but 'error_message' internally
        populate_by_name = True

    @classmethod
    def success(cls, data: T = None, message: str = None) -> "APIResponse":
        return cls(
            success=True,
            message=message,
            data=data,
            error_message=None  # Explicitly set to None
        )

    @classmethod
    def error(cls, error_msg: str, message: str = None) -> "APIResponse":
        return cls(
            success=False,
            message=message,
            data=None,
            error_message=error_msg  # Use the renamed field
        )


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = datetime.now()


class HealthResponse(BaseModel):
    status: str
    database: str
    chatbot: str
    version: str
