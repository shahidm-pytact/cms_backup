# Error Book - Common Errors, Solutions, and Prevention

**Purpose:** Quick reference for common development errors, their solutions, and prevention patterns.

## RULE 1: Quick Reference Table
### 1.1 Error Reference Table
**RULE 1.1.1: Error Quick Reference**
| Error | File | Cause | Solution | Rulebook |
|-------|------|-------|----------|----------|
| RecursionError (BaseSettings) | `config.py` | `Field()` in `BaseSettings` | Direct assignment | `config_validate.md` |
| RecursionError (Generic) | `pagination.py` | `Field()` in `Generic[T]` | Direct assignment | `module_architecture_validate.md` |
| RecursionError (Decimal) | `schemas.py` | `Decimal = Field(...)` | `Annotated[Decimal, Field(...)]` | `module_architecture_validate.md` |
| Port Conflict | `docker-compose.yml` | Port already in use | Stop containers / Use different ports | `docker_validate.md` |
| Unnecessary Files | `docker-compose.dev.yml`, `.cursorrules` | Created automatically | Only create if user explicitly requests | `development_build.md` |
| SQLAlchemy Join Error | `router.py`, `service.py` | `.join()` without explicit ON clause | `join(Model, Model1.fk == Model2.pk)` | `module_architecture_validate.md` |
| ForeignKeyViolationError | `service.py` (ANY project) | Not validating foreign keys before insert/update | Validate existence, soft delete, permissions before DB operation | `module_architecture_validate.md` |
| KeyError in Enum Conversion | `models.py`, `router.py` | Using SQLAlchemy `Enum()` for enum fields | Use `String(n)` type, convert manually | `module_architecture_validate.md` |
| PaginatedResponse Field Mismatch | `router.py` | Using `size`/`pages` instead of `page_size`/`total_pages` | Use exact field names from schema | `module_architecture_validate.md` |
| FastAPI Route Ordering | `router.py` | Parameterized routes before specific routes | Define specific routes before `/{id}` | `module_architecture_validate.md` |
| Enum Comparison Type Mismatch | `router.py`, `service.py` | Using enum objects directly in queries | Use `.value` (e.g., `MemberRole.OWNER.value`) | `module_architecture_validate.md` |
| bcrypt Version Incompatibility | `requirements/base.txt` | `passlib==1.7.4` incompatible with `bcrypt>=5.0.0` | Pin `bcrypt==4.0.1` | `dependencies_validate.md` |
| OAuth2 Swagger UI Authorization | `router.py`, `dependencies.py` | Missing OAuth2-compatible `/token` endpoint | Add `/token` endpoint with `Form(...)` | `auth_setup.md` |
| Exception Constructor Mismatch | `service.py`, `exceptions.py` | Passing args to constructors that don't accept them | Don't pass args, add `self.message` to `StandardErrorResponse` | Exception handling |
| Alembic Config AttributeError | `alembic/env.py` | Using `config.config_file_path` instead of `config.config_file_name` | Change to `config.config_file_name` | `database_setup.md` |
| ImportError: cannot import name 'tuple' | `repository.py` | Importing `tuple` from `typing` in Python 3.11+ | Remove `tuple` from typing imports, use built-in `tuple` | Python 3.11+ compatibility |
| ImportError: circular import | `dependencies.py`, `service.py` | Module A imports Module B, Module B imports Module A | Move shared functions to utility module | Module architecture |
| AssertionError: path prefix must not end with '/' | `config.py`, `main.py` | FastAPI prefix ending with '/' | Remove trailing slash from `api_prefix` | FastAPI configuration |

## RULE 2: RecursionError Patterns
### 2.1 Error 1: Field() in BaseSettings
**RULE 2.1.1: Error Description**
- Error: `RecursionError: maximum recursion depth exceeded`
- File: `src/config.py`
- When: During application startup, when importing `Settings` class

**RULE 2.1.2: Cause**
- Using `Field()` with `BaseSettings` in Pydantic v2 causes infinite recursion

**RULE 2.1.3: WRONG Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG
class Settings(BaseSettings):
    database_url: str = Field(default="...", description="...")  # INCORRECT ERROR
```

**RULE 2.1.4: CORRECT Pattern**
```python
# CORRECT
class Settings(BaseSettings):
    database_url: str = "postgresql://..."  # CORRECT Direct assignment
    # Description can be added as comment if needed
```

**RULE 2.1.5: Prevention Rules**
- CORRECT BaseSettings fields MUST use direct assignment (no `Field()`)
- INCORRECT NEVER use `Field()` in BaseSettings classes
- CORRECT Use comments for field descriptions if needed

**RULE 2.1.6: Reference**
- Rule: `config_validate.md` - NEVER use `Field()` in BaseSettings classes

### 2.2 Error 2: Field() in Generic Models
**RULE 2.2.1: Error Description**
- Error: `RecursionError: maximum recursion depth exceeded`
- File: `src/pagination.py`
- When: During application startup, when importing `PaginatedResponse` class

**RULE 2.2.2: Cause**
- Using `Field()` in Generic models (`Generic[T]`) without default values causes infinite recursion

**RULE 2.2.3: WRONG Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T] = Field(description="...")  # INCORRECT ERROR
```

**RULE 2.2.4: CORRECT Pattern**
```python
# CORRECT
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]  # CORRECT No Field() needed
    total: int
    page: int
```

**RULE 2.2.5: Prevention Rules**
- CORRECT Generic models don't need `Field()`
- CORRECT Use direct assignment for Generic model fields
- INCORRECT Using `Field()` in Generic models causes recursion

**RULE 2.2.6: Reference**
- Rule: `module_architecture_validate.md` - Generic models don't need `Field()`

### 2.3 Error 3: Field() with Decimal and Constraints
**RULE 2.3.1: Error Description**
- Error: `RecursionError: maximum recursion depth exceeded`
- File: `src/*/schemas.py`
- When: During request validation with Decimal field

**RULE 2.3.2: Cause**
- Using `Field()` directly with `Decimal` type and validation constraints causes infinite recursion

**RULE 2.3.3: WRONG Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG
from decimal import Decimal
from pydantic import BaseModel, Field

class TimesheetCreate(BaseModel):
    hours_worked: Decimal = Field(..., gt=0)  # INCORRECT ERROR
```

**RULE 2.3.4: CORRECT Pattern**
```python
# CORRECT
from typing import Annotated
from decimal import Decimal
from pydantic import BaseModel, Field

class TimesheetCreate(BaseModel):
    hours_worked: Annotated[Decimal, Field(gt=0, description="Hours worked")]  # CORRECT
```

**RULE 2.3.5: Prevention Rules**
- CORRECT Use `Annotated[Decimal, Field(...)]` for complex types with constraints
- INCORRECT Using `Field()` directly with Decimal causes recursion
- CORRECT Use Annotated pattern for Decimal, datetime with validation

**RULE 2.3.6: Reference**
- Rule: `module_architecture_validate.md` - Use `Annotated[Decimal, Field(...)]` for complex types with constraints

## RULE 3: SQLAlchemy Errors
### 3.1 Error 6: Missing JOIN ON Clause
**RULE 3.1.1: Error Description**
- Error: `InvalidRequestError: Don't know how to join to <Mapper>... Please use .select_from() method...`
- File: `router.py`, `service.py`
- When: During API endpoint execution with JOIN queries

**RULE 3.1.2: Cause**
- Using `.join()` without explicit ON clause when SQLAlchemy cannot infer the join condition

**RULE 3.1.3: WRONG Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG
query = select(Member).join(Organization).where(...)  # INCORRECT Missing ON clause
```

**RULE 3.1.4: CORRECT Pattern**
```python
# CORRECT
query = select(Member, Organization).join(
    Organization,
    Member.organization_id == Organization.id  # CORRECT Explicit join condition
).where(...)
```

**RULE 3.1.5: Prevention Rules**
- CORRECT Always provide explicit ON clause: `Model1.foreign_key == Model2.primary_key`
- INCORRECT Skip explicit join conditions
- CORRECT Use explicit join condition format: `Model1.fk == Model2.pk`

### 3.2 Error 7: ForeignKeyViolationError (Universal)
**RULE 3.2.1: Error Description**
- Error: `ForeignKeyViolationError: insert or update violates foreign key constraint`
- File: `service.py` (ANY project)
- When: During insert/update with non-existent foreign key

**RULE 3.2.2: Cause**
- Not validating that foreign key references exist before inserting or updating records

**RULE 3.2.3: CORRECT Pattern - Universal Validation**
```python
# CORRECT: Universal pattern - validate before DB operation
async def create_record_with_foreign_key(
    self,
    foreign_key_id: UUID,
    data: CreateSchema,
) -> Entity:
    # CORRECT STEP 1: Validate foreign entity exists
    foreign_entity_result = await self.session.execute(
        select(ForeignEntity).where(
            ForeignEntity.id == foreign_key_id,
            ForeignEntity.deleted_at.is_(None),  # CORRECT Check soft delete (if field exists)
        )
    )
    foreign_entity = foreign_entity_result.scalar_one_or_none()
    if not foreign_entity:
        raise NotFoundError("ForeignEntity", str(foreign_key_id))
    
    # CORRECT STEP 2: Validate permissions (if applicable)
    # ... permission checks ...
    
    # CORRECT STEP 3: Now safe to create record
    record = Entity(foreign_key_id=foreign_key_id, ...)
    self.session.add(record)
    await self.session.commit()
    return record
```

**RULE 3.2.4: Critical Prevention Rules**
- CORRECT ALWAYS validate foreign key references before insert/update - NO EXCEPTIONS
- CORRECT Check model fields before using - verify field exists (e.g., `deleted_at` exists before using `deleted_at.is_(None)`)
- CORRECT Validate optional foreign keys - if provided, must validate
- CORRECT Apply to ALL services - not just one specific module
- CORRECT Validate proactively - don't fix errors reactively, validate upfront
- INCORRECT Skip foreign key validation

**RULE 3.2.5: Pattern for Optional Foreign Keys**
```python
# CORRECT: Validate optional foreign key if provided
if data.optional_foreign_key_id:  # Check if optional FK is provided
    optional_entity_result = await self.session.execute(
        select(OptionalEntity).where(
            OptionalEntity.id == data.optional_foreign_key_id,
            # Check soft delete only if field exists in model
            # OptionalEntity.deleted_at.is_(None),  # Only if model has deleted_at field
        )
    )
    optional_entity = optional_entity_result.scalar_one_or_none()
    if not optional_entity:
        raise NotFoundError("OptionalEntity", str(data.optional_foreign_key_id))
```

**RULE 3.2.6: Pattern for Checking Model Fields**
```python
# CORRECT: Check if model field exists before using
# Best practice: Check model definition first
# If model has deleted_at field → use deleted_at.is_(None)
# If model doesn't have deleted_at field → don't use it

# Example:
# AttendanceRecord model: NO deleted_at field → Don't use deleted_at.is_(None)
# Timesheet model: HAS deleted_at field → Use deleted_at.is_(None)
```

**RULE 3.2.7: Reference**
- Rule: `module_architecture_validate.md` - Universal foreign key validation pattern

### 3.3 Error 11: Enum Comparison Type Mismatch

**RULE 3.3.1: Error Description**
- Error: `UndefinedFunctionError: operator does not exist: memberrole = character varying`
- File: `router.py`, `service.py`
- When: During API endpoint execution with enum comparisons in queries

**RULE 3.3.2: Cause**
- Using enum objects (like `MemberRole.OWNER`) directly in SQLAlchemy queries instead of converting them to strings with `.value`

**RULE 3.3.3: WRONG Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG
Member.role.in_([MemberRole.OWNER, MemberRole.ADMIN])  # INCORRECT Type mismatch
```

**RULE 3.3.4: CORRECT Pattern**
```python
# CORRECT
Member.role.in_([MemberRole.OWNER.value, MemberRole.ADMIN.value])  # CORRECT Use .value
```

**RULE 3.3.5: Prevention Rules**
- CORRECT Always use `.value` when comparing enums in SQLAlchemy queries
- INCORRECT Using enum objects directly causes type mismatch
- CORRECT Convert enum to string with `.value` before query

## RULE 4: FastAPI Errors
### 4.1 Error 9: PaginatedResponse Field Name Mismatch
**RULE 4.1.1: Error Description**
- Error: `ValidationError: Field required [type=missing, input_value={'size': 20, 'pages': 1}]`
- File: `router.py`
- When: During API endpoint execution with paginated responses

**RULE 4.1.2: Cause**
- Using incorrect field names (`size`, `pages`) instead of schema-defined names (`page_size`, `total_pages`)

**RULE 4.1.3: WRONG Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG
PaginatedResponse(
    items=items,
    total=total,
    page=page,
    size=limit,  # INCORRECT Should be 'page_size'
    pages=total_pages,  # INCORRECT Should be 'total_pages'
)
```

**RULE 4.1.4: CORRECT Pattern**
```python
# CORRECT
PaginatedResponse(
    items=items,
    total=total,
    page=page,
    page_size=limit,  # CORRECT Must be 'page_size'
    total_pages=total_pages,  # CORRECT Must be 'total_pages'
)
```

**RULE 4.1.5: Prevention Rules**
- CORRECT Always use exact field names from schema: `page_size`, `total_pages` (NOT `size`, `pages`)
- INCORRECT Using incorrect field names causes validation errors
- CORRECT Verify field names match schema definition

### 4.2 Error 10: FastAPI Route Ordering
**RULE 4.2.1: Error Description**
- Error: `422 Unprocessable Entity` when calling specific routes like `/summary`
- File: `router.py`
- When: When calling specific routes like `/summary` or `/calendar`

**RULE 4.2.2: Cause**
- Defining parameterized routes (like `/{id}`) before specific routes (like `/summary`, `/calendar`) causes FastAPI to match specific paths to parameterized routes first

**RULE 4.2.3: WRONG Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG: Parameterized route before specific routes
@router.get("", ...)  # List endpoint
@router.get("/{id}", ...)  # INCORRECT ERROR: This will match /summary first
@router.get("/summary", ...)  # INCORRECT ERROR: Never reached
```

**RULE 4.2.4: CORRECT Pattern**
```python
# CORRECT: Specific routes before parameterized routes
@router.get("", ...)  # List endpoint
@router.get("/summary", ...)  # CORRECT Specific route - BEFORE /{id}
@router.get("/calendar", ...)  # CORRECT Specific route - BEFORE /{id}
@router.get("/{id}", ...)  # CORRECT Parameterized route - AFTER specific routes
```

**RULE 4.2.5: Prevention Rules**
- CORRECT Order: List → Specific → Parameterized
- CORRECT Define specific routes before parameterized routes
- INCORRECT Define parameterized routes before specific routes

### 4.3 Error 13: OAuth2 Swagger UI Authorization Not Working
**RULE 4.3.1: Error Description**
- Error: `401 Unauthorized` when using Swagger UI "Authorize" button
- File: `router.py`, `dependencies.py`
- When: When clicking "Authorize" button in Swagger UI

**RULE 4.3.2: Cause**
- Missing OAuth2-compatible `/token` endpoint that accepts form data

**RULE 4.3.3: CORRECT Pattern**
```python
# CORRECT: Add OAuth2-compatible token endpoint
@router.post("/token", status_code=status.HTTP_200_OK)
async def token(
    username: str = Form(...),  # CORRECT OAuth2 uses 'username' but treat as email
    password: str = Form(...),  # CORRECT Form data (not JSON)
    session: AsyncSession = Depends(get_session),
):
    """OAuth2-compatible token endpoint for Swagger UI authorization"""
    service = UserService(session)
    user = await service.authenticate_user(username, password)
    tokens = await service.create_tokens(user)
    return {
        "access_token": tokens["access_token"],
        "token_type": "bearer"  # CORRECT OAuth2-compatible response
    }

# CORRECT: Update OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/v1/users/token",  # CORRECT Point to OAuth2-compatible endpoint
    auto_error=False
)
```

**RULE 4.3.4: Prevention Rules**
- CORRECT MUST use `Form(...)` for OAuth2 token endpoints (NOT JSON body)
- CORRECT Return OAuth2-compatible response format
- CORRECT Point OAuth2PasswordBearer to token endpoint
- INCORRECT Using JSON body for token endpoint

**RULE 4.3.5: Reference**
- Rule: `auth_setup.md` - MUST use `Form(...)` for OAuth2 token endpoints (NOT JSON body)

## RULE 5: Dependency Errors
### 5.1 Error 12: bcrypt Version Incompatibility
**RULE 5.1.1: Error Description**
- Error: `ValueError: password cannot be longer than 72 bytes`
- File: `requirements/base.txt`
- When: During user registration, password hashing

**RULE 5.1.2: Cause**
- `passlib==1.7.4` is not compatible with `bcrypt>=5.0.0`

**RULE 5.1.3: WRONG Pattern (DO NOT DO THIS)**
```txt
# INCORRECT WRONG
passlib[bcrypt]==1.7.4
bcrypt==5.0.0  # INCORRECT ERROR: Incompatible
```

**RULE 5.1.4: CORRECT Pattern**
```txt
# CORRECT
passlib[bcrypt]==1.7.4
bcrypt==4.0.1  # CORRECT Pin to compatible version
```

**RULE 5.1.5: Prevention Rules**
- CORRECT MUST pin `bcrypt==4.0.1` (NOT 5.0.0)
- INCORRECT Using bcrypt 5.0.0 with passlib 1.7.4 causes errors
- CORRECT Verify dependency compatibility before upgrading

**RULE 5.1.6: Reference**
- Rule: `dependencies_validate.md` - MUST pin `bcrypt==4.0.1` (NOT 5.0.0)

## RULE 6: Other Errors
### 6.1 Error 4: Port Already in Use (Docker)
**RULE 6.1.1: Error Description**
- Error: `Error response from daemon: Bind for 0.0.0.0:5433 failed: port is already allocated`
- When: When starting Docker containers

**RULE 6.1.2: Solutions**
```bash
# Method 1: Stop conflicting containers
docker compose down

# Method 2: Use different ports
# docker-compose.yml
services:
  db:
    ports:
      - "5434:5432"  # Changed from 5433 to 5434
```

**RULE 6.1.3: Prevention Rules**
- CORRECT Always use non-standard host ports to avoid conflicts
- CORRECT Stop conflicting containers before starting new ones
- CORRECT Check for port conflicts before starting services

### 6.2 Error 5: Creating Optional Files Unnecessarily
**RULE 6.2.1: Error Description**
- Error Type: Unnecessary File Creation
- Files: `docker-compose.dev.yml`, `.cursorrules`

**RULE 6.2.2: Cause**
- Creating optional files automatically when they're not needed

**RULE 6.2.3: Solutions**
- CORRECT Only create optional files if user explicitly requests them
- CORRECT Use existing `docker-compose.yml` if it works
- INCORRECT Don't create files "just in case"

**RULE 6.2.4: Prevention Rules**
- CORRECT Only create files user explicitly requests
- INCORRECT Creating optional files automatically
- CORRECT Check if existing config is sufficient

**RULE 6.2.5: Reference**
- Rule: `development_build.md` - Only create optional files if user explicitly requests

### 6.3 Error 8: KeyError in SQLAlchemy Enum Conversion
**RULE 6.3.1: Error Description**
- Error: `KeyError: 'owner'` in SQLAlchemy enum conversion
- File: `models.py`, `router.py`
- When: When reading enum fields from database

**RULE 6.3.2: Cause**
- Using SQLAlchemy's `Enum()` type for enum fields causes conversion failures

**RULE 6.3.3: WRONG Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG
from sqlalchemy import Enum

class Member(Base):
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole, create_type=False),  # INCORRECT ERROR: KeyError
    )
```

**RULE 6.3.4: CORRECT Pattern**
```python
# CORRECT
from sqlalchemy import String

class Member(Base):
    role: Mapped[MemberRole] = mapped_column(
        String(50),  # CORRECT Store as string
        nullable=False,
        default=MemberRole.MEMBER.value,  # CORRECT Use .value for default
    )
```

**RULE 6.3.5: Prevention Rules**
- CORRECT Always use `String(n)` type for enum fields (NOT SQLAlchemy `Enum()`)
- INCORRECT Using SQLAlchemy Enum() causes conversion failures
- CORRECT Use `.value` for enum defaults

### 6.4 Error 14: Exception Constructor Mismatch
**RULE 6.4.1: Error Description**
- Error: `TypeError: InvalidCredentialsException.__init__() takes 1 positional argument but 2 were given`
- File: `service.py`, `exceptions.py`
- When: During exception handling in service layer

**RULE 6.4.2: Cause**
- Passing arguments to exception constructors that don't accept them, or missing `self.message` attribute

**RULE 6.4.3: WRONG Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG
except InvalidCredentialsException as e:
    raise InvalidCredentialsException(str(e.detail))  # INCORRECT ERROR: Constructor takes 0 args
```

**RULE 6.4.4: CORRECT Pattern**
```python
# CORRECT
except InvalidCredentialsException:
    raise  # CORRECT Re-raise as-is

# CORRECT: Add self.message to StandardErrorResponse
class StandardErrorResponse(HTTPException):
    def __init__(self, error_code: str, message: str, ...):
        self.error_code = error_code
        self.message = message  # CORRECT Store as attribute
        super().__init__(status_code=status_code, detail={"message": message, ...})
```

**RULE 6.4.5: Prevention Rules**
- CORRECT Check exception constructor signatures before re-raising
- CORRECT Add `self.message` to `StandardErrorResponse`
- CORRECT Use `raise` to re-raise exceptions when no transformation needed
- INCORRECT Passing arguments to constructors that don't accept them

### 6.5 Error 15: Alembic Config AttributeError
**RULE 6.5.1: Error Description**
- Error: `AttributeError: 'Config' object has no attribute 'config_file_path'`
- File: `alembic/env.py`
- When: During Docker migration service execution

**RULE 6.5.2: Cause**
- Using incorrect attribute name `config_file_path` instead of `config_file_name`

**RULE 6.5.3: WRONG Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG
if config.config_file_path is not None:  # INCORRECT ERROR: Attribute doesn't exist
    fileConfig(config.config_file_path)
```

**RULE 6.5.4: CORRECT Pattern**
```python
# CORRECT
if config.config_file_name is not None:  # CORRECT Use config_file_name
    fileConfig(config.config_file_name)
```

**RULE 6.5.5: Prevention Rules**
- CORRECT MUST use `config.config_file_name` (NOT `config_file_path`)
- INCORRECT Using incorrect attribute name causes AttributeError
- CORRECT Verify attribute name matches Alembic config API

**RULE 6.5.6: Reference**
- Rule: `database_setup.md` - MUST use `config.config_file_name` (NOT `config_file_path`)

### 6.6 Error 16: ImportError: cannot import name 'tuple' from 'typing'
**RULE 6.6.1: Error Description**
- Error: `ImportError: cannot import name 'tuple' from 'typing'`
- File: `repository.py` (any module)
- When: During application startup in Python 3.11+

**RULE 6.6.2: Cause**
- In Python 3.9+, `tuple` is a built-in type and doesn't need to be imported from `typing`
- In Python 3.11+, `tuple` is no longer available in the `typing` module

**RULE 6.6.3: WRONG Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG
from typing import Optional, tuple  # INCORRECT ERROR: tuple not in typing in Python 3.11+

def method(self) -> tuple[list[Model], int]:  # This is correct, but import is wrong
    ...
```

**RULE 6.6.4: CORRECT Pattern**
```python
# CORRECT
from typing import Optional  # CORRECT: tuple is built-in, no import needed

def method(self) -> tuple[list[Model], int]:  # CORRECT: Use built-in tuple for type hints
    ...
```

**RULE 6.6.5: Prevention Rules**
- CORRECT In Python 3.9+, use built-in `tuple` directly for type hints (no import needed)
- INCORRECT Don't import `tuple` from `typing` in Python 3.11+
- CORRECT Use `tuple[...]` syntax directly for type hints
- CORRECT Only import `Optional`, `List`, `Dict`, etc. from `typing` when needed

**RULE 6.6.6: Reference**
- Python 3.9+ PEP 585: Built-in collection types can be used directly for type hints

### 6.7 Error 17: ImportError: circular import
**RULE 6.7.1: Error Description**
- Error: `ImportError: cannot import name 'X' from partially initialized module 'Y' (most likely due to a circular import)`
- File: `dependencies.py`, `service.py` (any module pair)
- When: During application startup when modules import each other

**RULE 6.7.2: Cause**
- Module A imports Module B, and Module B imports Module A (directly or indirectly)
- Common pattern: `dependencies.py` imports `Service` from `service.py`, and `service.py` imports helper functions from `dependencies.py`

**RULE 6.7.3: WRONG Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG: Circular import
# dependencies.py
from src.users.service import UserService  # Imports service

def _is_superadmin(user: User) -> bool:  # Helper function
    ...

# service.py
from src.users.dependencies import _is_superadmin  # INCORRECT ERROR: Circular import
```

**RULE 6.7.4: CORRECT Pattern**
```python
# CORRECT: Move shared functions to utility module
# utils.py
def is_superadmin(user: User) -> bool:  # CORRECT: Shared utility function
    ...

# dependencies.py
from src.users.service import UserService  # OK: No circular dependency
from src.users.utils import is_superadmin  # CORRECT: Import from utils

# service.py
from src.users.utils import is_superadmin  # CORRECT: Import from utils
```

**RULE 6.7.5: Prevention Rules**
- CORRECT Move shared helper functions to `utils.py` or separate utility module
- CORRECT Break circular dependencies by introducing a third module
- INCORRECT Don't import from modules that import you
- CORRECT Use `TYPE_CHECKING` for type-only imports if needed
- CORRECT Structure: `utils.py` → no dependencies on `service.py` or `dependencies.py`

**RULE 6.7.6: Reference**
- Rule: Module architecture - Break circular dependencies by moving shared code to utility modules

### 6.8 Error 18: AssertionError: path prefix must not end with '/'
**RULE 6.8.1: Error Description**
- Error: `AssertionError: A path prefix must not end with '/', as the routes will start with '/'`
- File: `config.py`, `main.py`
- When: During application startup when including router with prefix

**RULE 6.8.2: Cause**
- FastAPI doesn't allow path prefixes to end with '/' because routes already start with '/'
- Common mistake: Setting `api_prefix = "/v1/"` instead of `api_prefix = "/v1"`

**RULE 6.8.3: WRONG Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG
# config.py
class Settings(BaseSettings):
    api_prefix: str = "/v1/"  # INCORRECT ERROR: Trailing slash

# main.py
app.include_router(api_router, prefix=settings.api_prefix)  # Error: prefix ends with '/'
```

**RULE 6.8.4: CORRECT Pattern**
```python
# CORRECT
# config.py
class Settings(BaseSettings):
    api_prefix: str = "/v1"  # CORRECT: No trailing slash

# main.py
app.include_router(api_router, prefix=settings.api_prefix)  # CORRECT: Works
```

**RULE 6.8.5: Prevention Rules**
- CORRECT Always use path prefixes without trailing slash: `"/v1"` (NOT `"/v1/"`)
- INCORRECT Don't add trailing slash to FastAPI path prefixes
- CORRECT FastAPI automatically handles path joining correctly
- CORRECT Routes defined in router already start with '/', so prefix shouldn't end with '/'

**RULE 6.8.6: Reference**
- FastAPI documentation: Path prefixes must not end with '/'

## RULE 7: Quick Reference - When to Use Field()
### 7.1 Use Field() Directly
**RULE 7.1.1: When to Use Field() Directly**
- CORRECT Simple types (str, int, UUID, EmailStr)
- CORRECT Regular BaseModel (not BaseSettings)
- CORRECT Without Generic types

**RULE 7.1.2: Example**
```python
class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User email")  # CORRECT OK
    name: str = Field(..., max_length=255)  # CORRECT OK
```

### 7.2 Don't Use Field() Directly
**RULE 7.2.1: When NOT to Use Field() Directly**
- INCORRECT BaseSettings classes → Use direct assignment
- INCORRECT Generic models (Generic[T]) → Use direct assignment
- INCORRECT Complex types (Decimal, datetime) with constraints → Use `Annotated`

### 7.3 Use Annotated Pattern
**RULE 7.3.1: When to Use Annotated Pattern**
- CORRECT Complex types with constraints
- CORRECT Decimal, datetime with validation

**RULE 7.3.2: Example**
```python
from typing import Annotated
from decimal import Decimal

class TimesheetCreate(BaseModel):
    hours: Annotated[Decimal, Field(gt=0)]  # CORRECT
```

### 7.4 Use Direct Assignment
**RULE 7.4.1: When to Use Direct Assignment**
- CORRECT BaseSettings fields
- CORRECT Generic model fields
- CORRECT Simple fields without constraints

**RULE 7.4.2: Example**
```python
class Settings(BaseSettings):
    database_url: str = "postgresql://..."  # CORRECT

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]  # CORRECT
```

## RULE 8: Critical Prevention Rules
### 8.1 Pydantic v2 Patterns
**RULE 8.1.1: Pydantic v2 Rules**
- CORRECT BaseSettings → Direct assignment (NO Field())
- CORRECT Generic models → Direct assignment (NO Field())
- CORRECT Complex types with constraints → `Annotated[Type, Field(...)]`
- CORRECT Simple types → `Field()` directly is OK

### 8.2 SQLAlchemy Queries
**RULE 8.2.1: SQLAlchemy Query Rules**
- CORRECT Always provide explicit ON clause in JOIN queries
- CORRECT Always validate foreign key references before insert/update
- CORRECT Always use `.value` when comparing enums in queries
- CORRECT Always use `String(n)` for enum fields (NOT SQLAlchemy Enum())

### 8.3 FastAPI Routes
**RULE 8.3.1: FastAPI Route Rules**
- CORRECT Always define specific routes BEFORE parameterized routes
- CORRECT Always use exact field names from schema (`page_size`, `total_pages`)
- CORRECT Always provide OAuth2-compatible `/token` endpoint for Swagger UI
- CORRECT Always use path prefixes without trailing slash: `"/v1"` (NOT `"/v1/"`)

### 8.4 Dependencies
**RULE 8.4.1: Dependency Rules**
- CORRECT Always pin `bcrypt==4.0.1` (NOT 5.0.0)
- CORRECT Always verify dependency compatibility before upgrading

### 8.5 Foreign Key Validation (Universal)
**RULE 8.5.1: Foreign Key Validation Rules**
- CORRECT ALWAYS validate foreign key references before insert/update - NO EXCEPTIONS
- CORRECT Check model fields before using - verify field exists (e.g., `deleted_at` exists before using `deleted_at.is_(None)`)
- CORRECT Validate optional foreign keys - if provided, must validate
- CORRECT Apply to ALL services - not just one specific module

### 8.6 File Creation
**RULE 8.6.1: File Creation Rules**
- CORRECT Only create files user explicitly requests
- INCORRECT Don't create optional files "just in case"
- CORRECT Check if existing config is sufficient

### 8.7 Exception Handling
**RULE 8.7.1: Exception Handling Rules**
- CORRECT Check exception constructor signatures before re-raising
- CORRECT Add `self.message` to `StandardErrorResponse` classes
- CORRECT Use `raise` to re-raise exceptions when no transformation needed

### 8.8 Python 3.11+ Compatibility
**RULE 8.8.1: Python 3.11+ Import Rules**
- CORRECT Don't import `tuple` from `typing` - use built-in `tuple` directly
- CORRECT Use `tuple[...]` syntax directly for type hints (no import needed)
- INCORRECT Importing `tuple` from `typing` causes ImportError in Python 3.11+

### 8.9 Module Architecture
**RULE 8.9.1: Circular Import Prevention Rules**
- CORRECT Move shared helper functions to `utils.py` or separate utility module
- CORRECT Break circular dependencies by introducing a third module
- INCORRECT Don't import from modules that import you
- CORRECT Structure dependencies: `utils.py` → no dependencies on `service.py` or `dependencies.py`

### 8.10 Database Migrations
**RULE 8.10.1: Database Migration Rules**
- CORRECT Always use `config.config_file_name` (NOT `config_file_path`)

## RULE 9: Testing Checklist1
### 9.1 Verification Checklist
**RULE 9.1.1: After Fixing Errors, Always Verify**
- CORRECT Application starts without errors
- CORRECT No RecursionError in logs
- CORRECT All schemas import successfully
- CORRECT API endpoints work correctly
- CORRECT Docker containers start without port conflicts
- CORRECT All JOIN queries have explicit ON clauses
- CORRECT All foreign key references validated before insert/update
- CORRECT All enum fields use `String(n)` type (not SQLAlchemy Enum())
- CORRECT All PaginatedResponse use correct field names (`page_size`, `total_pages`)
- CORRECT All specific routes defined before parameterized routes
- CORRECT All enum comparisons in queries use `.value`
- CORRECT Password hashing works correctly (test after dependency updates)
- CORRECT Swagger UI authorization flow works (click "Authorize" button)
- CORRECT All exception constructors match their usage
- CORRECT Migration service runs successfully
- CORRECT No ImportError for `tuple` from `typing` (Python 3.11+)
- CORRECT No circular import errors
- CORRECT FastAPI path prefixes don't end with '/'

## Summary
This guide provides rule-based instructions for common development errors, their solutions, and prevention patterns. Each rule is numbered and contains specific, actionable requirements.

**Key Principles:**
- Use direct assignment for BaseSettings and Generic models
- Always validate foreign key references before DB operations
- Use explicit join conditions in SQLAlchemy queries
- Define specific routes before parameterized routes
- Pin critical dependencies to compatible versions

**Critical Reminders:**
- NEVER use `Field()` in BaseSettings classes
- ALWAYS validate foreign key references before insert/update
- ALWAYS use `.value` when comparing enums in queries
- ALWAYS use `String(n)` for enum fields (NOT SQLAlchemy Enum())
- ALWAYS pin `bcrypt==4.0.1` (NOT 5.0.0)
- ALWAYS provide OAuth2-compatible `/token` endpoint for Swagger UI
- NEVER import `tuple` from `typing` in Python 3.11+ (use built-in `tuple`)
- ALWAYS break circular imports by moving shared code to utility modules
- ALWAYS use path prefixes without trailing slash: `"/v1"` (NOT `"/v1/"`)
