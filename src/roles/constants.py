"""Role module constants."""
# Error Messages
ERROR_ROLE_NOT_FOUND = "Role not found"
ERROR_DUPLICATE_ROLE_SLUG = "A role with this slug already exists"
ERROR_INVALID_PERMISSIONS_STRUCTURE = "permissions_json must have 'modules' and 'system' objects. 'system' must contain 'super_admin' field."
ERROR_INVALID_STATE_TRANSITION = "Invalid status transition"
ERROR_EMPTY_REQUEST_BODY = "Request body cannot be empty. Please provide at least one field to update."

# Success Messages
SUCCESS_ROLE_CREATED = "Role created successfully"
SUCCESS_ROLE_RETRIEVED = "Role retrieved successfully"
SUCCESS_ROLES_RETRIEVED = "Roles retrieved successfully"
SUCCESS_ROLE_UPDATED = "Role updated successfully"

# Error Codes
ERROR_CODE_ROLE_NOT_FOUND = "ROLE_NOT_FOUND"
ERROR_CODE_DUPLICATE_ROLE_SLUG = "DUPLICATE_ROLE_SLUG"
ERROR_CODE_INVALID_PERMISSIONS_STRUCTURE = "INVALID_PERMISSIONS_STRUCTURE"
ERROR_CODE_INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
ERROR_CODE_VALIDATION_ERROR = "VALIDATION_ERROR"

# Status Values
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"

# Role Type Values
ROLE_TYPE_SYSTEM = "system"
ROLE_TYPE_CUSTOM = "custom"

# Sort Fields
SORT_FIELD_CREATED_AT = "created_at"
SORT_FIELD_UPDATED_AT = "updated_at"
SORT_FIELD_NAME = "name"
SORT_FIELD_SLUG = "slug"
SORT_FIELD_STATUS = "status"

# Sort Orders
SORT_ORDER_ASC = "asc"
SORT_ORDER_DESC = "desc"
