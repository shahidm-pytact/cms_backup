"""Roles API documentation for Swagger/OpenAPI."""
from typing import ClassVar


class RoleApiDocs:
    """API documentation for Role endpoints."""
    
    list: ClassVar[dict] = {
        "summary": "List all roles across the platform with pagination, filtering, and sorting",
        "description": (
            "Retrieves a paginated list of roles with support for filtering by status and role type, "
            "searching by name or slug, and sorting by various fields. "
            "All authenticated users (SuperAdmin and Operator) can read roles for reference. "
            "Supports conditional GET with If-None-Match header for cache validation."
        ),
    }
    
    create: ClassVar[dict] = {
        "summary": "Create a new custom role with permissions assignment",
        "description": (
            "Creates a new custom role with the specified slug, name, permissions, and status. "
            "Only SuperAdmin can create roles. "
            "Role slug must be unique (case-insensitive) and follow the format: lowercase alphanumeric and hyphens only. "
            "Permissions must match the required structure with 'modules' and 'system' objects. "
            "System roles are created via database migrations, not through this API."
        ),
    }
    
    get: ClassVar[dict] = {
        "summary": "Get specific role details with permissions",
        "description": (
            "Retrieves complete role information including permissions_json structure. "
            "All authenticated users (SuperAdmin and Operator) can read role details for reference. "
            "Supports conditional GET with If-None-Match header for cache validation."
        ),
    }
    
    update: ClassVar[dict] = {
        "summary": "Update role information (name, permissions_json, status)",
        "description": (
            "Updates role information with partial update support. Only SuperAdmin can update roles. "
            "Supports updating name, permissions_json, and status fields. "
            "System roles can only update status field (slug, name, and permissions_json are immutable for system roles). "
            "Custom roles can update all fields except slug (slug is immutable once created). "
            "Requires If-Match header with ETag from GET response for concurrency control. "
            "At least one field must be provided in the request body."
        ),
    }
