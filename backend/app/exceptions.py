"""Custom exception classes for consistent API error responses."""

from fastapi import HTTPException


class AppError(HTTPException):
    """Base application error producing consistent JSON responses.

    Response format: {"detail": {"code": "ERROR_CODE", "message": "Human-readable message"}}
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict | None = None,
    ):
        detail = {"code": code, "message": message}
        if details:
            detail["details"] = details
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(status_code=404, code="NOT_FOUND", message=message)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(status_code=403, code="FORBIDDEN", message=message)


class ValidationError(AppError):
    def __init__(self, message: str = "Validation error", code: str = "VALIDATION_ERROR"):
        super().__init__(status_code=422, code=code, message=message)


class RateLimitError(AppError):
    def __init__(
        self,
        message: str = "Rate limit exceeded. Please wait before sending more messages.",
    ):
        super().__init__(status_code=429, code="RATE_LIMIT_EXCEEDED", message=message)


class ConflictError(AppError):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(status_code=409, code="CONFLICT", message=message)
