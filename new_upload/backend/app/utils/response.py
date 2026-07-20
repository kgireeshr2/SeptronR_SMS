from typing import Any, Optional
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class APIResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str = "Success"
    pagination: Optional[PaginationMeta] = None


def ok(
    data: Any = None,
    message: str = "Success",
    pagination: Optional[PaginationMeta] = None,
) -> dict:
    """Return a success response envelope.
    
    Pre-serializes data with jsonable_encoder so SQLAlchemy models,
    UUIDs, dates, etc. are all converted to JSON-safe types before
    the dict is returned to FastAPI.
    """
    serialized = jsonable_encoder(data)
    return APIResponse(
        success=True, data=serialized, message=message, pagination=pagination
    ).model_dump()


def error(message: str = "An error occurred", data: Any = None) -> dict:
    """Return an error response envelope."""
    return APIResponse(success=False, data=jsonable_encoder(data), message=message).model_dump()
