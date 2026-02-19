# Error Prevention Guide - Critical Rules

**Purpose:** Prevent common errors encountered during development by following these critical rules.

**CRITICAL:** These rules are based on **actual production errors**. **STRICTLY FOLLOW** them to prevent repeating mistakes.

## RULE 1: Password Hashing Dependencies
### 1.1 Issue: bcrypt/passlib Compatibility Error
**Error:** `ValueError: password cannot be longer than 72 bytes` or `AttributeError: module 'bcrypt' has no attribute '__about__'`

**Root Cause:** `bcrypt 5.0.0` is **INCOMPATIBLE** with `passlib 1.7.4`

**CRITICAL RULE:**
- CORRECT: **MUST pin bcrypt to version 4.0.1** in `requirements/base.txt`
- INCORRECT: **NEVER use bcrypt 5.0.0** with passlib 1.7.4

**Required in `requirements/base.txt`:**
```txt
passlib[bcrypt]==1.7.4
bcrypt==4.0.1  # CRITICAL: Pin to 4.0.1 for passlib compatibility
```

**Verification Checklist:**
- CORRECT: `bcrypt==4.0.1` in `requirements/base.txt`
- CORRECT: `passlib[bcrypt]==1.7.4` in `requirements/base.txt`
- CORRECT: No bcrypt 5.0.0 installed

## RULE 2: JWT Token None Check
### 2.1 Issue: AttributeError when token is None
**Error:** `AttributeError: 'NoneType' object has no attribute 'rsplit'`

**Root Cause:** `OAuth2PasswordBearer` with `auto_error=False` returns `None` when token is missing, but code tries to decode `None`

**CRITICAL RULE:**
- CORRECT: **ALWAYS check if token is None** before decoding
- INCORRECT: **NEVER decode token without None check**

**Required Pattern in `dependencies.py`:**
```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    credentials_exception = UnauthenticatedError("Could not validate credentials")
    
    # CRITICAL: Check if token is provided
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, auth_settings.SECRET_KEY, algorithms=[auth_settings.ALGORITHM])
        # ... rest of code
    except JWTError:
        raise credentials_exception
```

**Verification Checklist:**
- CORRECT: Token None check exists before `jwt.decode()`
- CORRECT: Proper exception raised when token is None

## RULE 3: OAuth2 Token Endpoint
### 3.1 Issue: Swagger UI Authorization Fails
**Error:** `400 Bad Request` or `401 Unauthorized` in OAuth2 authorization modal

**Root Cause:** OAuth2 requires form data (username/password), but login endpoint uses JSON

**CRITICAL RULE:**
- CORRECT: **MUST create OAuth2-compatible token endpoint** for Swagger UI
- CORRECT: **MUST accept form data** (username, password) not JSON
- CORRECT: **MUST return OAuth2-compatible response** (access_token, token_type)
- CORRECT: **MUST handle errors in OAuth2 format**

**Required Endpoint in `router.py`:**
```python
@router.post("/token", status_code=status.HTTP_200_OK)
async def token(
    username: str = Form(...),  # OAuth2 uses 'username' but we treat it as email
    password: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    """OAuth2-compatible token endpoint for Swagger UI authorization"""
    try:
        service = UserService(session)
        user = await service.authenticate_user(username, password)
        tokens = await service.create_tokens(user)
        return {
            "access_token": tokens["access_token"],
            "token_type": "bearer"
        }
    except (InvalidCredentialsException, InactiveUserException):
        # CRITICAL: Return OAuth2-compatible error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

**Required in `dependencies.py`:**
```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/users/token", auto_error=False)
```

**Verification Checklist:**
- CORRECT: Token endpoint accepts `Form(...)` parameters
- CORRECT: Returns `{"access_token": "...", "token_type": "bearer"}`
- CORRECT: Errors return proper OAuth2 format with `WWW-Authenticate` header
- CORRECT: `OAuth2PasswordBearer` uses correct `tokenUrl`

## RULE 4: Form Data Dependency (python-multipart)
### 4.1 Issue: RuntimeError when using Form(...) parameters
**Error:** `RuntimeError: Form data requires "python-multipart" to be installed`

**Root Cause:** FastAPI requires `python-multipart` package to parse form data (`Form(...)` parameters), but it's not included by default

**CRITICAL RULE:**
- CORRECT: **MUST include `python-multipart==0.0.6`** in `requirements/base.txt` if using `Form(...)` parameters
- CORRECT: **OAuth2 token endpoints ALWAYS use Form(...)** → Always requires python-multipart
- INCORRECT: **NEVER use Form(...) without python-multipart** → Will cause RuntimeError at startup

**Required in `requirements/base.txt`:**
```txt
# Form data support (required for OAuth2 Form(...) parameters)
python-multipart==0.0.6
```

**When This Error Occurs:**
- Using `Form(...)` in any endpoint (especially OAuth2 token endpoints)
- FastAPI detects `Form(...)` parameters at startup
- Raises `RuntimeError` if package is missing
- **Error occurs at startup, not at runtime** - prevents application from starting

**Verification Checklist:**
- CORRECT: `python-multipart==0.0.6` in `requirements/base.txt`
- CORRECT: Application starts without RuntimeError
- CORRECT: OAuth2 token endpoint works correctly

## RULE 5: SQLAlchemy Relationship Eager Loading
### 5.1 Issue: MissingGreenlet Error in Async Context
**Error:** `sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here`

**Root Cause:** Accessing relationship attributes (e.g., `member.user`) triggers lazy loading, which fails in async context

**CRITICAL RULE:**
- CORRECT: **ALWAYS use `selectinload()` for relationships** accessed after query
- INCORRECT: **NEVER access relationships without eager loading** in async code
- CORRECT: **Eager load ALL relationships** that will be accessed

**Required Pattern in `repository.py`:**
```python
from sqlalchemy.orm import selectinload

async def get_by_id(self, member_id: UUID) -> Optional[Member]:
    """Get member by ID"""
    result = await self.session.execute(
        select(Member)
        .options(selectinload(Member.user))  # CRITICAL: Eager load user
        .where(Member.id == member_id, Member.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()

async def list_by_organization(...) -> tuple[list[Member], int]:
    """List members by organization"""
    query = select(Member).options(
        selectinload(Member.user)  # CRITICAL: Eager load user
    ).join(...)
    # ... rest of query
```

**Common Patterns to Fix:**
```python
# INCORRECT: Will cause MissingGreenlet error
member = await repository.get_by_id(member_id)
user_email = member.user.email  # Lazy load fails in async

# CORRECT: Eager load in repository
member = await repository.get_by_id(member_id)  # User already loaded
user_email = member.user.email  # Works because user is eagerly loaded
```

**Verification Checklist:**
- CORRECT: All repository methods that return models with relationships use `selectinload()`
- CORRECT: All relationships accessed in service/router are eagerly loaded
- CORRECT: No lazy loading in async context

## RULE 6: UUID Validation
### 6.1 Issue: UUID Validation Error with Extra Characters
**Error:** `Input should be a valid UUID, invalid character: expected [0-9a-fA-F-], found ')' at 37`

**Root Cause:** UUID contains extra characters (like closing parenthesis `)` or URL-encoded `%29`)

**CRITICAL RULE:**
- CORRECT: **ALWAYS validate UUID format** before using in queries
- CORRECT: **FastAPI automatically validates UUID** when using UUID type

**Required Pattern:**
```python
from uuid import UUID

@router.get("/{organization_id}")
async def get_organization(
    organization_id: UUID,  # FastAPI automatically validates UUID format
    ...
):
    # FastAPI will reject invalid UUIDs before reaching this code
    ...
```

**Verification Checklist:**
- CORRECT: All path parameters use `UUID` type (not `str`)
- CORRECT: FastAPI automatically validates UUID format

## RULE 7: Port Conflicts in Docker
### 7.1 Issue: Port Already Allocated Error
**Error:** `Bind for 0.0.0.0:5433 failed: port is already allocated`

**CRITICAL RULE:**
- CORRECT: **ALWAYS use non-standard host ports** to avoid conflicts
- CORRECT: **PostgreSQL: Use 5433 or 5434 (not 5432)**
- CORRECT: **Redis: Use 6380 (not 6379)**
- CORRECT: **API: Use 8001 (not 8000)** if 8000 is in use

**Required in `docker-compose.yml`:**
```yaml
services:
  db:
    ports:
      - "5433:5432"  # CRITICAL: Non-standard host port
  
  redis:
    ports:
      - "6380:6379"  # CRITICAL: Non-standard host port
  
  api:
    ports:
      - "8001:8000"  # CRITICAL: Non-standard if 8000 in use
```

**Verification Checklist:**
- CORRECT: PostgreSQL uses port 5433 or 5434 (or other non-standard)
- CORRECT: Redis uses port 6380 (or other non-standard)
- CORRECT: No port conflicts with local services
- CORRECT: Container-to-container communication uses standard ports (5432, 6379, 8000)

## RULE 8: Member Invitation User Existence
### 8.1 Issue: Member Not Found Error when Inviting
**Error:** `404 Member not found` when user doesn't exist

**CRITICAL RULE:**
- CORRECT: **User MUST exist before inviting** to organization
- CORRECT: **Check user existence** before creating member
- CORRECT: **Provide clear error message** if user doesn't exist

**Required Pattern:**
```python
async def invite_member(...):
    # Get or create user by email
    user = await self.user_repository.get_by_email(invite_data.user_email)
    if not user:
        # User doesn't exist - raise clear error
        raise UserNotFoundException()  # Or create user first
```

**Verification Checklist:**
- CORRECT: User existence checked before member creation
- CORRECT: Clear error message if user doesn't exist

## RULE 9: Accept Invitation User Verification
### 9.1 Issue: Member Not Found when Wrong User Accepts
**Error:** `404 Member not found` when different user tries to accept invitation

**Root Cause:** Security check - invitation belongs to different user

**CRITICAL RULE:**
- CORRECT: **Verify invitation belongs to logged-in user**
- CORRECT: **Return proper error** if user mismatch
- CORRECT: **Security: Don't reveal member exists** if wrong user

**Required Pattern:**
```python
async def accept_invitation(member_id: UUID, user_id: UUID) -> Member:
    member = await self.get_member_by_id(member_id)
    
    # CRITICAL: Verify the invitation belongs to the user
    if member.user_id != user_id:
        raise MemberNotFoundException()  # Security: Don't reveal member exists
```

**Verification Checklist:**
- CORRECT: User ID verification exists
- CORRECT: Proper error raised on mismatch
- CORRECT: Security maintained (no information leakage)

## RULE 10: Role Values Case Sensitivity
### 10.1 Issue: Validation Error for Role
**Error:** `Input should be 'owner', 'admin', 'member' or 'viewer'` when using uppercase

**CRITICAL RULE:**
- CORRECT: **Role values MUST be lowercase** in API requests
- CORRECT: **Document lowercase requirement** clearly
- CORRECT: **Validate and convert** role values if needed

**Required Values:**
- `"owner"` (not "OWNER" or "Owner")
- `"admin"` (not "ADMIN" or "Admin")
- `"member"` (not "MEMBER" or "Member")
- `"viewer"` (not "VIEWER" or "Viewer")

**Verification Checklist:**
- CORRECT: API documentation specifies lowercase
- CORRECT: Error messages mention lowercase requirement
- CORRECT: Validation accepts only lowercase

## RULE 11: Alembic Config Attribute Name
### 11.1 Issue: AttributeError in Alembic env.py
**Error:** `AttributeError: 'Config' object has no attribute 'config_file_path'. Did you mean: 'config_file_name'?`

**Root Cause:** Alembic's `Config` object uses `config_file_name` (NOT `config_file_path`)

**CRITICAL RULE:**
- CORRECT: **ALWAYS use `config.config_file_name`** in `alembic/env.py`
- INCORRECT: **NEVER use `config.config_file_path`** - attribute doesn't exist

**Required Pattern in `alembic/env.py`:**
```python
from alembic import context

config = context.config

# CORRECT: Use config_file_name
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
```

**WRONG Pattern:**
```python
# INCORRECT: Attribute doesn't exist
if config.config_file_path is not None:
    fileConfig(config.config_file_path)
```

**Impact:**
- Migration service fails to start
- Application cannot start (depends on migration service)
- Database migrations cannot run

**Verification Checklist:**
- CORRECT: `alembic/env.py` uses `config.config_file_name` (NOT `config_file_path`)
- CORRECT: Migration service runs successfully: `docker compose up migrate`
- CORRECT: No `AttributeError` when loading Alembic configuration

## RULE 12: Database Constraint Violation Handling
### 12.1 Issue: Internal Server Error on Constraint Violations
**Error:** `500 Internal Server Error` when database constraints are violated (unique, foreign key, not null, check)

**Root Cause:** Database constraint violations are not caught and converted to user-friendly error messages

**CRITICAL RULE:**
- CORRECT: **MUST implement database exception handlers** for all constraint types
- CORRECT: **MUST convert database errors to user-friendly messages**
- CORRECT: **MUST return appropriate HTTP status codes** (409 for unique, 404 for FK, 422 for validation)
- CORRECT: **MUST extract field names from constraint names** for better error messages

**Required Setup:**
- **Reference:** See `cursor/rules/creation/database_constraint_handling.md` for complete implementation guide

**Key Points:**
- Register handlers for `IntegrityError`, `UniqueViolationError`, `ForeignKeyViolationError`, `NotNullViolationError`, `CheckViolationError`
- Register handlers **BEFORE** catch-all handler in `src/main.py`
- Extract field names from constraint names (e.g., `ix_users_email` → `email`)
- Return `StandardResponse` format with field-level error details

**Verification Checklist:**
- CORRECT: `src/exceptions.py` imports all required database exceptions
- CORRECT: `database_exception_handler` function exists in `src/exceptions.py`
- CORRECT: Database exception handlers registered in `src/main.py` BEFORE catch-all
- CORRECT: Constraint violations return user-friendly errors (not 500 Internal Server Error)

## RULE 13: Schema Duplication Anti-Pattern
### 13.1 Issue: Request Fields Defined in Router Instead of Using Schemas
**Error:** Field definitions duplicated between `router.py` and `schemas.py`, manual schema construction, inconsistent validation

**Root Cause:** Routers use individual `Form()` or `Body()` parameters instead of using Pydantic schemas that already exist

**CRITICAL RULE:**
- CORRECT: **MUST use Pydantic schemas for ALL request bodies** when schemas exist
- CORRECT: **DO NOT** define individual `Form()`/`Body()` parameters that duplicate schema fields
- CORRECT: **DO NOT** manually construct schema objects from individual parameters
- INCORRECT: **NEVER** duplicate field definitions between router and schema

**Required Pattern in `router.py`:**
```python
from src.module.schemas import ResourceCreate, ResourceUpdate

@router.post("")
async def create_resource(
    data: ResourceCreate,  # CORRECT: Use schema directly - FastAPI validates automatically
    session: AsyncSession = Depends(get_session),
):
    service = ResourceService(session)
    result = await service.create_resource(data)
    return StandardResponse(data=result, message="Resource created successfully")
```

**WRONG Pattern (DO NOT DO THIS):**
```python
@router.post("")
async def create_resource(
    name: str = Form(...),  # INCORRECT: Field already defined in ResourceCreate schema
    address: str = Form(...),  # INCORRECT: Duplicating schema field
    city: str = Form(...),  # INCORRECT: Manual parameter definition
    session: AsyncSession = Depends(get_session),
):
    # INCORRECT: Manual schema construction - violates DRY principle
    data = ResourceCreate(name=name, address=address, city=city, ...)
    service = ResourceService(session)
    result = await service.create_resource(data)
```

**Exceptions (when individual parameters are allowed):**
- OAuth2 token endpoints: `username: str = Form(...)`, `password: str = Form(...)` (standard OAuth2 pattern)
- File-only upload endpoints: `file: UploadFile = File(...)` (when file is the only parameter)
- Query parameters: Individual `Query()` parameters are fine (e.g., `page: int = Query(1)`, `search: str = Query(None)`)

**Verification Checklist:**
- CORRECT: All request bodies use Pydantic schemas from `schemas.py`
- CORRECT: No individual `Form()`/`Body()` parameters that duplicate schema fields
- CORRECT: No manual schema construction from individual parameters
- CORRECT: FastAPI automatically validates request bodies using schemas

## RULE 14: API Dependency Pattern Violation
### 14.1 Issue: Direct Service Instantiation in Routers
**CRITICAL VIOLATION:** Routers directly instantiating services instead of using API dependency pattern.

**WRONG Pattern:**
```python
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)  # WRONG: Direct instantiation
    return await service.get_user(user_id)
```

**CORRECT Pattern:**
```python
async def get_user(
    user_id: UUID,
    api: UserApiDep,  # CORRECT: API dependency injection
):
    return await api.get_user(user_id)
```

**Reference:** See `setup.md` RULE 8.6.7 for complete API dependency pattern implementation.

## RULE 15: Repository Layer Separation
### 15.1 Issue: Business Logic in Repository
**Problem:** Business logic, validation, and business rules placed in repository.py instead of service.py, violating layer separation.

**Root Cause:** Unclear understanding of repository's role - repository should only handle database operations.

**CRITICAL RULE:**
- CORRECT: **Repository MUST only contain database operations** (CRUD, queries, filtering)
- CORRECT: **ALL business logic MUST be in service.py** - NOT in repository
- CORRECT: **Repository methods should be pure data access** - no validation, no business rules
- INCORRECT: **NEVER put business logic in repository** - violates separation of concerns

**What Repository SHOULD Contain:**
- Database queries (SELECT, INSERT, UPDATE, DELETE)
- SQLAlchemy operations using AsyncSession
- Eager loading relationships with `selectinload()`
- Filtering, sorting, pagination at database level
- Transaction management (commit, rollback)

**What Repository MUST NOT Contain:**
- Business logic (validation rules, business rules, calculations)
- HTTP concerns (status codes, request/response handling)
- Validation (use schemas and service layer for validation)
- Error messages (use constants.py for messages)
- Configuration (use config.py for settings)

**CORRECT Pattern:**
```python
# CORRECT: Pure database operation
async def get_by_id(self, org_id: UUID) -> Optional[Organization]:
    """Get organization by ID - pure database operation"""
    result = await self.session.execute(
        select(Organization)
        .where(Organization.id == org_id)
    )
    return result.scalar_one_or_none()
```

**WRONG Pattern (DO NOT DO THIS):**
```python
# INCORRECT: Business logic in repository
async def create(self, org: Organization) -> Organization:
    # INCORRECT: Business validation in repository
    if org.status == "inactive":
        raise ValueError("Cannot create inactive organization")  # WRONG: Business logic
    
    # INCORRECT: Business rule in repository
    if await self.count_by_name(org.name) > 0:
        raise ValueError("Organization name must be unique")  # WRONG: Business logic
    
    self.session.add(org)
    await self.session.commit()
    return org
```

**Verification Checklist:**
- CORRECT: Repository methods only contain database operations
- CORRECT: No business logic in repository (validation, business rules)
- CORRECT: No error messages in repository (use constants.py)
- CORRECT: No HTTP concerns in repository
- CORRECT: All business logic moved to service.py

## RULE 16: Constants vs Config Separation
### 16.1 Issue: Confusion Between Constants and Config
**Problem:** Developers mix static constants (constants.py) with environment-based configuration (config.py), leading to incorrect file usage.

**Root Cause:** Unclear distinction between static values and environment-based settings.

**CRITICAL RULE:**
- CORRECT: **constants.py** for static values (error messages, status values, error codes)
- CORRECT: **config.py** for environment-based settings (loaded from .env, feature flags, limits)
- CORRECT: **constants.py** contains string/number literals only (no functions, no computed values)
- CORRECT: **config.py** uses Pydantic BaseSettings (optional file - only if needed)
- INCORRECT: **NEVER put static constants in config.py** - use constants.py
- INCORRECT: **NEVER put environment-based settings in constants.py** - use config.py

**Constants.py SHOULD Contain:**
- Error message strings (e.g., `ERROR_ORGANIZATION_NOT_FOUND = "Organization not found"`)
- Success message strings (e.g., `SUCCESS_ORGANIZATION_CREATED = "Organization created successfully"`)
- Status values (e.g., `STATUS_ACTIVE = "active"`)
- Error codes (e.g., `ERROR_CODE_ORG_NOT_FOUND = "ORGANIZATION_NOT_FOUND"`)
- Enum-like constants (e.g., `ROLE_ADMIN = "admin"`)
- Static string/number literals only

**Constants.py MUST NOT Contain:**
- Functions or logic (use utils.py for functions)
- Computed values (only static literals)
- Database access (use repository.py)
- Environment-based settings (use config.py)

**Config.py SHOULD Contain (Optional File):**
- Environment-based settings (API keys, URLs, timeouts)
- Feature flags (e.g., `ENABLE_LOGO_UPLOAD: bool = True`)
- Configurable limits (e.g., `MAX_LOGO_SIZE_MB: int = 2`)
- Default values that vary by environment
- Settings loaded from `.env` file

**Config.py MUST NOT Contain:**
- Hardcoded secrets (use environment variables)
- Static constants (use constants.py)
- Business logic (use service.py)
- Functions (use utils.py)

**CORRECT Pattern:**
```python
# CORRECT: constants.py - Static values
ERROR_ORGANIZATION_NOT_FOUND = "Organization not found"
STATUS_ACTIVE = "active"
ERROR_CODE_ORG_NOT_FOUND = "ORGANIZATION_NOT_FOUND"

# CORRECT: config.py - Environment-based settings (optional)
class OrganizationSettings(BaseSettings):
    MAX_LOGO_SIZE_MB: int = 2  # Can be overridden via .env
    ENABLE_LOGO_UPLOAD: bool = True  # Feature flag
    DEFAULT_PAGE_SIZE: int = 20  # Configurable default
```

**Decision Tree:**
1. **Is it a static string/number that never changes?** → Use `constants.py`
2. **Does it vary by environment (dev/staging/prod)?** → Use `config.py` (optional file)
3. **Is it a function or computed value?** → Use `utils.py`
4. **Is it a database operation?** → Use `repository.py`
5. **Is it business logic?** → Use `service.py`

**Verification Checklist:**
- CORRECT: Static constants in constants.py (error messages, status values, error codes)
- CORRECT: Environment-based settings in config.py (if config.py exists)
- CORRECT: No functions in constants.py
- CORRECT: No computed values in constants.py
- CORRECT: No static constants in config.py
- CORRECT: Config.py uses Pydantic BaseSettings (if config.py exists)

## RULE 17: ETag Logic Location
### 17.1 Issue: ETag Logic in Router Layer
**Problem:** ETag logic (version validation, conditional request handling, status codes) placed in router layer instead of service layer.

**Root Cause:** Unclear understanding of layer separation - ETag handling is a business logic concern for version control and conflict prevention, not just HTTP protocol.

**CRITICAL RULE:**
- CORRECT: **ETag logic MUST be in service layer** (version validation, conditional requests, conflict detection)
- CORRECT: **Service layer handles ETag validation** - checks If-Match/If-None-Match, generates ETag, validates version conflicts
- INCORRECT: **NEVER put ETag logic in router layer** - violates separation of concerns (business logic belongs in service)

**What ETag Logic Includes:**
- Reading `If-Match` header from request
- Reading `If-None-Match` header from request
- Generating ETag from resource `updated_at` timestamp
- Setting `ETag` header in response
- Setting `Last-Modified` header in response
- Returning `304 Not Modified` status code (for If-None-Match)
- Returning `412 Precondition Failed` status code (for If-Match mismatch)
- Validating ETag matches current resource version

**CORRECT Pattern (ETag in Service):**
```python
# CORRECT: Service handles ETag logic
from fastapi.responses import Response as FastAPIResponse

class ResourceService:
    async def get_resource_by_id(
        self, 
        resource_id: UUID,
        if_none_match: str | None = None,  # CORRECT: Accept header in service
    ) -> ResourceRead | FastAPIResponse:
        """Get resource with ETag support - business logic in service"""
        resource = await self.repository.get_by_id(resource_id)
        if not resource:
            raise ResourceNotFoundException()
        
        # CORRECT: Generate ETag in service (business logic)
        etag = generate_etag(resource.updated_at)
        
        # CORRECT: Check If-None-Match in service (version validation)
        if if_none_match and if_none_match == etag:
            # CORRECT: Return 304 in service (business logic decision)
            return FastAPIResponse(status_code=status.HTTP_304_NOT_MODIFIED)
        
        # CORRECT: Return resource with ETag metadata
        result = ResourceRead.model_validate(resource)
        result._etag = etag  # Attach ETag to result for router to set header
        result._last_modified = resource.updated_at
        return result
    
    async def update_resource(
        self, 
        resource_id: UUID, 
        data: ResourceUpdate,
        if_match: str | None = None,  # CORRECT: Accept header in service
    ) -> ResourceRead:
        """Update resource with ETag validation - business logic in service"""
        current_resource = await self.repository.get_by_id(resource_id)
        if not current_resource:
            raise ResourceNotFoundException()
        
        # CORRECT: Generate ETag in service
        current_etag = generate_etag(current_resource.updated_at)
        
        # CORRECT: Validate If-Match in service (business logic)
        if not if_match:
            raise PreconditionRequiredException("If-Match header required")
        
        if if_match != current_etag:
            # CORRECT: Raise exception in service (business logic validation)
            raise PreconditionFailedException("Resource version mismatch")
        
        # CORRECT: Update resource (business logic)
        updated_resource = await self.repository.update(resource_id, data)
        result = ResourceRead.model_validate(updated_resource)
        result._etag = generate_etag(updated_resource.updated_at)
        return result

# CORRECT: Router delegates ETag logic to service
@router.get("/{resource_id}", response_model=ResourceRead)
async def get_resource(
    resource_id: UUID,
    api: ResourceApiDep,
    if_none_match: str | None = Header(None, alias="If-None-Match"),  # CORRECT: Read header, pass to service
    response: Response = None,  # CORRECT: FastAPI injects Response for setting headers
) -> ResourceRead | FastAPIResponse:
    """Get resource with ETag support"""
    # CORRECT: Pass header to service (service handles ETag logic)
    result = await api.get_resource_by_id(resource_id, if_none_match=if_none_match)
    
    # CORRECT: If service returned 304, return it directly
    if isinstance(result, FastAPIResponse):
        return result
    
    # CORRECT: Set headers from service result (router sets HTTP headers)
    if hasattr(result, '_etag'):
        response.headers["ETag"] = result._etag
        response.headers["Last-Modified"] = format_last_modified(result._last_modified)
    
    return result
```

**WRONG Pattern (ETag in Router - DO NOT DO THIS):**
```python
# INCORRECT: ETag logic in router layer
@router.get("/{resource_id}")
async def get_resource(
    resource_id: UUID,
    api: ResourceApiDep,
    if_none_match: str | None = Header(None, alias="If-None-Match"),  # WRONG: Router handles ETag logic
    response: Response = None,
) -> ResourceRead | FastAPIResponse:
    """Get resource with ETag support"""
    # WRONG: Get resource from service (no ETag logic)
    resource = await api.get_resource_by_id(resource_id)
    
    # WRONG: Generate ETag in router (business logic in router)
    etag = generate_etag(resource.updated_at)
    
    # WRONG: Check If-None-Match in router (business logic in router)
    if if_none_match and if_none_match == etag:
        return FastAPIResponse(status_code=status.HTTP_304_NOT_MODIFIED)
    
    # WRONG: Set headers in router (mixing business logic with HTTP)
    response.headers["ETag"] = etag
    return resource
```

**ETag Generation Helper (CORRECT):**
```python
# CORRECT: ETag utility function (can be in utils.py or service)
from datetime import datetime

def generate_etag(updated_at: datetime) -> str:
    """Generate ETag from updated_at timestamp"""
    return updated_at.strftime("%Y%m%dT%H%M%SZ")

def format_last_modified(updated_at: datetime) -> str:
    """Format datetime for Last-Modified header (RFC 7231 format)"""
    return updated_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
```

**Key Principles:**
- **ETag is business logic concern** - version validation and conflict prevention belong in service layer
- **Service layer handles ETag validation** - checks If-Match/If-None-Match, generates ETag, validates version conflicts
- **Router handles HTTP protocol** - reads headers, passes to service, sets response headers from service result
- **Separation of concerns** - business logic (ETag validation) in service, HTTP protocol (header reading/setting) in router
- **Testability** - service can be tested with ETag logic without HTTP framework dependencies

**Verification Checklist:**
- CORRECT: ETag generation happens in service (not router)
- CORRECT: `If-Match` and `If-None-Match` headers read in router and passed to service
- CORRECT: `ETag` and `Last-Modified` headers set in router from service result (service attaches ETag to result)
- CORRECT: `304 Not Modified` and `412 Precondition Failed` status codes returned from service (not router)
- CORRECT: Service methods accept HTTP headers as parameters for business logic validation
- CORRECT: Service methods can return Response objects with status codes (304, 412) for business logic decisions
- CORRECT: Router reads headers and sets response headers, but delegates ETag validation to service

## RULE 18: Summary Checklist
### 18.1 Pre-Development Checklist
Before declaring any feature complete, verify all rules above. **CRITICAL:** These rules are based on **actual production errors**. **STRICTLY FOLLOW** them to prevent repeating mistakes.

**Quick Reference:**
- **Dependencies:** bcrypt 4.0.1, python-multipart for Form(...) parameters
- **Authentication:** JWT token None check, OAuth2 token endpoint with Form params
- **Database:** Eager load relationships with selectinload, UUID type for path parameters, Alembic config_file_name, constraint violation handling
- **Router:** Use Pydantic schemas (not individual Form()/Body()), API dependency pattern, ETag logic in service layer
- **Repository:** Only database operations, no business logic
- **Constants vs Config:** Static values in constants.py, environment-based in config.py
- **Docker:** Non-standard ports to avoid conflicts

## Related Documentation
- **Database Constraint Handling:** `cursor/rules/creation/database_constraint_handling.md`
- **Router Development Pattern:** `rules/creation/setup.md` - Router section
- **Response and Error Handling:** `rules/creation/response_error_handling.md`

## Summary
This guide provides rule-based instructions for preventing common errors encountered during development. Each rule is numbered and contains specific, actionable requirements based on actual production errors.

**Key Principles:**
- Follow dependency version requirements strictly
- Always check for None values before operations
- Use proper OAuth2 patterns for token endpoints
- Eager load all relationships in async context
- Use Pydantic schemas instead of duplicating field definitions
- Follow router development flow: Router → Request Schema → Service → Response Schema
- Handle database constraint violations with user-friendly errors
- Keep repository layer pure (only database operations, no business logic)
- Separate constants (static values) from config (environment-based settings)
- Keep ETag logic in service layer (business logic - version validation, conflict prevention), router only reads/sets headers

**Critical Reminders:**
- bcrypt 4.0.1 (NOT 5.0.0) for passlib compatibility
- python-multipart required for Form(...) parameters
- Always eager load relationships with selectinload
- Use UUID type for path parameters (not str)
- Use config_file_name (NOT config_file_path) in Alembic
