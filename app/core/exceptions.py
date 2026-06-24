"""
Custom application exceptions.
By extending HTTPException, FastAPI handles these automatically
with the correct HTTP status code — no extra exception handlers needed.
"""
from fastapi import HTTPException


class NotFoundError(HTTPException):
    """Raised when a requested resource does not exist."""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class ConflictError(HTTPException):
    """Raised when an operation conflicts with existing data."""
    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=409, detail=detail)


class ForbiddenError(HTTPException):
    """Raised when the current user lacks permission."""
    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(status_code=403, detail=detail)


class UnprocessableError(HTTPException):
    """Raised for business-logic validation failures (422)."""
    def __init__(self, detail: str = "Unprocessable request"):
        super().__init__(status_code=422, detail=detail)
