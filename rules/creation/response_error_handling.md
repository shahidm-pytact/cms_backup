# Standardized Response and Error Handling

**Purpose:** Implement standardized responses and error handling throughout the project.

## RULE 1: Response Format Structure

### 1.1 Success Response Format
**MANDATORY:** Success responses MUST follow this exact structure:
```json
{
  "data": { ... },
  "message": "Operation completed successfully"
}
```

**CRITICAL Rules:**
- Field order is CRITICAL: `data`, `message` (in that exact order)
- Success responses contain ONLY these two fields
- `data` contains the actual response payload
- `message` contains human-friendly success message

### 1.2 Error Response Format
**MANDATORY:** Error responses MUST follow this exact structure:
```json
{
  "error": {
    "code": "UPPER_SNAKE_CODE",
    "details": [{"field": "field_name", "issue": "What is wrong"}]
  },
  "message": "Human friendly error message"
}
```

**CRITICAL Rules:**
- Field order is CRITICAL: `error`, `message` (in that exact order)
- The `error` object MUST contain ONLY `code` and `details`
- The `error` object MUST NOT contain `message` field
- The `message` field is ONLY at root level, never inside `error` object
- `code` uses UPPER_SNAKE_CASE format
- `details` is an array of objects with `field` and `issue` properties

**WRONG Patterns:**
```json
// INCORRECT: message inside error object
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found"  // INCORRECT: message should be at root level
  }
}
// INCORRECT: Wrong field order
{
  "message": "Error occurred",
  "error": {...}
}
```

## RULE 2: Base Exception Types

### 2.1 Exception Class Hierarchy
**MANDATORY:** All domain exceptions MUST extend base exception classes from `src.exceptions`.

**Available Base Exception Types:**

| Exception | HTTP Status | Auto Code | Use Case |
|-----------|-------------|-----------|----------|
| `BadRequestError` | 400 | Custom | Bad input/invalid format |
| `UnauthenticatedError` | 401 | Custom | Missing/invalid token |
| `ForbiddenError` | 403 | Custom | Insufficient permissions |
| `NotFoundError` | 404 | `<DOMAIN>_NOT_FOUND` | Resource not found |
| `ConflictError` | 409 | Custom | Resource conflicts/duplicates |
| `ValidationError` | 422 | Custom | Domain rule violations |
| `InternalServerError` | 500 | Custom | Server errors |

**CRITICAL:** Use `UnauthenticatedError` (NOT `UnauthorizedError`) for 401 errors.

### 2.2 Exception Definition Pattern
**CORRECT Patterns:**
```python
from src.exceptions import NotFoundError, ConflictError, UnauthenticatedError

# Not Found (auto-generates RESOURCE_NOT_FOUND code)
class ResourceNotFound(NotFoundError):
    def __init__(self, resource_id: str):
        super().__init__(resource="Resource", resource_id=resource_id)

# Conflict (duplicate)
class UserEmailExists(ConflictError):
    def __init__(self, email: str):
        super().__init__(
            message=f"User with email {email} already exists",
            error_code="DUPLICATE_EMAIL",
            details=[{"field": "email", "issue": email}]
        )

# Unauthenticated (401) - CRITICAL: Use UnauthenticatedError, NOT UnauthorizedError
class InvalidCredentials(UnauthenticatedError):
    def __init__(self):
        super().__init__(
            message="Invalid email or password",
            error_code="INVALID_CREDENTIALS",
            details=[{"field": "email", "issue": "Invalid email or password"}]
        )
```

**WRONG Patterns:**
```python
# INCORRECT: Using HTTPException directly
class ResourceNotFound(HTTPException):  # INCORRECT: Must extend base exception
    ...

# INCORRECT: Using UnauthorizedError (doesn't exist)
from src.exceptions import UnauthorizedError  # INCORRECT: Use UnauthenticatedError
```

## RULE 3: Router Response Pattern

### 3.1 StandardResponse Wrapper
**MANDATORY:** All endpoints MUST use `StandardResponse[T]` wrapper and specify `response_model=StandardResponse[T]` in router decorator.

**CORRECT Patterns:**
```python
from src.schemas import StandardResponse
from src.module.schemas import ResourceResponse

# Single Item Response
@router.get("/{id}", response_model=StandardResponse[ResourceResponse])
async def get_resource(id: UUID, ...):
    resource = await service.get_resource(id)
    return StandardResponse(data=resource, message="Resource retrieved successfully")

# List Response
@router.get("", response_model=StandardResponse[List[ResourceResponse]])
async def list_resources(...):
    resources = await service.list_resources()
    return StandardResponse(data=resources, message="Resources retrieved successfully")

# Delete Response (No Data)
@router.delete("/{id}", response_model=StandardResponse[dict])
async def delete_resource(id: UUID, ...):
    await service.delete_resource(id)
    return StandardResponse(data={}, message="Resource deleted successfully")
```

**WRONG Patterns:**
```python
# INCORRECT: Missing StandardResponse wrapper
@router.get("/{id}", response_model=ResourceResponse)
async def get_resource(...):
    return resource  # INCORRECT: Must wrap in StandardResponse

# INCORRECT: Missing response_model
@router.get("/{id}")
async def get_resource(...):
    return StandardResponse(...)  # INCORRECT: Must specify response_model
```

## RULE 4: Service Layer Pattern

### 4.1 Exception Raising
**MANDATORY:** Services MUST raise exceptions (NOT return error responses).

**CORRECT Pattern:**
```python
async def get_resource(self, resource_id: UUID) -> Resource:
    resource = await self.repository.get_by_id(resource_id)
    if not resource:
        raise ResourceNotFound(str(resource_id))  # CORRECT: Raise exception
    return resource
```

**WRONG Pattern:**
```python
async def get_resource(self, resource_id: UUID):
    resource = await self.repository.get_by_id(resource_id)
    if not resource:
        return {"error": "Not found"}  # INCORRECT: Don't return error responses
    return resource
```

### 4.2 Service Exception Handling
**MANDATORY:** Services raise exceptions, routers let them propagate to global handlers.

**Key Principles:**
- Services raise exceptions when errors occur
- Services return domain models or response schemas on success
- Services do NOT catch exceptions (let them propagate)
- Services do NOT return error responses

## RULE 5: Router Layer Pattern

### 5.1 Exception Propagation
**MANDATORY:** Routers MUST NOT handle exceptions - let global handlers do it.

**CORRECT Pattern:**
```python
@router.get("/{id}", response_model=StandardResponse[ResourceResponse])
async def get_resource(id: UUID, ...):
    resource = await service.get_resource(id)  # Exception auto-handled by global handler
    return StandardResponse(data=resource, message="Resource retrieved successfully")
```

**WRONG Pattern:**
```python
@router.get("/{id}")
async def get_resource(id: UUID, ...):
    try:
        resource = await service.get_resource(id)
    except ResourceNotFound:
        return {"error": "Not found"}  # INCORRECT: Don't handle exceptions in routers
```

### 5.2 Router Exception Handling Rules
**MANDATORY:**
- Routers do NOT use try-catch blocks
- Routers let exceptions propagate to global handlers
- Routers only wrap successful responses in `StandardResponse`
- Routers do NOT return error responses directly

## RULE 6: Exception Handler Registration

### 6.1 Handler Registration Order
**CRITICAL:** Handlers registered in `src/main.py` - DO NOT modify order.

**MANDATORY Order:**
```python
# Order matters - most specific first
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
# ... database handlers ...
app.add_exception_handler(Exception, catch_all_exception_handler)  # Last
```

**CRITICAL Rules:**
- Most specific exceptions first
- Generic exceptions last
- `Exception` handler must be registered last (catch-all)
- DO NOT modify this order
- DO NOT add custom exception handlers in routers
- DO NOT register handlers in multiple places

## RULE 7: Success Message Standards

### 7.1 Message Format
**MANDATORY:** Use consistent success messages following this pattern:
- **Create:** `"{Resource} created successfully"`
- **Get:** `"{Resource} retrieved successfully"`
- **List:** `"{Resources} retrieved successfully"`
- **Update:** `"{Resource} updated successfully"`
- **Delete:** `"{Resource} deleted successfully"`

**Examples:**
```python
return StandardResponse(data=resource, message="User created successfully")
return StandardResponse(data=resource, message="User retrieved successfully")
return StandardResponse(data=resources, message="Users retrieved successfully")
return StandardResponse(data=resource, message="User updated successfully")
return StandardResponse(data={}, message="User deleted successfully")
```

## RULE 8: HTTP Status Codes

### 8.1 Status Code Reference
| Status | When to Use | Typical Error Code |
|--------|-------------|-------------------|
| 200 | Successful read/update | - |
| 201 | Resource created | - |
| 204 | Successful delete/no content | - |
| 400 | Bad input/invalid format | `INVALID_REQUEST` / `VALIDATION_FAILED` |
| 401 | Missing/invalid token | `UNAUTHENTICATED` |
| 403 | Valid token, insufficient rights | `INSUFFICIENT_PERMISSIONS` |
| 404 | Resource not found | `<DOMAIN>_NOT_FOUND` |
| 409 | Business conflict/duplicate | `DUPLICATE_<THING>` / `RESOURCE_IN_USE` |
| 422 | Domain rule violation | `BUSINESS_RULE_FAILED` / `VALIDATION_FAILED` |
| 500 | Server error | `INTERNAL_ERROR` |

### 8.2 Status Code Rules
**MANDATORY:**
- Use appropriate HTTP status codes for each operation
- 201 for POST (create) operations
- 200 for GET, PATCH, PUT, DELETE operations
- Status codes are automatically set by exception handlers
- DO NOT manually set status codes in routers (exception handlers do this)

## RULE 9: Error Codes

### 9.1 Error Code Patterns
| Code Pattern | HTTP | Description |
|--------------|------|-------------|
| `<DOMAIN>_NOT_FOUND` | 404 | Resource not found (auto-generated by `NotFoundError`) |
| `DUPLICATE_<FIELD>` | 409 | Duplicate value (field must be unique) |
| `VALIDATION_FAILED` | 400/422 | Input validation failed (see `details[]`) |
| `RESOURCE_IN_USE` | 409 | Cannot delete (FK/reference exists) |
| `INVALID_REQUEST` | 400 | Bad request (invalid input format) |
| `UNAUTHENTICATED` | 401 | Authentication required (missing/invalid token) |
| `INSUFFICIENT_PERMISSIONS` | 403 | Insufficient permissions (valid token but no access) |
| `BUSINESS_RULE_FAILED` | 422 | Business rule violation (domain-specific) |
| `INTERNAL_ERROR` | 500 | Internal server error (unexpected error) |

### 9.2 Error Code Rules
**MANDATORY:**
- Use UPPER_SNAKE_CASE format for error codes
- Use descriptive, specific error codes
- Follow naming patterns shown above
- `NotFoundError` automatically generates `<DOMAIN>_NOT_FOUND` code
- Custom error codes for other exception types

## RULE 10: Critical Rules Summary

### 10.1 Mandatory Rules
**ALWAYS:**
1. Use `StandardResponse[T]` wrapper for all responses
2. Specify `response_model=StandardResponse[T]` in router decorators
3. Extend base exception classes (NOT `HTTPException`)
4. Use `UnauthenticatedError` (NOT `UnauthorizedError`) for 401 errors
5. Raise exceptions in services (NOT return error responses)
6. Let exceptions propagate in routers (NO try-catch)
7. Maintain field order: `data`/`error`, `message`
8. Include `message` field ONLY at root level (never inside `error` object)
9. Use consistent success message formats
10. Follow HTTP status code conventions

**NEVER:**
1. Include `message` field inside `error` object
2. Handle exceptions in routers
3. Return error responses from services
4. Modify exception handler registration order
5. Use `HTTPException` directly (use base exceptions)
6. Use `UnauthorizedError` (use `UnauthenticatedError`)
7. Skip `response_model` in router decorators
8. Return raw data without `StandardResponse` wrapper
9. Use inconsistent success message formats
10. Manually set status codes in routers

## RULE 11: Common Mistakes
| Mistake | Correct Approach |
|---------|------------------|
| Returning raw data without `StandardResponse` | Wrap in `StandardResponse(data=..., message=...)` |
| Using `HTTPException` directly | Extend base exception (`NotFoundError`, `ConflictError`, etc.) |
| Using `UnauthorizedError` | Use `UnauthenticatedError` (correct class name) |
| Handling exceptions in routers | Let global handlers catch exceptions |
| Returning error responses from services | Raise exceptions instead |
| Missing `response_model` in decorator | Add `response_model=StandardResponse[T]` |
| Including `message` in `error` object | `message` only at root level, `error` has only `code` and `details` |
| Wrong field order | Success: `data`, `message` / Error: `error`, `message` |
| Try-catch blocks in routers | Remove try-catch, let exceptions propagate |
| Inconsistent success messages | Follow naming convention: `"{Resource} {action} successfully"` |

## RULE 12: Verification Checklist

### 12.1 Endpoint Verification
Before marking any endpoint as complete, verify:
- [ ] Response uses `StandardResponse[T]` wrapper
- [ ] `response_model=StandardResponse[T]` specified in decorator
- [ ] Success message follows naming convention
- [ ] Exceptions extend base exception classes (NOT `HTTPException`)
- [ ] Using `UnauthenticatedError` (NOT `UnauthorizedError`) for 401 errors
- [ ] No try-catch blocks in routers
- [ ] Services raise exceptions (not return errors)
- [ ] Field order correct: Success (`data`, `message`) / Error (`error`, `message`)
- [ ] `error` object contains ONLY `code` and `details` (NO `message`)
- [ ] `message` field is ONLY at root level (never inside `error` object)

### 12.2 Service Verification
Before marking any service method as complete, verify:
- [ ] Service raises exceptions when errors occur
- [ ] Service does NOT return error responses
- [ ] Service does NOT catch exceptions (lets them propagate)
- [ ] Service returns domain models or response schemas on success

### 12.3 Exception Verification
Before marking any exception as complete, verify:
- [ ] Exception extends base exception class (NOT `HTTPException`)
- [ ] Exception uses correct base class for HTTP status code
- [ ] Exception provides appropriate error code
- [ ] Exception provides appropriate error details
- [ ] Exception message is human-friendly

## RULE 13: Files Reference

### 13.1 Required Files
- **Response Schemas:** `src/schemas.py` - Contains: `StandardResponse`, `ErrorInfo`, `ErrorDetail`
- **Base Exceptions:** `src/exceptions.py` - Contains: `BadRequestError`, `UnauthenticatedError`, `ForbiddenError`, `NotFoundError`, `ConflictError`, `ValidationError`, `InternalServerError`
- **Exception Handlers:** `src/exceptions.py` - Contains: Handler functions for each exception type
- **Handler Registration:** `src/main.py` - Contains: Exception handler registration (DO NOT modify order)
- **Domain Exceptions:** `src/<module>/exceptions.py` - Domain-specific exceptions

### 13.2 File Structure Rules
**MANDATORY:**
- Response schemas defined in `src/schemas.py`
- Base exceptions defined in `src/exceptions.py`
- Exception handlers defined in `src/exceptions.py`
- Handler registration in `src/main.py`
- Domain exceptions in `src/<module>/exceptions.py`

## Summary

This guide provides rule-based instructions for implementing standardized responses and error handling.

**Key Principles:**
- All responses use `StandardResponse[T]` wrapper
- All exceptions extend base exception classes
- Services raise exceptions, routers let them propagate
- Global exception handlers format all error responses
- Consistent field order and message formats throughout

**Critical Reminders:**
- Use `UnauthenticatedError` (NOT `UnauthorizedError`) for 401 errors
- `message` field is ONLY at root level, never inside `error` object
- Field order is CRITICAL: `data`/`error`, `message`
- DO NOT handle exceptions in routers - let global handlers do it
