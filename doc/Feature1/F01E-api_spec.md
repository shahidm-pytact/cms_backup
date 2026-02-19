# API Specification: F-001 — Core Platform Administration
## Part E: Audit Logs Module Endpoints

---

## 1. Overview

This document specifies the audit log endpoints for F-001 Core Platform Administration. These endpoints provide read-only access to the immutable audit trail of all administrative and security-sensitive actions.

**Scope:** Audit log listing and detail retrieval. Audit logs are immutable and append-only.

---

## 2. Global API Rules

### 2.1 Authentication

All endpoints require JWT Bearer token authentication (see Part A for JWT structure details).

### 2.2 Response Format

**Success Response (200):**
```json
{
  "data": { ... },
  "message": "Operation completed successfully"
}
```

**Error Response (400/401/403/404/etc.):**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "details": [{"field": "field_name", "issue": "Error description"}]
  },
  "message": "Human-friendly error message"
}
```

**Response Headers (REQUIRED):**
- `X-Request-ID`: Unique request identifier for debugging (e.g., `req_abc123xyz789`) - **MUST be present in ALL responses**

**Note:** 
- Field order shown is for readability only. JSON objects are unordered (RFC 7159).
- DO NOT include `success` field - HTTP status codes indicate success/failure.

### 2.3 UTC Timezone

All datetime fields MUST use UTC timezone (ISO 8601 format with `Z` suffix).

### 2.4 Path Parameters

All path parameters MUST use snake_case (e.g., `{audit_log_id}`, `{user_id}`).

### 2.5 Query Parameters

Query parameters MUST be defined using query schema classes with `Depends()` pattern (Rule 9), NOT individual `Query()` parameters in router endpoints.

---

## 3. Roles & Permissions

### 3.1 Audit Log Access Rules

**SuperAdmin:**
- Can read all audit logs across the entire platform
- Full system-wide audit visibility
- Can filter by any user, entity type, or action

**Operator:**
- **NO ACCESS** - Cannot access audit logs

**Operator:**
- **NO ACCESS** - Cannot access audit logs

**Note:** Only SuperAdmin is allowed to access audit logs. All other roles are denied access.

---

## 4. Audit Logs Module Endpoints

### 4.1 GET /v1/audit-logs

**Purpose:** List all audit logs across the platform with pagination, filtering, and sorting. Only SuperAdmin can access this endpoint.

**Authentication:** Required (JWT Bearer token)

**Authorization / Roles:** SuperAdmin only

**Headers:**
- `Authorization: Bearer <token>` (REQUIRED)
- `If-None-Match: "20240120T103000Z"` (optional, for cache validation - returns 304 if unchanged)
- **Response Headers (REQUIRED):**
  - `X-Request-ID`: Unique request identifier for debugging
  - `ETag`: Collection ETag (optional, based on latest audit log `created_at`)

**Query Schema Class (REQUIRED):**
```python
from uuid import UUID

class AuditLogListQuery(BaseModel):
    """Query schema for listing audit logs with pagination and filtering."""

    page: int = Field(1, ge=1, description="Page number (≥ 1)")
    page_size: int = Field(20, ge=1, le=100, description="Page size (1-100)")
    user_id: Optional[UUID] = Field(None, description="Filter by user ID (actor)")
    entity_type: Optional[str] = Field(None, description="Filter by entity type (e.g., 'user', 'user', 'role')")
    action: Optional[str] = Field(None, description="Filter by action (e.g., 'create', 'update', 'delete')")
    date_from: Optional[str] = Field(None, description="Filter from date (ISO 8601 format, UTC, e.g., '2024-01-01T00:00:00Z')")
    date_to: Optional[str] = Field(None, description="Filter to date (ISO 8601 format, UTC, e.g., '2024-01-31T23:59:59Z')")
    sort_by: str = Field("created_at", description="Sort field: created_at, user_id, entity_type, action")
    sort_order: str = Field("desc", description="Sort order: asc or desc")

    model_config = ConfigDict(from_attributes=True)
```

**Router Endpoint Pattern (REQUIRED):**
```python
@router.get("", response_model=StandardResponse[AuditLogPaginatedResponse])
async def list_audit_logs(
    query: AuditLogListQuery = Depends(AuditLogListQuery),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superadmin),
):
    """List audit logs with pagination, filtering, search, and sorting."""
    # Access via query.page, query.page_size, query.user_id, etc.
```

**Query Parameters Table (for documentation only):**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number (≥ 1) |
| page_size | integer | No | 20 | Page size (1-100) |
| user_id | string (UUID) | No | null | Filter by user ID (actor who performed the action) |
| user_id | string (UUID) | No | null | Filter by user ID (tenant scope) |
| entity_type | string | No | null | Filter by entity type (e.g., "user", "user", "role") |
| action | string | No | null | Filter by action (e.g., "create", "update", "delete", "invite", "activate") |
| date_from | string | No | null | Filter from date (ISO 8601 format, UTC, e.g., "2024-01-01T00:00:00Z") |
| date_to | string | No | null | Filter to date (ISO 8601 format, UTC, e.g., "2024-01-31T23:59:59Z") |
| sort_by | string | No | "created_at" | Sort field: "created_at", "user_id", "user_id", "entity_type", "action" |
| sort_order | string | No | "desc" | Sort order: "asc" or "desc" |

**Success Response (200 OK):**
```json
{
  "data": {
    "items": [
      {
        "id": "aa0e8400-e29b-41d4-a716-446655440000",
        "user_id": "440e8400-e29b-41d4-a716-446655440000",
        "action": "create",
        "entity_type": "user",
        "entity_id": "550e8400-e29b-41d4-a716-446655440000",
        "description": "User 'john@example.com' created",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "created_at": "2024-01-20T10:30:00Z"
      },
      {
        "id": "aa0e8400-e29b-41d4-a716-446655440001",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "action": "invite",
        "entity_type": "user",
        "entity_id": "660e8400-e29b-41d4-a716-446655440000",
        "description": "User 'newuser@example.com' invited",
        "ip_address": "192.168.1.101",
        "user_agent": "Mozilla/5.0...",
        "created_at": "2024-01-20T10:35:00Z"
      },
      {
        "id": "aa0e8400-e29b-41d4-a716-446655440002",
        "user_id": "440e8400-e29b-41d4-a716-446655440000",
        "action": "update",
        "entity_type": "role",
        "entity_id": "770e8400-e29b-41d4-a716-446655440000",
        "description": "Role 'Custom Manager' permissions updated",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "created_at": "2024-01-20T10:40:00Z"
      }
    ],
    "total": 1250,
    "page": 1,
    "page_size": 20,
    "total_pages": 63,
    "next_page": "/v1/audit-logs?page=2&page_size=20&sort_by=created_at&sort_order=desc&entity_type=user",
    "prev_page": null
  },
  "message": "Audit logs retrieved successfully"
}
```

**Response Headers:**
- `X-Request-ID: req_abc123xyz789`

**Conditional GET (304 Not Modified):**
If request includes `If-None-Match` header with matching ETag, return `304 Not Modified` (no response body).

**Error Responses:**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 304 Not Modified | - | Resource unchanged, ETag matches (conditional GET) |
| 401 Unauthorized | `UNAUTHENTICATED` | Missing or invalid authentication token |
| 403 Forbidden | `INSUFFICIENT_PERMISSIONS` | User is not SuperAdmin (only SuperAdmin can access audit logs) |
| 422 Unprocessable Entity | `VALIDATION_ERROR` | Invalid query parameter values (e.g., page < 1, page_size > 100, invalid date format) |

**Business Rules:**
- **Only SuperAdmin can access audit logs** - All other roles are denied access (403 Forbidden)
- SuperAdmin sees all audit logs across the entire platform
- `user_id` filter: Filter by the actor (user who performed the action)
- `user_id` filter: Filter by tenant scope (can be null for system-level actions)
- `entity_type` filter: Filter by affected entity type (e.g., "user", "user", "role")
- `action` filter: Filter by action performed (e.g., "create", "update", "delete", "invite", "activate", "deactivate")
- `date_from` and `date_to`: Filter by date range (ISO 8601 format, UTC)
  - `date_from`: Inclusive start date (defaults to beginning of time if not provided)
  - `date_to`: Inclusive end date (defaults to current time if not provided)
- Sort fields: "created_at", "user_id", "user_id", "entity_type", "action"
- Sort order: "asc" or "desc"
- Default sort: "created_at" descending (newest first)
- Audit logs are immutable and append-only (no updates or deletes)

**Example Error Response (403 - Insufficient Permissions):**
```json
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "details": [{"field": "role", "issue": "Only SuperAdmin can access audit logs."}]
  },
  "message": "Access denied. Only SuperAdmin can view audit logs."
}
```

---

### 4.2 GET /v1/audit-logs/{audit_log_id}

**Purpose:** Get detailed audit log information including old_values and new_values.

**Authentication:** Required (JWT Bearer token)

**Authorization / Roles:** SuperAdmin only

**Headers:**
- `Authorization: Bearer <token>` (REQUIRED)
- `If-None-Match: "20240120T103000Z"` (optional, for cache validation - returns 304 if unchanged)
- **Response Headers (REQUIRED):**
  - `X-Request-ID`: Unique request identifier for debugging
  - `ETag`: Resource version identifier based on `created_at` (audit logs are immutable, so ETag is based on creation time)

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| audit_log_id | string (UUID) | Yes | Audit log ID (RFC 4122 UUID format) |

**Success Response (200 OK):**
```json
{
  "data": {
    "id": "aa0e8400-e29b-41d4-a716-446655440000",
    "user_id": "440e8400-e29b-41d4-a716-446655440000",
    "action": "update",
    "entity_type": "user",
    "entity_id": "550e8400-e29b-41d4-a716-446655440000",
    "old_values": {
      "name": "John Doe",
      "status": "active",
      "role_id": "770e8400-e29b-41d4-a716-446655440000"
    },
    "new_values": {
      "name": "John Doe Updated",
      "status": "active",
      "role_id": "770e8400-e29b-41d4-a716-446655440001"
    },
    "description": "User 'user@example.com' updated: name changed from 'John Doe' to 'John Doe Updated', role_id changed from 2 to 3",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "created_at": "2024-01-20T10:30:00Z"
  },
  "message": "Audit log retrieved successfully"
}
```

**Response Headers:**
- `X-Request-ID: req_abc123xyz789`
- `ETag: "20240120T103000Z"` (based on `created_at` - audit logs are immutable)
- `Last-Modified: Wed, 20 Jan 2024 10:30:00 GMT`

**Conditional GET (304 Not Modified):**
If request includes `If-None-Match` header with matching ETag, return `304 Not Modified` (no response body).

**Error Responses:**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 304 Not Modified | - | Resource unchanged, ETag matches (conditional GET) |
| 401 Unauthorized | `UNAUTHENTICATED` | Missing or invalid authentication token |
| 403 Forbidden | `INSUFFICIENT_PERMISSIONS` | User is not SuperAdmin (only SuperAdmin can access audit logs) |
| 404 Not Found | `AUDIT_LOG_NOT_FOUND` | Audit log not found |

**Business Rules:**
- **Only SuperAdmin can access audit log details** - All other roles are denied access (403 Forbidden)
- Returns complete audit log information including:
  - `old_values`: JSON object containing the state before the action (can be null for create actions)
  - `new_values`: JSON object containing the state after the action (can be null for delete actions)
  - `description`: Human-readable summary of the action
  - `ip_address`: IP address of the actor
  - `user_agent`: Client information of the actor
- Audit logs are immutable (never updated or deleted)
- `user_id` can be null for system-generated actions
- `user_id` can be null for system-level actions (SuperAdmin actions)

**Example Response (Create Action):**
```json
{
  "data": {
    "id": "aa0e8400-e29b-41d4-a716-446655440003",
    "user_id": "440e8400-e29b-41d4-a716-446655440000",
    "action": "create",
    "entity_type": "user",
    "entity_id": "990e8400-e29b-41d4-a716-446655440000",
    "old_values": null,
    "new_values": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john@example.com",
      "name": "John Doe",
      "status": "active"
    },
    "description": "User 'john@example.com' created",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "created_at": "2024-01-20T10:30:00Z"
  },
  "message": "Audit log retrieved successfully"
}
```

**Example Response (Delete Action):**
```json
{
  "data": {
    "id": "aa0e8400-e29b-41d4-a716-446655440004",
    "user_id": "440e8400-e29b-41d4-a716-446655440000",
    "action": "delete",
    "entity_type": "user",
    "entity_id": "990e8400-e29b-41d4-a716-446655440000",
    "old_values": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "name": "John Doe",
      "status": "active"
    },
    "new_values": null,
    "description": "User 'john@example.com' deleted",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "created_at": "2024-01-20T11:00:00Z"
  },
  "message": "Audit log retrieved successfully"
}
```

---

## 5. Error Codes Summary

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Invalid request format or missing required fields |
| `UNAUTHENTICATED` | 401 | Missing or invalid authentication token |
| `INSUFFICIENT_PERMISSIONS` | 403 | User is not SuperAdmin (only SuperAdmin can access audit logs) |
| `AUDIT_LOG_NOT_FOUND` | 404 | Audit log not found |
| `VALIDATION_ERROR` | 422 | Invalid query parameter values (e.g., invalid date format) |

---

## 6. Assumptions

- Audit logs are immutable and append-only (never updated or deleted)
- Audit logs survive hard deletes of entities (preserved for compliance)
- All administrative actions generate audit log entries automatically
- `old_values` and `new_values` are JSON objects containing the state changes
- `user_id` can be null for system-generated actions
- `user_id` can be null for system-level actions (SuperAdmin actions)
- All datetime fields are stored and returned in UTC timezone
- Date range filters use inclusive boundaries (date_from ≤ created_at ≤ date_to)
- Audit log entries are indexed for efficient querying by (entity_type, entity_id), user_id, and created_at

---

## 7. Audit Log Fields Reference

### 7.1 Common Entity Types

- `user` - User entity
- `role` - Role entity
- `permission` - Permission entity (if applicable)

### 7.2 Common Actions

- `create` - Entity created
- `update` - Entity updated
- `delete` - Entity deleted
- `invite` - User invited
- `activate` - Entity activated (status changed to active)
- `deactivate` - Entity deactivated (status changed to inactive)
- `login` - User logged in
- `logout` - User logged out
- `password_reset` - Password reset requested
- `role_assigned` - Role assigned to user

---

**End of Part E: Audit Logs Module Endpoints**

