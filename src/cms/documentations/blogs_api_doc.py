"""Blogs API documentation for Swagger/OpenAPI."""
from typing import ClassVar


class BlogApiDocs:
    """API documentation for Blog endpoints."""
    
    list: ClassVar[dict] = {
        "summary": "List all blogs with pagination, filtering, and sorting",
        "description": (
            "Retrieves a paginated list of blogs with their metadata (title, author, publishedDate, etc.). "
            "Returns only blog metadata, not the full content (sections and blocks) to keep payload size manageable. "
            "Supports filtering by author, searching in title/subtitle/description, and sorting by publishedDate, title, or author. "
            "Use this endpoint for listing pages, search results, and blog previews. "
            "Supports conditional GET with If-None-Match header for cache validation."
        ),
    }
    
    create: ClassVar[dict] = {
        "summary": "Create a new blog post",
        "description": (
            "Creates a new blog post with complete structure including metadata and sections. "
            "The slug must be unique and URL-friendly (lowercase alphanumeric, hyphens, underscores). "
            "Each section must have id, title, order_index, and blocks. "
            "Each block must have id, type, and order_index. "
            "Section IDs must be unique within the blog, and block IDs must be unique within their section. "
            "If status is not provided, it defaults to 'draft'. "
            "publishedDate is optional for draft blogs."
        ),
    }
    
    get: ClassVar[dict] = {
        "summary": "Get specific blog with full details",
        "description": (
            "Retrieves a complete blog post including all metadata, sections, and blocks. "
            "Use this endpoint when displaying the full blog post content. "
            "The slug is case-sensitive and must match exactly. "
            "Supports conditional GET with If-None-Match header for cache validation."
        ),
    }
    
    update: ClassVar[dict] = {
        "summary": "Update blog post (full update)",
        "description": (
            "Updates an existing blog post with full replacement (PUT). "
            "Include the complete blog structure in the request body. "
            "If slug is changed in the request body, the blog will be accessible via the new slug. "
            "When updating sections or blocks, ensure order_index values are provided and valid. "
            "All validation rules from create endpoint apply to updates."
        ),
    }
    
    delete: ClassVar[dict] = {
        "summary": "Delete blog post",
        "description": (
            "Deletes a blog post from the system using soft delete. "
            "The blog is marked as deleted (deleted_at timestamp is set) but not permanently removed from the database. "
            "Ensure proper authorization before allowing deletion. "
            "Related resources (images, assets) may need separate cleanup."
        ),
    }
