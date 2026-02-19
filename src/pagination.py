"""Pagination schemas for paginated API responses."""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response schema for list endpoints.
    
    This schema provides a standard structure for paginated responses
    with items, pagination metadata, and navigation links.
    """
    
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    next_page: Optional[str] = None
    prev_page: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
