# API Specification: F-001 — Core Platform Administration
## Part D: Roles Module Endpoints

---

## 1. Overview

This document specifies the role management endpoints for F-001 Core Platform Administration. These endpoints handle role lifecycle management (create, read, update, activate/deactivate) and permission assignment to roles.

**Scope:** Role CRUD operations, permission assignment, and role status management.

---

## 2. Global API Rules

### 2.1 Authentication

All endpoints require JWT Bearer token authentication (see Part A for JWT structure details).

### 2.2 Response Format

**Success Response (200/201):**
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
- `ETag`: Resource version identifier (for GET responses, based on `updated_at`)
- `Last-Modified`: Timestamp of last modification (for GET responses, optional)

**Note:** 
- Field order shown is for readability only. JSON objects are unordered (RFC 7159).
- DO NOT include `success` field - HTTP status codes indicate success/failure.

### 2.3 UTC Timezone

All datetime fields MUST use UTC timezone (ISO 8601 format with `Z` suffix).

### 2.4 Path Parameters

All path parameters MUST use snake_case (e.g., `{role_id}`, `{user_id}`).

### 2.5 Query Parameters

Query parameters MUST be defined using query schema classes with `Depends()` pattern (Rule 9), NOT individual `Query()` parameters in router endpoints.

---

## 3. Roles & Permissions

### 3.1 Role Access Rules

**SuperAdmin:**
- Can create, read, update, delete all roles
- Can assign permissions to any role
- Full access to all role data


**Operator:**
- Can read roles (for reference)
- No write access to roles

### 3.2 Role Types

**System Roles:**
- Inbuilt roles (e.g., SuperAdmin, Operator)
- Immutable except for `status` field (can activate/deactivate)
- Cannot update `slug`, `name`, or `permissions_json`
- Protected from deletion

**Custom Roles:**
- User-created roles
- Can be updated and changed (all fields)
- Can be deleted (if no users are assigned)

### 3.3 Permission Structure

Permissions are stored in `roles.permissions_json` as a JSON object with the following structure:

```json
{
  "modules": {
    "user": {
      "read": true,
      "invite": true,
      "update": false
    }
  },
  "system": {
    "super_admin": false
  }
}
```

- `modules`: Nested object where each module (e.g., "user") contains actions as keys with boolean values
- `system`: System-level permissions object with keys like "super_admin" with boolean values

---

## 4. Roles Module Endpoints

### 4.1 GET /v1/roles

**Purpose:** List all roles across the platform with pagination, filtering, and sorting.

**Authentication:** Required (JWT Bearer token)

**Authorization / Roles:** SuperAdmin, Operator (all can read roles for reference)

**Headers:**
- `Authorization: Bearer <token>` (REQUIRED)
- `If-None-Match: "20240120T103000Z"` (optional, for cache validation - returns 304 if unchanged)
- **Response Headers (REQUIRED):**
  - `X-Request-ID`: Unique request identifier for debugging
  - `ETag`: Collection ETag (optional, based on latest role `updated_at`)

**Query Schema Class (REQUIRED):**
```python
class RoleListQuery(BaseModel):
    """Query schema for listing roles with pagination and filtering."""

    page: int = Field(1, ge=1, description="Page number (≥ 1)")
    page_size: int = Field(20, ge=1, le=100, description="Page size (1-100)")
    search: Optional[str] = Field(None, description="Search by role name or slug (case-insensitive partial match)")
    status: Optional[str] = Field(None, description="Filter by status: active, inactive")
    role_type: Optional[str] = Field(None, description="Filter by role type: system, custom")
    sort_by: str = Field("created_at", description="Sort field: created_at, updated_at, name, slug, status")
    sort_order: str = Field("desc", description="Sort order: asc or desc")

    model_config = ConfigDict(from_attributes=True)
```

**Router Endpoint Pattern (REQUIRED):**
```python
@router.get("", response_model=StandardResponse[RolePaginatedResponse])
async def list_roles(
    query: RoleListQuery = Depends(RoleListQuery),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List roles with pagination, filtering, search, and sorting."""
    # Access via query.page, query.page_size, query.search, etc.
```

**Query Parameters Table (for documentation only):**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number (≥ 1) |
| page_size | integer | No | 20 | Page size (1-100) |
| search | string | No | null | Search by role name or slug (case-insensitive partial match) |
| status | string | No | null | Filter by status: "active", "inactive" |
| role_type | string | No | null | Filter by role type: "system", "custom" |
| sort_by | string | No | "created_at" | Sort field: "created_at", "updated_at", "name", "slug", "status" |
| sort_order | string | No | "desc" | Sort order: "asc" or "desc" |

**Success Response (200 OK):**
```json
{
  "data": {
    "items": [
      {
        "id": "330e8400-e29b-41d4-a716-446655440000",
        "slug": "super-admin",
        "name": "Super Administrator",
        "status": "active",
        "role_type": "system",
        "created_at": "2024-01-01T08:00:00Z",
        "updated_at": "2024-01-20T08:30:00Z"
      },
      {
        "id": "770e8400-e29b-41d4-a716-446655440001",
        "slug": "custom-role-1",
        "name": "Custom Role 1",
        "status": "active",
        "role_type": "custom",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-18T14:20:00Z"
      }
    ],
    "total": 3,
    "page": 1,
    "page_size": 20,
    "total_pages": 1,
    "next_page": null,
    "prev_page": null
  },
  "message": "Roles retrieved successfully"
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
| 422 Unprocessable Entity | `VALIDATION_ERROR` | Invalid query parameter values (e.g., page < 1, page_size > 100) |

**Business Rules:**
- All authenticated users can read roles (for reference when assigning to users)
- Search matches role name or slug (case-insensitive partial match)
- Status filter accepts: "active", "inactive"
- Role type filter accepts: "system", "custom"
- Sort fields: "created_at", "updated_at", "name", "slug", "status"
- Sort order: "asc" or "desc"

---

### 4.2 POST /v1/roles

**Purpose:** Create a new custom role with permissions assignment.

**Authentication:** Required (JWT Bearer token)

**Authorization / Roles:** SuperAdmin only

**Headers:**
- `Authorization: Bearer <token>` (REQUIRED)
- `Content-Type: application/json` (REQUIRED)
- **Response Headers (REQUIRED):**
  - `X-Request-ID`: Unique request identifier for debugging

**Request Body:**
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| slug | string | Yes | Unique role identifier | Min 1 character, max 100 characters, lowercase alphanumeric and hyphens only, case-insensitive unique across all roles |
| name | string | Yes | Role display name | Min 1 character, max 255 characters |
| permissions_json | object | Yes | Assigned permissions | Must match permissions_json structure: { "modules": {...}, "system": {...} } |
| status | string | No | Role activation status | Enum: "active", "inactive" (default: "active") |

**Request Body Example:**
```json
{
  "slug": "custom-manager",
  "name": "Custom Manager Role",
  "permissions_json": {
    "modules": {
      "user": {
        "read": true,
        "invite": true,
        "update": false
      }
    },
    "system": {
      "super_admin": false
    }
  },
  "status": "active"
}
```

**Success Response (201 Created):**
```json
{
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "slug": "custom-manager",
    "name": "Custom Manager Role",
    "status": "active",
    "role_type": "custom",
    "permissions_json": {
      "modules": {
        "user": {
          "read": true,
          "invite": true,
          "update": false
        }
      },
      "system": {
        "super_admin": false,
      }
    },
    "created_at": "2024-01-20T10:30:00Z",
    "updated_at": "2024-01-20T10:30:00Z",
    "created_by": "440e8400-e29b-41d4-a716-446655440000",
    "updated_by": "440e8400-e29b-41d4-a716-446655440000"
  },
  "message": "Role created successfully"
}
```

**Response Headers:**
- `X-Request-ID: req_abc123xyz789`
- `ETag: "20240120T103000Z"` (based on `updated_at`)
- `Last-Modified: Wed, 20 Jan 2024 10:30:00 GMT`

**Error Responses:**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 400 Bad Request | `INVALID_REQUEST` | Missing required fields or invalid JSON |
| 401 Unauthorized | `UNAUTHENTICATED` | Missing or invalid authentication token |
| 403 Forbidden | `INSUFFICIENT_PERMISSIONS` | User is not SuperAdmin |
| 409 Conflict | `DUPLICATE_ROLE_SLUG` | Role slug already exists (case-insensitive) |
| 422 Unprocessable Entity | `VALIDATION_ERROR` | Field validation failed (slug format, name length, permissions_json structure) |
| 422 Unprocessable Entity | `INVALID_PERMISSIONS_STRUCTURE` | permissions_json does not match required structure |

**Business Rules:**
- Only SuperAdmin can create roles
- Role slug must be case-insensitive unique across all roles
- Role slug format: lowercase alphanumeric and hyphens only
- `permissions_json` must match the required structure:
  - Must have `modules` object (can be empty `{}`)
  - Must have `system` object with `super_admin` boolean field
  - Module actions are boolean values
- Default `role_type` is "custom" (system roles are created via database migrations)
- Default `status` is "active" if not provided
- Sets `created_by` and `updated_by` to current user ID
- All role creations are audited

**Example Error Response (422 - Invalid Permissions Structure):**
```json
{
  "error": {
    "code": "INVALID_PERMISSIONS_STRUCTURE",
    "details": [{"field": "permissions_json", "issue": "permissions_json must have 'modules' and 'system' objects. 'system' must contain 'super_admin' field."}]
  },
  "message": "Invalid permissions_json structure."
}
```

---

### 4.3 GET /v1/roles/{role_id}

**Purpose:** Get specific role details with permissions.

**Authentication:** Required (JWT Bearer token)

**Authorization / Roles:** SuperAdmin, Operator (all can read roles for reference)

**Headers:**
- `Authorization: Bearer <token>` (REQUIRED)
- `If-None-Match: "20240120T103000Z"` (optional, for cache validation - returns 304 if unchanged)
- **Response Headers (REQUIRED):**
  - `X-Request-ID`: Unique request identifier for debugging
  - `ETag`: Resource version identifier based on `updated_at`
  - `Last-Modified`: Timestamp of last modification from `updated_at` field (optional)

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| role_id | string (UUID) | Yes | Role ID (RFC 4122 UUID format) |

**Success Response (200 OK):**
```json
{
  "data": {
    "permissions_json": {
      "modules": {
        "user": {
          "read": true,
          "invite": true,
          "update": true,
          "deactivate": true
        }
      },
      "system": {
        "super_admin": false
      }
    },
    "created_at": "2024-01-01T08:00:00Z",
    "updated_at": "2024-01-20T08:30:00Z",
    "created_by": "440e8400-e29b-41d4-a716-446655440000",
    "updated_by": "440e8400-e29b-41d4-a716-446655440000"
  },
  "message": "Role retrieved successfully"
}
```

**Response Headers:**
- `X-Request-ID: req_abc123xyz789`
- `ETag: "20240120T083000Z"` (based on `updated_at`)
- `Last-Modified: Wed, 20 Jan 2024 08:30:00 GMT`

**Conditional GET (304 Not Modified):**
If request includes `If-None-Match` header with matching ETag, return `304 Not Modified` (no response body).

**Error Responses:**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 304 Not Modified | - | Resource unchanged, ETag matches (conditional GET) |
| 401 Unauthorized | `UNAUTHENTICATED` | Missing or invalid authentication token |
| 404 Not Found | `ROLE_NOT_FOUND` | Role not found |

**Business Rules:**
- All authenticated users can read role details (for reference)
- Returns complete role information including `permissions_json`
- Includes `role_type` to indicate if role is "system" or "custom"

---

### 4.4 PATCH /v1/roles/{role_id}

**Purpose:** Update role information (name, permissions_json, status). System roles can only update status.

**Authentication:** Required (JWT Bearer token)

**Authorization / Roles:** SuperAdmin only

**Headers:**
- `Authorization: Bearer <token>` (REQUIRED)
- `Content-Type: application/json` (REQUIRED)
- `If-Match: "20240120T103000Z"` (REQUIRED - ETag from GET response, based on `updated_at`, see Rule 8)
- **Response Headers (REQUIRED):**
  - `X-Request-ID`: Unique request identifier for debugging
  - `ETag`: New resource version identifier after update (based on new `updated_at`)

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| role_id | string (UUID) | Yes | Role ID (RFC 4122 UUID format) |

**Request Body:**
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| name | string | No | Role display name | Min 1 character, max 255 characters |
| permissions_json | object | No | Assigned permissions | Must match permissions_json structure: { "modules": {...}, "system": {...} } |
| status | string | No | Role activation status | Enum: "active", "inactive" (case-insensitive, lowercase values) |

**Request Body Example (Update name and permissions):**
```json
{
  "name": "Custom Manager Role Updated",
  "permissions_json": {
    "modules": {
      "user": {
        "read": true,
        "create": true,
        "update": true,
        "delete": false
      },
      "user": {
        "read": true,
        "invite": true,
        "update": true
      }
    },
    "system": {
      "super_admin": false,
    }
  }
}
```

**OR update status only (system or custom role):**
```json
{
  "status": "inactive"
}
```

**Success Response (200 OK):**
```json
{
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "slug": "custom-manager",
    "name": "Custom Manager Role Updated",
    "status": "active",
    "role_type": "custom",
    "permissions_json": {
      "modules": {
        "user": {
          "read": true,
          "invite": true,
          "update": true
        }
      },
      "system": {
        "super_admin": false
      }
    },
    "created_at": "2024-01-20T10:30:00Z",
    "updated_at": "2024-01-20T10:35:00Z",
    "created_by": "440e8400-e29b-41d4-a716-446655440000",
    "updated_by": "440e8400-e29b-41d4-a716-446655440000"
  },
  "message": "Role updated successfully"
}
```

**Response Headers:**
- `X-Request-ID: req_abc123xyz789`
- `ETag: "20240120T103500Z"` (New ETag after update, based on new `updated_at`)

**Error Responses:**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 400 Bad Request | `INVALID_REQUEST` | Missing required fields or invalid JSON, or empty request body (at least one field must be provided) |
| 401 Unauthorized | `UNAUTHENTICATED` | Missing or invalid authentication token |
| 403 Forbidden | `INSUFFICIENT_PERMISSIONS` | User is not SuperAdmin |
| 404 Not Found | `ROLE_NOT_FOUND` | Role not found |
| 412 Precondition Failed | `PRECONDITION_FAILED` | ETag mismatch (If-Match header doesn't match current resource version) |
| 422 Unprocessable Entity | `VALIDATION_ERROR` | Field validation failed |
| 422 Unprocessable Entity | `INVALID_PERMISSIONS_STRUCTURE` | permissions_json does not match required structure |
| 422 Unprocessable Entity | `INVALID_STATE_TRANSITION` | Invalid status transition (e.g., already in requested state) |
| 428 Precondition Required | `PRECONDITION_REQUIRED` | If-Match header missing (required for update operations) |

**Business Rules:**
- Only SuperAdmin can update roles
- Supports partial updates - only provided fields are updated
- **At least one field must be provided** - empty request body returns `400 Bad Request` with `VALIDATION_ERROR`
- **Both system and custom roles can update:**
  - `name` - Role display name
  - `permissions_json` - Assigned permissions (must match required structure)
  - `status` - Role activation status
- **Slug is immutable for all roles** - Cannot update `slug` (slug is immutable once created)
- `permissions_json` must match the required structure (if provided)
- Valid status values: "active", "inactive" (case-insensitive, but values must be lowercase)
- Status validation accepts "active" or "inactive" in any case but normalizes to lowercase
- When role status changes to "inactive", all users with this role are blocked from login (enforced at login time)
- Updates `updated_at` timestamp
- Sets `updated_by` to current user ID
- All changes are audited
- **ETag-based concurrency control:** If-Match header is REQUIRED

**Example Error Response (400 - Empty Request Body):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [{"field": "request_body", "issue": "At least one field must be provided for update"}]
  },
  "message": "Request body cannot be empty. Please provide at least one field to update."
}
```

**Example Error Response (422 - Invalid Status):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [{"field": "status", "issue": "Status must be 'active' or 'inactive'"}]
  },
  "message": "Invalid status value."
}
```

---

## 5. Error Codes Summary

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Invalid request format or missing required fields |
| `UNAUTHENTICATED` | 401 | Missing or invalid authentication token |
| `INSUFFICIENT_PERMISSIONS` | 403 | User lacks required permissions |
| `ROLE_NOT_FOUND` | 404 | Role not found |
| `DUPLICATE_ROLE_SLUG` | 409 | Role slug already exists (case-insensitive) |
| `PRECONDITION_FAILED` | 412 | ETag mismatch (If-Match header doesn't match current resource version) |
| `PRECONDITION_REQUIRED` | 428 | If-Match header missing (required for update operations) |
| `VALIDATION_ERROR` | 422 | Field validation failed |
| `INVALID_PERMISSIONS_STRUCTURE` | 422 | permissions_json does not match required structure |
| `INVALID_STATE_TRANSITION` | 422 | Invalid status transition |

---

## 6. Assumptions

- System roles are created via database migrations (not via API)
- Role slug is immutable once created (cannot be updated)
- System roles are protected from deletion (implementation-dependent, not in scope for F-001)
- Custom roles can be deleted if no users are assigned (implementation-dependent, not in scope for F-001)
- When role status changes to "inactive", all users with this role are blocked from login (enforced at login time)
- All datetime fields are stored and returned in UTC timezone
- ETag-based concurrency control prevents lost updates on role modifications
- Role slug uniqueness checks are case-insensitive
- `permissions_json` structure validation ensures data integrity

---

**End of Part D: Roles Module Endpoints**

