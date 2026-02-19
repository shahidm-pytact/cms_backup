"""API documentation for Authentication endpoints."""
from typing import ClassVar


class AuthApiDocs:
    """API documentation for Authentication endpoints."""
    
    token: ClassVar[dict] = {
        "summary": "OAuth2 token endpoint for Swagger UI authentication",
        "description": "OAuth2-compatible token endpoint that accepts form data (username/password) and returns access token. Used by Swagger UI for authentication.",
    }
    
    login: ClassVar[dict] = {
        "summary": "Authenticate user with email and password",
        "description": "Authenticates user with email and password, returns JWT access token along with user information and permissions. Login is allowed only when user status is 'active' and role status is 'active'.",
    }
    
    logout: ClassVar[dict] = {
        "summary": "Logout and invalidate user session/token",
        "description": "Logout endpoint that invalidates user session/token. Token invalidation may be handled via token blacklist or JWT ID (jti) revocation depending on implementation.",
    }
    
    validate_invitation: ClassVar[dict] = {
        "summary": "Validate invitation token and return invitation status",
        "description": "Validates invitation token and returns invitation status, expiry information, and validity. Returns 404 if token not found, 410 if expired, 409 if already accepted.",
    }
    
    accept_invitation: ClassVar[dict] = {
        "summary": "Accept invitation (validate token and mark invitation as accepted)",
        "description": "Accepts invitation by validating token and marking invitation as accepted. Updates invite_accepted_at timestamp but does NOT set password or change user status. User status remains 'invited' until password is set via set-password endpoint.",
    }
    
    set_password: ClassVar[dict] = {
        "summary": "Set initial password after accepting invitation",
        "description": "Sets initial password after accepting invitation. Requires invitation to be accepted first. Sets password hash, updates user status from 'invited' to 'active', and clears invitation fields. Password must meet strength requirements (min 8 chars, uppercase, lowercase, number, special character).",
    }
    
    request_password_reset: ClassVar[dict] = {
        "summary": "Request password reset (generates reset token and sends email)",
        "description": "Requests password reset by generating reset token and sending email. Always returns generic success message (does not disclose whether user exists) to prevent user enumeration attacks. Token expires after 24 hours.",
    }
    
    reset_password: ClassVar[dict] = {
        "summary": "Reset user password using reset token",
        "description": "Resets user password using reset token from email link. Validates reset token and expiry, sets new password hash, and clears reset token fields. Password must meet strength requirements.",
    }
    
    get_me: ClassVar[dict] = {
        "summary": "Retrieve current user's details, permissions, and context",
        "description": "Retrieves current user's complete context including user information, role details, and permissions in both nested structure and flat list format. Supports conditional GET with If-None-Match header for cache validation (returns 304 if unchanged).",
    }
