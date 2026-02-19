"""Blog CMS Pydantic schemas."""
from typing import Optional, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator


# Nested Schemas for Content Structure

class LinkSchema(BaseModel):
    """Link schema for text blocks."""
    
    text: str
    url: str
    external: bool = True
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BlockSchema(BaseModel):
    """Base block schema - all blocks share id, type, and order_index."""
    
    id: str = Field(..., description="Unique block identifier")
    type: str = Field(..., description="Block type (text, code, list, highlight, etc.)")
    order_index: int = Field(..., ge=1, description="Block ordering (gap-based: 10, 20, 30...)")
    
    # Type-specific fields (optional, validated in service)
    content: Optional[str] = None
    links: Optional[list[LinkSchema]] = None
    language: Optional[str] = None
    code: Optional[str] = None
    variant: Optional[str] = None
    items: Optional[list[Any]] = None
    src: Optional[str] = None
    alt: Optional[str] = None
    caption: Optional[str] = None
    columns: Optional[int] = None
    steps: Optional[list[str]] = None
    title: Optional[str] = None
    step_number: Optional[int] = Field(None, alias="stepNumber")
    options: Optional[dict[str, str]] = None
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SectionSchema(BaseModel):
    """Section schema with blocks."""
    
    id: str = Field(..., description="Unique section identifier")
    title: str = Field(..., description="Section title")
    order_index: int = Field(..., ge=1, description="Section ordering (gap-based: 1, 2, 3...)")
    badge: Optional[str] = Field(None, description="Optional badge text")
    badge_variant: Optional[str] = Field(None, alias="badgeVariant", description="Badge style variant")
    blocks: list[BlockSchema] = Field(..., description="Array of content blocks")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Request Schemas

class BlogCreate(BaseModel):
    """Request schema for creating a new blog."""
    
    slug: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique URL-friendly identifier"
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Blog title"
    )
    subtitle: Optional[str] = Field(None, description="Blog subtitle")
    description: Optional[str] = Field(None, description="Blog description")
    author: str = Field(..., min_length=1, max_length=255, description="Author name")
    author_img: Optional[str] = Field(None, alias="authorImg", description="Author image URL or base64 data URL")
    published_date: Optional[datetime] = Field(None, alias="publishedDate", description="Publication date (ISO 8601)")
    reading_time: Optional[str] = Field(None, alias="readingTime", max_length=50, description="Estimated reading time")
    hero_quote: Optional[str] = Field(None, alias="heroQuote", description="Hero quote text")
    blog_image: Optional[str] = Field(None, alias="blogImage", description="Blog image URL or base64 data URL")
    meta_description: Optional[str] = Field(None, alias="metaDescription", description="SEO meta description")
    keywords: Optional[list[str]] = Field(None, description="SEO keywords array")
    status: Optional[str] = Field("draft", description="Blog status: draft or published")
    sections: list[SectionSchema] = Field(..., description="Blog content sections")
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> str:
        """Validate and normalize status value."""
        if v is None:
            return "draft"
        v_lower = v.lower()
        if v_lower not in ("draft", "published"):
            raise ValueError("Status must be 'draft' or 'published'")
        return v_lower
    
    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format: URL-friendly (lowercase, hyphens)."""
        v_lower = v.lower().strip()
        if not v_lower:
            raise ValueError("Slug cannot be empty")
        # Allow lowercase alphanumeric, hyphens, and underscores
        if not all(c.isalnum() or c in ("-", "_") for c in v_lower):
            raise ValueError("Slug must contain only lowercase alphanumeric characters, hyphens, and underscores")
        return v_lower
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BlogUpdate(BaseModel):
    """Request schema for updating blog (partial update)."""
    
    slug: Optional[str] = Field(None, min_length=1, max_length=255, description="Unique URL-friendly identifier")
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Blog title")
    subtitle: Optional[str] = Field(None, description="Blog subtitle")
    description: Optional[str] = Field(None, description="Blog description")
    author: Optional[str] = Field(None, min_length=1, max_length=255, description="Author name")
    author_img: Optional[str] = Field(None, alias="authorImg", description="Author image URL or base64 data URL")
    published_date: Optional[datetime] = Field(None, alias="publishedDate", description="Publication date (ISO 8601)")
    reading_time: Optional[str] = Field(None, alias="readingTime", max_length=50, description="Estimated reading time")
    hero_quote: Optional[str] = Field(None, alias="heroQuote", description="Hero quote text")
    blog_image: Optional[str] = Field(None, alias="blogImage", description="Blog image URL or base64 data URL")
    meta_description: Optional[str] = Field(None, alias="metaDescription", description="SEO meta description")
    keywords: Optional[list[str]] = Field(None, description="SEO keywords array")
    status: Optional[str] = Field(None, description="Blog status: draft or published")
    sections: Optional[list[SectionSchema]] = Field(None, description="Blog content sections")
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize status value."""
        if v is None:
            return None
        v_lower = v.lower()
        if v_lower not in ("draft", "published"):
            raise ValueError("Status must be 'draft' or 'published'")
        return v_lower
    
    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """Validate slug format: URL-friendly (lowercase, hyphens)."""
        if v is None:
            return None
        v_lower = v.lower().strip()
        if not v_lower:
            raise ValueError("Slug cannot be empty")
        if not all(c.isalnum() or c in ("-", "_") for c in v_lower):
            raise ValueError("Slug must contain only lowercase alphanumeric characters, hyphens, and underscores")
        return v_lower
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BlogListQuery(BaseModel):
    """Query schema for listing blogs with pagination and filtering."""
    
    page: int = Field(1, ge=1, alias="page", description="Page number (≥ 1)")
    limit: int = Field(10, ge=1, le=100, alias="limit", description="Number of blogs per page (1-100)")
    sort: str = Field("publishedDate", description="Sort field: publishedDate, title, author, createdAt, updatedAt")
    order: str = Field("desc", description="Sort order: asc or desc")
    author: Optional[str] = Field(None, description="Filter by author name (case-insensitive partial match)")
    search: Optional[str] = Field(None, description="Search in title, subtitle, or description (case-insensitive)")
    
    @field_validator("order")
    @classmethod
    def validate_order(cls, v: str) -> str:
        """Validate sort order."""
        v_lower = v.lower()
        if v_lower not in ("asc", "desc"):
            raise ValueError("Order must be 'asc' or 'desc'")
        return v_lower
    
    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v: str) -> str:
        """Validate sort field."""
        allowed = ("publishedDate", "title", "author", "createdAt", "updatedAt")
        if v not in allowed:
            raise ValueError(f"Sort field must be one of: {', '.join(allowed)}")
        return v
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Response Schemas

class BlogListItem(BaseModel):
    """Response schema for blog in list (metadata only, no sections)."""
    
    id: UUID
    slug: str
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    author: str
    author_img: Optional[str] = Field(None, alias="authorImg")
    published_at: Optional[datetime] = Field(None, alias="publishedDate")
    reading_time: Optional[str] = Field(None, alias="readingTime")
    blog_image: Optional[str] = Field(None, alias="blogImage")
    meta_description: Optional[str] = Field(None, alias="metaDescription")
    keywords: Optional[list[str]] = None
    status: str
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BlogRead(BaseModel):
    """Response schema for blog details (with full content including sections)."""
    
    id: UUID
    slug: str
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    author: str
    author_img: Optional[str] = Field(None, alias="authorImg")
    published_at: Optional[datetime] = Field(None, validation_alias="published_at", serialization_alias="publishedDate")
    reading_time: Optional[str] = Field(None, alias="readingTime")
    hero_quote: Optional[str] = Field(None, alias="heroQuote")
    blog_image: Optional[str] = Field(None, alias="blogImage")
    meta_description: Optional[str] = Field(None, alias="metaDescription")
    keywords: Optional[list[str]] = None
    status: str
    content: list[SectionSchema] = Field(..., description="Blog content sections")
    created_at: datetime = Field(..., serialization_alias="createdAt")
    updated_at: Optional[datetime] = Field(None, serialization_alias="updatedAt")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BlogPaginationInfo(BaseModel):
    """Pagination metadata matching API spec format."""
    
    page: int
    limit: int
    total: int
    total_pages: int = Field(..., alias="totalPages")
    has_next: bool = Field(..., alias="hasNext")
    has_prev: bool = Field(..., alias="hasPrev")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BlogPaginatedResponse(BaseModel):
    """Paginated response for blog list matching API spec format."""
    
    blogs: list[BlogListItem]
    pagination: BlogPaginationInfo
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BlogCreateResponse(BaseModel):
    """Response schema for blog creation (minimal fields per API spec)."""
    
    id: UUID
    slug: str
    title: str
    status: str
    created_at: datetime = Field(..., serialization_alias="createdAt")
    updated_at: Optional[datetime] = Field(None, serialization_alias="updatedAt")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BlogUpdateResponse(BaseModel):
    """Response schema for blog update (minimal fields per API spec)."""
    
    id: UUID
    slug: str
    updated_at: datetime = Field(..., alias="updatedAt")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BlogDeleteResponse(BaseModel):
    """Response schema for blog deletion."""
    
    slug: str
    deleted_at: datetime = Field(..., alias="deletedAt")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
