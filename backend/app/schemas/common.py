from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard response envelope used by all endpoints."""

    success: bool
    data: T | None = None
    error: dict[str, Any] | None = None

    @classmethod
    def ok(cls, data: T) -> "APIResponse[T]":
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, code: str, message: str) -> "APIResponse[None]":
        return cls(success=False, error={"code": code, "message": message})


class PaginatedResponse(BaseModel, Generic[T]):
    """Cursor-based paginated response."""

    success: bool = True
    data: list[T]
    next_cursor: str | None = None
    has_more: bool = False
