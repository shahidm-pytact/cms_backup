"""User module constants."""
# Error Messages
ERROR_USER_NOT_FOUND = "User not found"
ERROR_DUPLICATE_EMAIL = "A user with this email already exists"
ERROR_ROLE_NOT_FOUND = "Role not found"
ERROR_INACTIVE_ROLE = "Role is not active"
ERROR_INVALID_STATE_TRANSITION = "Invalid status transition"
ERROR_USER_NOT_ACTIVE = "User status is not active"
ERROR_USER_NOT_INVITED = "User status is not invited"
ERROR_INVITATION_NOT_FOUND = "User does not have an invitation"
ERROR_EMPTY_REQUEST_BODY = "At least one field must be provided for update"

# Success Messages
SUCCESS_USER_INVITED = "User invitation sent successfully"
SUCCESS_USER_RETRIEVED = "User retrieved successfully"
SUCCESS_USERS_RETRIEVED = "Users retrieved successfully"
SUCCESS_USER_UPDATED = "User updated successfully"
SUCCESS_USER_STATUS_UPDATED = "User status updated successfully"
SUCCESS_INVITATION_RESENT = "Invitation resent successfully"
SUCCESS_PASSWORD_RESET_EMAIL_SENT = "Password reset email sent successfully"
SUCCESS_INVITATION_STATUS_RETRIEVED = "Invitation status retrieved successfully"

# Error Codes
ERROR_CODE_USER_NOT_FOUND = "USER_NOT_FOUND"
ERROR_CODE_DUPLICATE_EMAIL = "DUPLICATE_EMAIL"
ERROR_CODE_ROLE_NOT_FOUND = "ROLE_NOT_FOUND"
ERROR_CODE_INACTIVE_ROLE = "INACTIVE_ROLE"
ERROR_CODE_INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
ERROR_CODE_USER_NOT_ACTIVE = "USER_NOT_ACTIVE"
ERROR_CODE_USER_NOT_INVITED = "USER_NOT_INVITED"
ERROR_CODE_INVITATION_NOT_FOUND = "INVITATION_NOT_FOUND"
ERROR_CODE_VALIDATION_ERROR = "VALIDATION_ERROR"

# Status Values
STATUS_INVITED = "invited"
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_EXPIRED = "expired"
STATUS_CANCELLED = "cancelled"

# Role Names (for permission checking)
ROLE_SUPERADMIN = "super-admin"
ROLE_OPERATOR = "operator"
