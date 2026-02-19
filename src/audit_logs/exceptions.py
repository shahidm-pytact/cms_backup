"""Audit Log module exceptions."""
from src.exceptions import NotFoundError
from src.audit_logs.constants import (
    ERROR_AUDIT_LOG_NOT_FOUND,
    ERROR_CODE_AUDIT_LOG_NOT_FOUND,
)


class AuditLogNotFound(NotFoundError):
    """Raised when audit log is not found."""
    
    def __init__(self, audit_log_id: str):
        super().__init__(
            resource="AuditLog",
            resource_id=audit_log_id,
        )
