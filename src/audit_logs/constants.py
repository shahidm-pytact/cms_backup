"""Audit Log module constants."""
# Error Messages
ERROR_AUDIT_LOG_NOT_FOUND = "Audit log not found"
ERROR_INVALID_DATE_FORMAT = "Invalid date format. Use ISO 8601 format (e.g., '2024-01-01T00:00:00Z')"
ERROR_INVALID_SORT_FIELD = "Invalid sort field. Allowed values: created_at, user_id, entity_type, action"
ERROR_INVALID_SORT_ORDER = "Invalid sort order. Allowed values: asc, desc"

# Success Messages
SUCCESS_AUDIT_LOG_RETRIEVED = "Audit log retrieved successfully"
SUCCESS_AUDIT_LOGS_RETRIEVED = "Audit logs retrieved successfully"

# Error Codes
ERROR_CODE_AUDIT_LOG_NOT_FOUND = "AUDIT_LOG_NOT_FOUND"
ERROR_CODE_VALIDATION_ERROR = "VALIDATION_ERROR"
ERROR_CODE_INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
