# API Specification: F-001 — Core Platform Administration
## Part A: Auth Module Endpoints

---

## 1. Overview

This document specifies the authentication and authorization endpoints for F-001 Core Platform Administration. These endpoints handle user login, logout, invitation acceptance, password reset, and user context retrieval.

**Scope:** Authentication flows, invitation management, password reset flows, and current user context.

---

## 2. Global API Rules

### 2.1 Authentication

**JWT Token Structure:**
All API endpoints (except public auth endpoints) require JWT Bearer token authentication.

**Token Format:** `Authorization: Bearer <jwt_token>`

**Required Claims in JWT Payload:**
- `sub` (subject): User ID (string, UUID format) - **REQUIRED**
- `role_id`: User role ID (string, UUID format) - **REQUIRED** - Encoded in token, not database lookup
- `exp`: Token expiration timestamp (integer, Unix timestamp) - **REQUIRED**
- `iat`: Token issued at timestamp (integer, Unix timestamp) - **RECOMMENDED**
- `jti`: JWT ID (string, unique token identifier) - **RECOMMENDED** for token revocation

**JWT Payload Example:**
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "role_id": "36d000fc-3d3e-42fc-b7fd-5d1e408eedb8",
  "exp": 1735689600,
  "iat": 1735686000,
  "jti": "jwt_abc123xyz789"
}
```

**Role Encoding:**
- Role ID MUST be encoded in JWT token (not database lookup during request)
- Role ID: UUID format (e.g., `"36d000fc-3d3e-42fc-b7fd-5d1e408eedb8"`)
- All roles have global access

**Token Expiration:**
- Access tokens expire after 15 minutes to 1 hour (specify in implementation)
- Expired token response: `401 UNAUTHENTICATED` with error code `TOKEN_EXPIRED`

**Token Validation:**
- Server MUST validate token signature, expiration, and required claims
- Missing or invalid token: Return `401 UNAUTHENTICATED`
- Missing required claims: Return `401 UNAUTHENTICATED` with error code `INVALID_TOKEN`

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
- `ETag`: Resource version identifier (for GET responses of resources that support updates, based on `updated_at`)
- `Last-Modified`: Timestamp of last modification (for GET responses, optional)

**Note:** 
- Field order shown is for readability only. JSON objects are unordered (RFC 7159). Do not require or emphasize field order.
- DO NOT include `success` field - HTTP status codes indicate success/failure.

### 2.3 UTC Timezone

All datetime fields MUST use UTC timezone (ISO 8601 format with `Z` suffix).
- Format: `YYYY-MM-DDTHH:mm:ssZ` (e.g., `2024-01-20T10:30:00Z`)
- All timestamps in request/response schemas MUST be in UTC.

---

## 3. Roles & Permissions

### 3.1 User Roles

**SuperAdmin:**
- System-wide authority
- Manages users, roles, permissions
- Full audit visibility

**Operator:**
- Execution-focused role
- No administrative authority
- Audit visibility limited to own actions

### 3.2 Permission Structure

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
    "super_admin": false,
  }
}
```

- `modules`: Nested object where each module (e.g., "user") contains actions as keys with boolean values
- `system`: System-level permissions object with keys like "super_admin" with boolean values

---

## 4. Auth Module Endpoints

### 4.1 POST /v1/auth/token

**Purpose:** OAuth2 token endpoint for Swagger UI authentication.

**Authentication:** Not required (public endpoint for Swagger UI)

**Authorization / Roles:** None

**Headers:**
- `Content-Type: application/x-www-form-urlencoded` (REQUIRED)
- **Response Headers (REQUIRED):**
  - `X-Request-ID`: Unique request identifier for debugging

**Request Body (Form Data):**
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| grant_type | string | Yes | OAuth2 grant type | Must be "password" |
| username | string | Yes | User email address | RFC 5322 format, max 254 chars |
| password | string | Yes | User password | Min 8 characters, max 128 characters |
| scope | string | No | OAuth2 scope | Optional, defaults to empty string |

**Success Response (200 OK):**
```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "scope": ""
  },
  "message": "Token generated successfully"
}
```

**Response Headers:**
- `X-Request-ID: req_abc123xyz789`

**Error Responses:**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 400 Bad Request | `INVALID_REQUEST` | Invalid grant_type or missing required fields |
| 401 Unauthorized | `UNAUTHENTICATED` | Invalid credentials (email or password incorrect) |
| 401 Unauthorized | `INACTIVE_USER` | User status is not "active" |
| 401 Unauthorized | `INACTIVE_ROLE` | User's role status is not "active" |
| 422 Unprocessable Entity | `VALIDATION_ERROR` | Email or password format validation failed |

**Example Error Response (401):**
```json
{
  "error": {
    "code": "UNAUTHENTICATED",
    "details": [{"field": "credentials", "issue": "Invalid email or password"}]
  },
  "message": "Authentication failed. Please check your credentials."
}
```

---

### 4.2 POST /v1/auth/login

**Purpose:** Authenticate user with email and password, return JWT access token.

**Authentication:** Not required (public endpoint)

**Authorization / Roles:** None

**Headers:**
- `Content-Type: application/json` (REQUIRED)
- **Response Headers (REQUIRED):**
  - `X-Request-ID`: Unique request identifier for debugging

**Request Body:**
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| email | string | Yes | User email address | RFC 5322 format, max 254 chars, case-insensitive |
| password | string | Yes | User password | Min 8 characters, max 128 characters |

**Request Body Example:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Success Response (200 OK):**
```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "name": "John Doe",
      "role_id": "770e8400-e29b-41d4-a716-446655440000",
      "status": "active"
    },
    "permissions": {
      "modules": {
        "user": {
          "read": true,
          "create": false,
          "update": true,
          "delete": false
        },
        "user": {
          "read": true,
          "invite": true,
          "update": true,
          "deactivate": true
        }
      },
      "system": {
        "super_admin": false,
      },
      "flat_list": [
        "user.read",
        "user.update",
        "user.read",
        "user.invite",
        "user.update",
        "user.deactivate"
      ]
    }
  },
  "message": "Login successful"
}
```

**Note:** The login response includes permissions to provide complete AuthContext as required by UI screens. This eliminates the need for an immediate `/auth/me` call after login.

**Response Headers:**
- `X-Request-ID: req_abc123xyz789`

**Error Responses:**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 400 Bad Request | `INVALID_REQUEST` | Missing required fields or invalid JSON |
| 401 Unauthorized | `UNAUTHENTICATED` | Invalid credentials (email or password incorrect) |
| 401 Unauthorized | `INACTIVE_USER` | User status is not "active" |
| 401 Unauthorized | `INACTIVE_ROLE` | User's role status is not "active" |
| 422 Unprocessable Entity | `VALIDATION_ERROR` | Email or password format validation failed |

**Login Enforcement Rules:**
Login is allowed only when:
- `users.status = active`
- `roles.status = active`

**SuperAdmin Login Response Example:**
```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "440e8400-e29b-41d4-a716-446655440000",
      "email": "admin@cmsplatform.com",
      "name": "System Administrator",
      "role_id": "330e8400-e29b-41d4-a716-446655440000",
      "status": "active"
    },
    "permissions": {
      "modules": {
        "user": {
          "read": true,
          "create": true,
          "update": true,
          "delete": true
        },
        "user": {
          "read": true,
          "invite": true,
          "update": true,
          "deactivate": true
        }
      },
      "system": {
        "super_admin": true,
      },
      "flat_list": [
        "user.read",
        "user.create",
        "user.update",
        "user.delete",
        "user.read",
        "user.invite",
        "user.update",
        "user.deactivate"
      ]
    }
  },
  "message": "Login successful"
}
```

**Example Error Response (401 - Inactive User):**
```json
{
  "error": {
    "code": "INACTIVE_USER",
    "details": [{"field": "user", "issue": "User account is not active. Please contact your administrator."}]
  },
  "message": "Login blocked: User account is inactive."
}
```

---

### 4.3 POST /v1/auth/logout

**Purpose:** Logout and invalidate user session/token.

**Authentication:** Required (JWT Bearer token)

**Authorization / Roles:** Any authenticated user

**Headers:**
- `Authorization: Bearer <token>` (REQUIRED)
- **Response Headers (REQUIRED):**
  - `X-Request-ID`: Unique request identifier for debugging

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "data": null,
  "message": "Logout successful"
}
```

**Response Headers:**
- `X-Request-ID: req_abc123xyz789`

**Error Responses:**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 401 Unauthorized | `UNAUTHENTICATED` | Missing or invalid authentication token |
| 401 Unauthorized | `TOKEN_EXPIRED` | JWT token has expired |

**Note:** Token invalidation may be handled via token blacklist or JWT ID (`jti`) revocation depending on implementation.

---

### 4.4 GET /v1/invitations/{token}/validate

**Purpose:** Validate invitation token and return invitation status, expiry information, and validity.

**Authentication:** Not required (public endpoint)

**Authorization / Roles:** None

**Headers:**
- **Response Headers (REQUIRED):**
  - `X-Request-ID`: Unique request identifier for debugging

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| token | string | Yes | Invitation token (from email link) |

**Success Response (200 OK):**
```json
{
  "data": {
    "valid": true,
    "user_id": "660e8400-e29b-41d4-a716-446655440000",
    "email": "newuser@example.com",
    "status": "invited",
    "invite_expires_at": "2024-01-25T10:30:00Z",
    "is_expired": false,
  },
  "message": "Invitation token is valid"
}
```

**Response Headers:**
- `X-Request-ID: req_abc123xyz789`

**Error Responses:**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 400 Bad Request | `INVALID_REQUEST` | Missing or invalid token format |
| 404 Not Found | `INVITATION_NOT_FOUND` | Invitation token not found in database |
| 410 Gone | `INVITATION_EXPIRED` | Invitation token has expired |
| 409 Conflict | `INVITATION_ALREADY_ACCEPTED` | Invitation has already been accepted (user status is not "invited") |

**Example Error Response (410 - Expired):**
```json
{
  "error": {
    "code": "INVITATION_EXPIRED",
    "details": [{"field": "token", "issue": "Invitation token has expired. Please request a new invitation."}]
  },
  "message": "Invitation token has expired."
}
```

---

### 4.5 POST /v1/auth/invitations/{token}/accept

**Purpose:** Accept invitation (validate token and mark invitation as accepted, but do not set password yet).

**Authentication:** Not required (public endpoint)

**Authorization / Roles:** None

**Headers:**
- `Content-Type: application/json` (REQUIRED)
- **Response Headers (REQUIRED):**
  - `X-Request-ID`: Unique request identifier for debugging

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| token | string | Yes | Invitation token (from email link) |

**Request Body:** None (token validation only)

**Success Response (200 OK):**
```json
{
  "data": {
    "user_id": "660e8400-e29b-41d4-a716-446655440000",
    "email": "newuser@example.com",
    "status": "invited",
    "invite_accepted_at": "2024-01-20T10:30:00Z",
    "can_set_password": true
  },
  "message": "Invitation accepted successfully. Please set your password."
}
```

**Response Headers:**
- `X-Request-ID: req_abc123xyz789`

**Error Responses:**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 400 Bad Request | `INVALID_REQUEST` | Missing or invalid token format |
| 404 Not Found | `INVITATION_NOT_FOUND` | Invitation token not found in database |
| 410 Gone | `INVITATION_EXPIRED` | Invitation token has expired |
| 409 Conflict | `INVITATION_ALREADY_ACCEPTED` | Invitation has already been accepted |

**Business Rules:**
- Validates invitation token and expiry
- Updates `invite_accepted_at` timestamp
- Does NOT set password (separate endpoint for password setup)
- Does NOT change user status (remains "invited" until password is set via `/v1/auth/invitations/{token}/set-password`)
- User status transitions from "invited" to "active" only after password is successfully set

---

### 4.6 POST /v1/auth/invitations/{token}/set-password

**Purpose:** Set initial password after accepting invitation.

**Authentication:** Not required (public endpoint, but requires valid invitation token)

**Authorization / Roles:** None

**Headers:**
- `Content-Type: application/json` (REQUIRED)
- **Response Headers (REQUIRED):**
  - `X-Request-ID`: Unique request identifier for debugging

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| token | string | Yes | Invitation token (from email link) |

**Request Body:**
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| password | string | Yes | New password | Min 8 characters, max 128 characters, must contain at least one uppercase letter, one lowercase letter, one number, and one special character |
| confirm_password | string | Yes | Password confirmation | Must match password field |

**Request Body Example:**
```json
{
  "password": "SecurePassword123!",
  "confirm_password": "SecurePassword123!"
}
```

**Success Response (200 OK):**
```json
{
  "data": {
    "user_id": "660e8400-e29b-41d4-a716-446655440000",
    "email": "newuser@example.com",
    "status": "active",
    "password_set_at": "2024-01-20T10:35:00Z"
  },
  "message": "Password set successfully. You can now login."
}
```

**Response Headers:**
- `X-Request-ID: req_abc123xyz789`

**Error Responses:**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 400 Bad Request | `INVALID_REQUEST` | Missing or invalid token format, missing required fields |
| 404 Not Found | `INVITATION_NOT_FOUND` | Invitation token not found in database |
| 410 Gone | `INVITATION_EXPIRED` | Invitation token has expired |
| 409 Conflict | `INVITATION_NOT_ACCEPTED` | Invitation has not been accepted yet (must call accept endpoint first) |
| 409 Conflict | `PASSWORD_ALREADY_SET` | Password has already been set for this user |
| 422 Unprocessable Entity | `VALIDATION_ERROR` | Password does not meet requirements or passwords do not match |

**Business Rules:**
- Requires invitation to be accepted first (via `/v1/auth/invitations/{token}/accept`)
- Sets password hash (never store plaintext)
- Updates user status from "invited" to "active" (status transition occurs here)
- Clears `invite_token` and `invite_expires_at` fields
- Sets `invite_accepted_at` if not already set
- After successful password set, user can login with email and password

**Example Error Response (422 - Password Validation):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "password", "issue": "Password must be at least 8 characters long"},
      {"field": "confirm_password", "issue": "Passwords do not match"}
    ]
  },
  "message": "Password validation failed."
}
```

---

### 4.7 POST /v1/auth/reset-password

**Purpose:** Request password reset (generates reset token and sends email).

**Authentication:** Not required (public endpoint)

**Authorization / Roles:** None

**Headers:**
- `Content-Type: application/json` (REQUIRED)
- **Response Headers (REQUIRED):**
  - `X-Request-ID`: Unique request identifier for debugging

**Request Body:**
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| email | string | Yes | User email address | RFC 5322 format, max 254 chars, case-insensitive |

**Request Body Example:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200 OK):**
```json
{
  "data": null,
  "message": "If an account exists with this email, a password reset link has been sent."
}
```

**Response Headers:**
- `X-Request-ID: req_abc123xyz789`

**Error Responses:**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 400 Bad Request | `INVALID_REQUEST` | Missing required fields or invalid JSON |
| 422 Unprocessable Entity | `VALIDATION_ERROR` | Email format validation failed |

**Business Rules:**
- **Always returns generic success message** (does not disclose whether user exists)
- If user exists and is active, generates `password_reset_token` and `password_reset_token_expires_at`
- Sends password reset email asynchronously (email failures logged only via audit logs, no retries)
- If user does not exist, still returns success (security best practice)
- Token expires after specified duration (e.g., 24 hours)

**Security Note:** This endpoint must not reveal whether an email exists in the system to prevent user enumeration attacks.

---

### 4.8 POST /v1/auth/reset-password/{token}

**Purpose:** Reset user password using reset token.

**Authentication:** Not required (public endpoint, but requires valid reset token)

**Authorization / Roles:** None

**Headers:**
- `Content-Type: application/json` (REQUIRED)
- **Response Headers (REQUIRED):**
  - `X-Request-ID`: Unique request identifier for debugging

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| token | string | Yes | Password reset token (from email link) |

**Request Body:**
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| password | string | Yes | New password | Min 8 characters, max 128 characters, must contain at least one uppercase letter, one lowercase letter, one number, and one special character |
| confirm_password | string | Yes | Password confirmation | Must match password field |

**Request Body Example:**
```json
{
  "password": "NewSecurePassword123!",
  "confirm_password": "NewSecurePassword123!"
}
```

**Success Response (200 OK):**
```json
{
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "password_reset_at": "2024-01-20T10:40:00Z"
  },
  "message": "Password reset successfully. You can now login with your new password."
}
```

**Response Headers:**
- `X-Request-ID: req_abc123xyz789`

**Error Responses:**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 400 Bad Request | `INVALID_REQUEST` | Missing or invalid token format, missing required fields |
| 404 Not Found | `RESET_TOKEN_NOT_FOUND` | Password reset token not found in database |
| 410 Gone | `RESET_TOKEN_EXPIRED` | Password reset token has expired |
| 422 Unprocessable Entity | `VALIDATION_ERROR` | Password does not meet requirements or passwords do not match |

**Business Rules:**
- Validates reset token and expiry
- Sets new password hash (never store plaintext)
- Clears `password_reset_token` and `password_reset_token_expires_at` fields
- Invalidates all existing sessions/tokens for security (optional, implementation-dependent)

**Example Error Response (410 - Expired):**
```json
{
  "error": {
    "code": "RESET_TOKEN_EXPIRED",
    "details": [{"field": "token", "issue": "Password reset token has expired. Please request a new password reset."}]
  },
  "message": "Password reset token has expired."
}
```

---

### 4.9 GET /v1/auth/me

**Purpose:** Retrieve current user's details, permissions, and context.

**Authentication:** Required (JWT Bearer token)

**Authorization / Roles:** Any authenticated user

**Note:** This endpoint uses GET method (RESTful for resource retrieval). The UI contract mentions POST, but GET is the standard HTTP method for retrieving resources per REST principles and API design rules.

**Headers:**
- `Authorization: Bearer <token>` (REQUIRED)
- `If-None-Match: "20240120T103000Z"` (optional, for cache validation - returns 304 if unchanged)
- **Response Headers (REQUIRED):**
  - `X-Request-ID`: Unique request identifier for debugging
  - `ETag`: Resource version identifier based on user's `updated_at` timestamp
  - `Last-Modified`: Timestamp of last modification from `updated_at` field (optional)

**Success Response (200 OK):**
```json
{
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "email": "operator@techcorp.com",
      "name": "John Smith",
      "role_id": "770e8400-e29b-41d4-a716-446655440000",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-20T08:30:00Z"
    },
    "role": {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "slug": "operator",
      "name": "Operator",
      "status": "active"
    },
    "permissions": {
      "modules": {
        "user": {
          "read": true,
          "create": false,
          "update": true,
          "delete": false
        },
        "user": {
          "read": true,
          "invite": true,
          "update": true,
          "deactivate": true
        }
      },
      "system": {
        "super_admin": false,
      },
      "flat_list": [
        "user.read",
        "user.update",
        "user.read",
        "user.invite",
        "user.update",
        "user.deactivate"
      ]
    }
  },
  "message": "User context retrieved successfully"
}
```

**Response Headers:**
- `X-Request-ID: req_abc123xyz789`
- `ETag: "20240120T083000Z"` (based on user's `updated_at`)
- `Last-Modified: Wed, 20 Jan 2024 08:30:00 GMT`

**Conditional GET (304 Not Modified):**
If request includes `If-None-Match` header with matching ETag, return `304 Not Modified` (no response body).

**Error Responses:**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 304 Not Modified | - | Resource unchanged, ETag matches (conditional GET) |
| 401 Unauthorized | `UNAUTHENTICATED` | Missing or invalid authentication token |
| 401 Unauthorized | `TOKEN_EXPIRED` | JWT token has expired |
| 401 Unauthorized | `INACTIVE_USER` | User status is not "active" |
| 401 Unauthorized | `INACTIVE_ROLE` | User's role status is not "active" |

**Business Rules:**
- Returns complete user context including user (if applicable) and role
- Includes permissions in both nested structure and flat list format
- For SuperAdmin users, `user` field is `null`
- Permissions are derived from `roles.permissions_json`
- `flat_list` contains all granted permissions in `module.action` format
- Response provides AuthContext with all required fields: `user_id` (from user.id), `user_id` (from user.user_id), `role_id` (from user.role_id), and `permissions` (full structure)

**SuperAdmin Example Response:**
```json
{
  "data": {
    "user": {
      "id": "440e8400-e29b-41d4-a716-446655440000",
      "email": "admin@cmsplatform.com",
      "name": "System Administrator",
      "role_id": "330e8400-e29b-41d4-a716-446655440000",
      "status": "active",
      "created_at": "2024-01-01T08:00:00Z",
      "updated_at": "2024-01-20T09:15:00Z"
    },
    "role": {
      "id": "330e8400-e29b-41d4-a716-446655440000",
      "slug": "super-admin",
      "name": "Super Administrator",
      "status": "active"
    },
    "permissions": {
      "modules": {
        "user": {
          "read": true,
          "create": true,
          "update": true,
          "delete": true
        },
        "user": {
          "read": true,
          "invite": true,
          "update": true,
          "deactivate": true
        }
      },
      "system": {
        "super_admin": true,
      },
      "flat_list": [
        "user.read",
        "user.create",
        "user.update",
        "user.delete",
        "user.read",
        "user.invite",
        "user.update",
        "user.deactivate"
      ]
    }
  },
  "message": "User context retrieved successfully"
}
```

---

## 5. Error Codes Summary

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Invalid request format or missing required fields |
| `UNAUTHENTICATED` | 401 | Missing or invalid authentication token |
| `TOKEN_EXPIRED` | 401 | JWT token has expired |
| `INVALID_TOKEN` | 401 | JWT token has invalid claims or signature |
| `INACTIVE_USER` | 401 | User account is not active |
| `INACTIVE_ROLE` | 401 | User's role is not active |
| `INVITATION_NOT_FOUND` | 404 | Invitation token not found |
| `INVITATION_EXPIRED` | 410 | Invitation token has expired |
| `INVITATION_ALREADY_ACCEPTED` | 409 | Invitation has already been accepted |
| `INVITATION_NOT_ACCEPTED` | 409 | Invitation has not been accepted yet |
| `PASSWORD_ALREADY_SET` | 409 | Password has already been set |
| `RESET_TOKEN_NOT_FOUND` | 404 | Password reset token not found |
| `RESET_TOKEN_EXPIRED` | 410 | Password reset token has expired |
| `VALIDATION_ERROR` | 422 | Field validation failed |

---

## 6. Assumptions

- Email delivery is asynchronous (failures logged only via audit logs, no retries)
- Password hashing uses secure algorithm (e.g., bcrypt, argon2)
- JWT tokens are stateless (no server-side session storage required)
- Token blacklist or JWT ID revocation may be implemented for logout (implementation-dependent)
- All datetime fields are stored and returned in UTC timezone
- Password reset tokens expire after 24 hours (configurable)
- Invitation tokens expire after 7 days (configurable)

---

**End of Part A: Auth Module Endpoints**

