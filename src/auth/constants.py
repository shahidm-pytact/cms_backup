"""Authentication constants and messages."""

# Success Messages
SUCCESS_TOKEN_GENERATED = "Token generated successfully"
SUCCESS_LOGIN = "Login successful"
SUCCESS_LOGOUT = "Logout successful"
SUCCESS_INVITATION_VALID = "Invitation token is valid"
SUCCESS_INVITATION_ACCEPTED = "Invitation accepted successfully. Please set your password."
SUCCESS_PASSWORD_SET = "Password set successfully. You can now login."
SUCCESS_PASSWORD_RESET_REQUESTED = "If an account exists with this email, a password reset link has been sent."
SUCCESS_PASSWORD_RESET = "Password reset successfully. You can now login with your new password."
SUCCESS_USER_CONTEXT_RETRIEVED = "User context retrieved successfully"

# Error Messages
ERROR_INVALID_CREDENTIALS = "Invalid email or password"
ERROR_INACTIVE_USER = "User account is not active. Please contact your administrator."
ERROR_INACTIVE_ROLE = "User's role is not active. Please contact your administrator."
ERROR_INVALID_TOKEN = "Invalid or expired token"
ERROR_TOKEN_EXPIRED = "Token has expired"
ERROR_INVITATION_NOT_FOUND = "Invitation token not found"
ERROR_INVITATION_EXPIRED = "Invitation token has expired. Please request a new invitation."
ERROR_INVITATION_ALREADY_ACCEPTED = "Invitation has already been accepted"
ERROR_INVITATION_NOT_ACCEPTED = "Invitation has not been accepted yet. Please accept the invitation first."
ERROR_PASSWORD_ALREADY_SET = "Password has already been set for this user"
ERROR_RESET_TOKEN_NOT_FOUND = "Password reset token not found"
ERROR_RESET_TOKEN_EXPIRED = "Password reset token has expired. Please request a new password reset."
ERROR_PASSWORD_VALIDATION_FAILED = "Password validation failed"
ERROR_PASSWORDS_DO_NOT_MATCH = "Passwords do not match"

# Error Codes
ERROR_CODE_INVALID_CREDENTIALS = "UNAUTHENTICATED"
ERROR_CODE_INACTIVE_USER = "INACTIVE_USER"
ERROR_CODE_INACTIVE_ROLE = "INACTIVE_ROLE"
ERROR_CODE_INVALID_TOKEN = "INVALID_TOKEN"
ERROR_CODE_TOKEN_EXPIRED = "TOKEN_EXPIRED"
ERROR_CODE_INVITATION_NOT_FOUND = "INVITATION_NOT_FOUND"
ERROR_CODE_INVITATION_EXPIRED = "INVITATION_EXPIRED"
ERROR_CODE_INVITATION_ALREADY_ACCEPTED = "INVITATION_ALREADY_ACCEPTED"
ERROR_CODE_INVITATION_NOT_ACCEPTED = "INVITATION_NOT_ACCEPTED"
ERROR_CODE_PASSWORD_ALREADY_SET = "PASSWORD_ALREADY_SET"
ERROR_CODE_RESET_TOKEN_NOT_FOUND = "RESET_TOKEN_NOT_FOUND"
ERROR_CODE_RESET_TOKEN_EXPIRED = "RESET_TOKEN_EXPIRED"
ERROR_CODE_VALIDATION_ERROR = "VALIDATION_ERROR"
ERROR_CODE_INVALID_REQUEST = "INVALID_REQUEST"

# Status Values
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_INVITED = "invited"

# Token Types
TOKEN_TYPE_BEARER = "bearer"
