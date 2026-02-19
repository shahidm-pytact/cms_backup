# Database Constraint Handling

**Purpose:** Convert database constraint violations to user-friendly errors with proper HTTP status codes and field-level details.

## RULE 1: Error Mappings
### 1.1 Constraint Type to HTTP Status Mapping
**MANDATORY:** Each constraint type MUST map to appropriate HTTP status code and error format.

| Constraint Type | HTTP Status | Error Code Pattern | Message Pattern |
|----------------|-------------|-------------------|-----------------|
| Unique | `409 Conflict` | `DUPLICATE_{FIELD}` | `"A record with this {field} already exists. Please use a different value."` |
| Foreign Key | `404 Not Found` | `{RESOURCE}_NOT_FOUND` | `"The referenced {resource} does not exist."` |
| Not Null | `422 Unprocessable Entity` | `REQUIRED_FIELD_MISSING` | `"The field '{field}' is required and cannot be null."` |
| Check | `422 Unprocessable Entity` | `CHECK_CONSTRAINT_VIOLATION` | `"The value provided for '{field}' violates a validation rule."` |

**RULE 1.1.1: HTTP Status Code Rules**
- CORRECT Unique violations → 409 Conflict
- CORRECT Foreign key violations → 404 Not Found
- CORRECT Not null violations → 422 Unprocessable Entity
- CORRECT Check violations → 422 Unprocessable Entity

**RULE 1.1.2: Error Code Format Rules**
- CORRECT Use UPPER_SNAKE_CASE for error codes
- CORRECT Include field name in error code when applicable
- CORRECT Use descriptive error codes (e.g., `DUPLICATE_EMAIL`, `USER_NOT_FOUND`)

---

## RULE 2: Implementation Steps
### 2.1 Step 1: Add Imports
**RULE 2.1.1: Required Imports in `src/exceptions.py`**
```python
import re
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import (
    UniqueViolationError,
    ForeignKeyViolationError,
    NotNullViolationError,
    CheckViolationError,
)
from src.schemas import StandardResponse, ErrorInfo
```

**RULE 2.1.2: Import Rules**
- CORRECT Import all required database exception types
- CORRECT Import `StandardResponse` and `ErrorInfo` for response formatting
- CORRECT Import `re` for regex pattern matching
- CORRECT Import `JSONResponse` for error responses

### 2.2 Step 2: Create Handler Function
**RULE 2.2.1: Handler Function Location**
- CORRECT Create `database_exception_handler` function in `src/exceptions.py`
- CORRECT Function signature: `async def database_exception_handler(request: Request, exc: Exception) -> JSONResponse`

**RULE 2.2.2: Handler Function Structure**
```python
async def database_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for database constraint violations"""
    
    def extract_field_name(error_msg: str, constraint_name: str = None) -> str:
        """Extract field name from constraint name or error message"""
        # Implementation details below
    
    def extract_constraint_info(error_msg: str) -> tuple[str, str]:
        """Extract constraint name and field from error message"""
        # Implementation details below
    
    def create_error_response(
        status_code: int,
        error_code: str,
        message: str,
        details: list[dict]
    ) -> JSONResponse:
        """Helper to create standardized error response"""
        # Implementation details below
    
    # Handle IntegrityError (wraps asyncpg exceptions)
    if isinstance(exc, IntegrityError):
        # Handle wrapped exceptions
        ...
    
    # Handle direct asyncpg exceptions (fallback)
    if isinstance(exc, UniqueViolationError):
        # Handle direct exceptions
        ...
```

**RULE 2.2.3: Handler Function Rules**
- CORRECT Handle both `IntegrityError` (wrapped) and direct asyncpg exceptions
- CORRECT Extract field names from constraint names
- CORRECT Use `StandardResponse` format for all error responses
- CORRECT Include field-level error details

## RULE 3: Field Name Extraction
### 3.1 Constraint Name Patterns
**RULE 3.1.1: Common Constraint Name Patterns**

| Constraint Name | Extracted Field |
|----------------|----------------|
| `ix_users_email` | `email` |
| `users_email_key` | `email` |
| `uq_customers_pan_card_num` | `pan_card_num` |
| `fk_customers_user_id` | `user_id` |
| `ck_users_age_positive` | `age` |

**RULE 3.1.2: Extraction Algorithm**

**MANDATORY Steps:**
1. Remove prefixes: `ix_`, `fk_`, `pk_`, `uq_`, `ck_`
2. Remove table prefix: Split by first `_`, take second part
3. Remove suffixes: `_key`, `_idx`, `_constraint`
4. Fallback: Extract from error message regex patterns

**RULE 3.1.3: Extract Field Name Function**
```python
def extract_field_name(error_msg: str, constraint_name: str = None) -> str:
    """Extract field name from constraint name or error message"""
    if constraint_name:
        field = constraint_name
        # Remove prefixes: ix_, fk_, pk_, uq_, ck_
        for prefix in ['ix_', 'fk_', 'pk_', 'uq_', 'ck_']:
            if field.startswith(prefix):
                field = field[len(prefix):]
        # Remove table prefix (e.g., "users_" from "users_email")
        if '_' in field:
            parts = field.split('_', 1)
            if len(parts) > 1:
                field = parts[1]
        # Remove suffixes: _key, _idx, _constraint
        for suffix in ['_key', '_idx', '_constraint']:
            if field.endswith(suffix):
                field = field[:-len(suffix)]
        return field
    
    # Extract from error message: "Key (field_name)=(value)"
    match = re.search(r'Key \(([^)]+)\)', error_msg)
    if match:
        return match.group(1)
    
    # Extract constraint name and recurse
    match = re.search(r'constraint "([^"]+)"', error_msg)
    if match:
        return extract_field_name(error_msg, match.group(1))
    
    return "field"
```

**RULE 3.1.4: Extract Constraint Info Function**
```python
def extract_constraint_info(error_msg: str) -> tuple[str, str]:
    """Extract constraint name and field from error message"""
    constraint_name = None
    match = re.search(r'constraint "([^"]+)"', error_msg)
    if match:
        constraint_name = match.group(1)
    field_name = extract_field_name(error_msg, constraint_name)
    return constraint_name, field_name
```

## RULE 4: Error Response Creation
### 4.1 Create Error Response Helper
**RULE 4.1.1: Helper Function**
```python
def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: list[dict]
) -> JSONResponse:
    """Helper to create standardized error response"""
    error_info = ErrorInfo(code=error_code, details=details)
    response = StandardResponse(error=error_info, message=message)
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(exclude_none=True),
    )
```

**RULE 4.1.2: Response Format Rules**
- CORRECT Use `StandardResponse` format
- CORRECT Include `ErrorInfo` with code and details
- CORRECT Set appropriate HTTP status code
- CORRECT Include field-level error details

## RULE 5: Unique Constraint Handling
### 5.1 Unique Violation Error
**RULE 5.1.1: Handler Pattern**
```python
if isinstance(orig_exc, UniqueViolationError):
    _, field_name = extract_constraint_info(str(orig_exc))
    return create_error_response(
        status_code=status.HTTP_409_CONFLICT,
        error_code=f"DUPLICATE_{field_name.upper()}",
        message=f"A record with this {field_name} already exists. Please use a different value.",
        details=[{"field": field_name, "issue": f"{field_name} must be unique"}],
    )
```

**RULE 5.1.2: Unique Constraint Rules**
- CORRECT HTTP Status: 409 Conflict
- CORRECT Error Code: `DUPLICATE_{FIELD}` (e.g., `DUPLICATE_EMAIL`)
- CORRECT Message: User-friendly message explaining duplicate value
- CORRECT Details: Field name and issue description

## RULE 6: Foreign Key Constraint Handling
### 6.1 Foreign Key Violation Error
**RULE 6.1.1: Handler Pattern**
```python
elif isinstance(orig_exc, ForeignKeyViolationError):
    error_msg = str(orig_exc)
    match = re.search(r'Key \(([^)]+)\)=\(([^)]+)\) is not present in table "([^"]+)"', error_msg)
    if match:
        field_name, key_value, table_name = match.group(1), match.group(2), match.group(3)
        resource_name = table_name.replace('_', ' ').title().replace(' ', '')
        return create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=f"{resource_name.upper()}_NOT_FOUND",
            message=f"The referenced {resource_name} does not exist.",
            details=[{"field": field_name, "issue": f"Referenced {resource_name} with ID '{key_value}' not found"}],
        )
    return create_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="FOREIGN_KEY_VIOLATION",
        message="The referenced record does not exist.",
        details=[{"field": "reference", "issue": "Referenced record not found"}],
    )
```

**RULE 6.1.2: Foreign Key Constraint Rules**
- CORRECT HTTP Status: 404 Not Found
- CORRECT Error Code: `{RESOURCE}_NOT_FOUND` (e.g., `USER_NOT_FOUND`)
- CORRECT Message: User-friendly message explaining referenced resource doesn't exist
- CORRECT Details: Field name, referenced resource, and ID value

## RULE 7: Not Null Constraint Handling
### 7.1 Not Null Violation Error
**RULE 7.1.1: Handler Pattern**
```python
elif isinstance(orig_exc, NotNullViolationError):
    error_msg = str(orig_exc)
    match = re.search(r'column "([^"]+)"', error_msg)
    field_name = match.group(1) if match else "field"
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="REQUIRED_FIELD_MISSING",
        message=f"The field '{field_name}' is required and cannot be null.",
        details=[{"field": field_name, "issue": f"{field_name} is required"}],
    )
```

**RULE 7.1.2: Not Null Constraint Rules**
- CORRECT HTTP Status: 422 Unprocessable Entity
- CORRECT Error Code: `REQUIRED_FIELD_MISSING`
- CORRECT Message: User-friendly message explaining field is required
- CORRECT Details: Field name and issue description

## RULE 8: Check Constraint Handling
### 8.1 Check Violation Error
**RULE 8.1.1: Handler Pattern**
```python
elif isinstance(orig_exc, CheckViolationError):
    _, field_name = extract_constraint_info(str(orig_exc))
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="CHECK_CONSTRAINT_VIOLATION",
        message=f"The value provided for '{field_name}' violates a validation rule.",
        details=[{"field": field_name, "issue": "Value violates check constraint"}],
    )
```

**RULE 8.1.2: Check Constraint Rules**
- CORRECT HTTP Status: 422 Unprocessable Entity
- CORRECT Error Code: `CHECK_CONSTRAINT_VIOLATION`
- CORRECT Message: User-friendly message explaining validation rule violation
- CORRECT Details: Field name and issue description

## RULE 9: Exception Handler Registration
### 9.1 Handler Registration Order
**CRITICAL RULE:** Register database handlers **BEFORE** catch-all handler.

**RULE 9.1.1: Required Imports in `src/main.py`**
```python
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from src.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    database_exception_handler,
    catch_all_exception_handler,
)
from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import (
    UniqueViolationError,
    ForeignKeyViolationError,
    NotNullViolationError,
    CheckViolationError,
)
```

**RULE 9.1.2: Handler Registration Pattern**
```python
# Register handlers (order matters - most specific first)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
# Database handlers (BEFORE catch-all)
app.add_exception_handler(IntegrityError, database_exception_handler)
app.add_exception_handler(UniqueViolationError, database_exception_handler)
app.add_exception_handler(ForeignKeyViolationError, database_exception_handler)
app.add_exception_handler(NotNullViolationError, database_exception_handler)
app.add_exception_handler(CheckViolationError, database_exception_handler)
app.add_exception_handler(Exception, catch_all_exception_handler)  # Last
```

**RULE 9.1.3: Registration Order Rules**
- CORRECT Most specific exceptions first
- CORRECT Database handlers registered BEFORE catch-all handler
- CORRECT Catch-all handler registered LAST
- CORRECT Order matters - handlers are checked in registration order

**RULE 9.1.4: WRONG Handler Order (DO NOT DO THIS)**
```python
app.add_exception_handler(Exception, catch_all_exception_handler)  # INCORRECT First
app.add_exception_handler(IntegrityError, database_exception_handler)  # INCORRECT Never reached
```

**RULE 9.1.5: CORRECT Handler Order**
```python
app.add_exception_handler(IntegrityError, database_exception_handler)  # CORRECT First
app.add_exception_handler(Exception, catch_all_exception_handler)  # CORRECT Last
```

## RULE 10: Handling Both Exception Types
### 10.1 IntegrityError and Direct Exceptions
**CRITICAL RULE:** Handle both `IntegrityError` (wrapped) and direct asyncpg exceptions.

**RULE 10.1.1: Handle IntegrityError (Wrapped)**
```python
# Handle IntegrityError (wraps asyncpg exceptions)
if isinstance(exc, IntegrityError):
    orig_exc = exc.orig if hasattr(exc, 'orig') else exc
    
    if isinstance(orig_exc, UniqueViolationError):
        # Handle unique violation
        ...
    elif isinstance(orig_exc, ForeignKeyViolationError):
        # Handle foreign key violation
        ...
    # ... other constraint types
```

**RULE 10.1.2: Handle Direct Exceptions (Fallback)**
```python
# Handle direct asyncpg exceptions (fallback)
if isinstance(exc, UniqueViolationError):
    # Handle direct unique violation
    ...
elif isinstance(exc, ForeignKeyViolationError):
    # Handle direct foreign key violation
    ...
# ... other constraint types
```

**RULE 10.1.3: WRONG Pattern (DO NOT DO THIS)**
```python
if isinstance(exc, IntegrityError):
    # Only handles wrapped exceptions
    # INCORRECT Missing: Direct asyncpg exception handling
```

**RULE 10.1.4: CORRECT Pattern**
```python
if isinstance(exc, IntegrityError):
    orig_exc = exc.orig
    # Handle wrapped...
elif isinstance(exc, UniqueViolationError):  # CORRECT Direct handling
    # Handle direct...
```

## RULE 11: Critical Rules Summary
### 11.1 Mandatory Rules
**ALWAYS:**
1. CORRECT Handle both `IntegrityError` (wrapped) and direct asyncpg exceptions
2. CORRECT Register database handlers BEFORE catch-all handler
3. CORRECT Extract field names from constraint names (not generic "field")
4. CORRECT Use `StandardResponse` format with field-level details
5. CORRECT Validate at application level first (handler is fallback)

**NEVER:**
1. INCORRECT Register catch-all handler before database handlers
2. INCORRECT Use generic field names without extraction
3. INCORRECT Return raw database error messages
4. INCORRECT Skip field-level error details
5. INCORRECT Handle only wrapped or only direct exceptions

## RULE 12: Common Mistakes
### 12.1 Wrong Handler Order
**RULE 12.1.1: WRONG Pattern**
```python
app.add_exception_handler(Exception, catch_all_exception_handler)  # INCORRECT First
app.add_exception_handler(IntegrityError, database_exception_handler)  # INCORRECT Never reached
```

**RULE 12.1.2: CORRECT Pattern**
```python
app.add_exception_handler(IntegrityError, database_exception_handler)  # CORRECT First
app.add_exception_handler(Exception, catch_all_exception_handler)  # CORRECT Last
```

### 12.2 Missing Direct Exception Handling
**RULE 12.2.1: WRONG Pattern**
```python
if isinstance(exc, IntegrityError):
    # Only handles wrapped exceptions
    # INCORRECT Missing: Direct asyncpg exception handling
```

**RULE 12.2.2: CORRECT Pattern**
```python
if isinstance(exc, IntegrityError):
    orig_exc = exc.orig
    # Handle wrapped...
elif isinstance(exc, UniqueViolationError):  # CORRECT Direct handling
    # Handle direct...
```

### 12.3 Common Mistakes Reference Table
| Mistake | Correct Approach |
|---------|------------------|
| Registering catch-all before database handlers | Register database handlers BEFORE catch-all |
| Handling only wrapped exceptions | Handle both `IntegrityError` and direct asyncpg exceptions |
| Using generic "field" name | Extract field name from constraint name or error message |
| Returning raw database errors | Convert to user-friendly `StandardResponse` format |
| Missing field-level details | Include field name and issue in error details |

## RULE 13: Testing Patterns
### 13.1 Test Unique Constraint
**RULE 13.1.1: Test Pattern**
```python
# Unique constraint
response = client.post("/v1/users", json={"email": "existing@example.com"})
assert response.status_code == 409
assert response.json()["error"]["code"] == "DUPLICATE_EMAIL"
```

**RULE 13.1.2: Expected Response**
- CORRECT Status Code: 409 Conflict
- CORRECT Error Code: `DUPLICATE_EMAIL` (or `DUPLICATE_{FIELD}`)
- CORRECT Message: User-friendly message about duplicate value
- CORRECT Details: Field name and issue description

### 13.2 Test Foreign Key Constraint
**RULE 13.2.1: Test Pattern**
```python
# Foreign key constraint
response = client.post("/v1/customers", json={"user_id": "non-existent-uuid"})
assert response.status_code == 404
assert response.json()["error"]["code"] == "USER_NOT_FOUND"
```

**RULE 13.2.2: Expected Response**
- CORRECT Status Code: 404 Not Found
- CORRECT Error Code: `{RESOURCE}_NOT_FOUND` (e.g., `USER_NOT_FOUND`)
- CORRECT Message: User-friendly message about referenced resource not found
- CORRECT Details: Field name, referenced resource, and ID value

### 13.3 Test Not Null Constraint
**RULE 13.3.1: Test Pattern**
```python
# Not null constraint
response = client.post("/v1/users", json={"email": None})
assert response.status_code == 422
assert response.json()["error"]["code"] == "REQUIRED_FIELD_MISSING"
```

**RULE 13.3.2: Expected Response**
- CORRECT Status Code: 422 Unprocessable Entity
- CORRECT Error Code: `REQUIRED_FIELD_MISSING`
- CORRECT Message: User-friendly message about required field
- CORRECT Details: Field name and issue description

## RULE 14: Verification Checklist
### 14.1 Implementation Verification
Before marking database constraint handling as complete, verify:

**Imports:**
- CORRECT Imports added to `src/exceptions.py`
- CORRECT All required database exception types imported
- CORRECT `StandardResponse` and `ErrorInfo` imported

**Handler Function:**
- CORRECT `database_exception_handler` function exists
- CORRECT Handler handles both `IntegrityError` and direct asyncpg exceptions
- CORRECT Field names extracted from constraint names
- CORRECT All constraint types handled (unique, foreign key, not null, check)

**Handler Registration:**
- CORRECT Handlers registered in `src/main.py` BEFORE catch-all
- CORRECT All database exception types registered
- CORRECT Handler registration order is correct

**Error Responses:**
- CORRECT Error responses use `StandardResponse` format
- CORRECT Field-level error details included
- CORRECT Appropriate HTTP status codes used
- CORRECT User-friendly error messages provided

## RULE 15: Best Practices
### 15.1 Validation Strategy
**RULE 15.1.1: Prefer Application-Level Validation**
- CORRECT Validate at application level first (handler is fallback)
- CORRECT Use Pydantic schemas for input validation
- CORRECT Use service layer validation for business rules
- CORRECT Database constraint handler catches edge cases

**RULE 15.1.2: Use Descriptive Constraint Names**
- CORRECT Use descriptive constraint names for better field extraction
- CORRECT Example: `ix_users_email` vs `users_email_key`
- CORRECT Include table name prefix for clarity
- CORRECT Use meaningful constraint names

**RULE 15.1.3: Test Constraint Violations**
- CORRECT Test all constraint types (unique, foreign key, not null, check)
- CORRECT Verify user-friendly errors are returned
- CORRECT Verify field-level error details are included
- CORRECT Verify appropriate HTTP status codes are used

## RULE 16: Extending for New Constraint Types
### 16.1 Adding Support for New Constraint Types
**RULE 16.1.1: Example: Exclusion Constraints**
```python
from asyncpg.exceptions import ExclusionViolationError

# In database_exception_handler, add:
elif isinstance(orig_exc, ExclusionViolationError):
    _, field_name = extract_constraint_info(str(orig_exc))
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="EXCLUSION_VIOLATION",
        message=f"The provided values for '{field_name}' violate an exclusion constraint.",
        details=[{"field": field_name, "issue": "Value violates exclusion constraint"}],
    )

# In main.py, register:
app.add_exception_handler(ExclusionViolationError, database_exception_handler)
```

**RULE 16.1.2: Extension Rules**
- CORRECT Add exception type to imports
- CORRECT Add handler logic in `database_exception_handler`
- CORRECT Register handler in `src/main.py`
- CORRECT Use appropriate HTTP status code
- CORRECT Extract field name from constraint
- CORRECT Provide user-friendly error message

---

## Related Documentation

- **Error Handling:** `rules/creation/response_error_handling.md`
- **Error Prevention:** `rules/creation/error_prevention.md`
- **Error Book:** `rules/validate/error_book.md`
- **Database Setup:** `rules/creation/database_setup.md`

---

## Summary

This guide provides rule-based instructions for handling database constraint violations. Each rule is numbered and contains specific, actionable requirements.

**Key Principles:**
- Convert database errors to user-friendly messages
- Use appropriate HTTP status codes for each constraint type
- Extract field names from constraint names
- Provide field-level error details
- Handle both wrapped and direct exceptions

**Critical Reminders:**
- Register database handlers BEFORE catch-all handler
- Handle both `IntegrityError` and direct asyncpg exceptions
- Extract field names from constraint names (not generic "field")
- Use `StandardResponse` format for all error responses
- Validate at application level first (handler is fallback)
