"""Audit Logs API documentation for Swagger/OpenAPI."""
from typing import ClassVar


class AuditLogsApiDocs:
    """API documentation for Audit Logs endpoints."""
    
    list: ClassVar[dict] = {
        "summary": "Purpose of this API is to list all audit logs across the platform with pagination, filtering, and sorting",
        "description": (
            "Retrieves a paginated list of audit logs across the entire platform. "
            "Only SuperAdmin can access this endpoint. Supports filtering by user ID (actor), "
            "entity type, action, and date range. Supports sorting by created_at, user_id, "
            "entity_type, or action. Default sort is created_at descending (newest first). "
            "Audit logs are immutable and append-only (never updated or deleted)."
        ),
    }
    
    get: ClassVar[dict] = {
        "summary": "Purpose of this API is to get detailed audit log information including old_values and new_values",
        "description": (
            "Retrieves detailed audit log information including old_values and new_values. "
            "Only SuperAdmin can access audit log details. Returns complete audit log information "
            "including state changes (old_values and new_values), description, IP address, and user agent. "
            "Audit logs are immutable (never updated or deleted). user_id can be null for system-generated "
            "actions or system-level actions (SuperAdmin actions)."
        ),
    }
