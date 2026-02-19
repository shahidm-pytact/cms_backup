"""User API documentation for Swagger/OpenAPI."""
from typing import ClassVar


class UserApiDocs:
    """API documentation for User endpoints."""
    
    list: ClassVar[dict] = {
        "summary": "List all users with pagination, search, filtering, and sorting",
        "description": "Retrieves a paginated list of users. SuperAdmin can see all users. Operator can only see their own user record. Supports search by email or name, filtering by status and role, and sorting by various fields."
    }
    
    invite: ClassVar[dict] = {
        "summary": "Invite a new user with role assignment",
        "description": "Creates a new user with status 'invited', generates an invitation token, sets invitation expiration (7 days), and sends an invitation email. Only SuperAdmin can invite users."
    }
    
    get: ClassVar[dict] = {
        "summary": "Get user details with invitation status and role information",
        "description": "Retrieves detailed user information including role details and invitation status (if user is invited). SuperAdmin can access any user. Operator can only access their own user record."
    }
    
    get_invitation_status: ClassVar[dict] = {
        "summary": "Get user invitation status including status, expiry date, and re-invite eligibility",
        "description": "Retrieves invitation status details for a user including invited_at, invite_expires_at, invite_accepted_at, is_expired, and can_resend flags. Only available for users with status 'invited'. Only SuperAdmin can access invitation status."
    }
    
    update: ClassVar[dict] = {
        "summary": "Update user information (name, email, role_id, status)",
        "description": "Updates user information with partial updates. Only provided fields are updated. Requires If-Match header for concurrency control. Supports updating name, email, role_id, and status. Only SuperAdmin can update users."
    }
    
    resend_invite: ClassVar[dict] = {
        "summary": "Resend invitation to user with new token",
        "description": "Resets invitation token and expiration, sends a new invitation email. Updates invited_at timestamp and invited_by field. User's role must be active. Only SuperAdmin can resend invitations."
    }
    
    request_password_reset: ClassVar[dict] = {
        "summary": "Request password reset for a user (generates reset token and sends email)",
        "description": "Admin-initiated password reset. Generates a password reset token with 24-hour expiration and sends a password reset email. User must be active and user's role must be active. Only SuperAdmin can request password resets."
    }
    
    update_status: ClassVar[dict] = {
        "summary": "Update user status (activate or deactivate)",
        "description": "Updates user status to 'active' or 'inactive'. Requires If-Match header for concurrency control. Can only activate users with status 'invited' (after password is set). Can deactivate users with status 'active' or 'invited'. User's role must be active to activate. Only SuperAdmin can update user status."
    }