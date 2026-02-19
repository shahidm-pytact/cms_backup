# Universal Validation Guide - Complete Standalone Reference

**Purpose:** COMPLETE, STANDALONE validation guide replacing ALL 12 source files. Use this file independently - the 12 source files are NOT required.

**Merges:** `setup.md`, `config_validate.md`, `dependencies_validate.md`, `docker_validate.md`, `module_architecture_validate.md`, `project_structure_validate.md`, `response_error_handling.md`, `error_prevention.md`, `development_build.md`, `auth_setup.md`, `database_constraint_handling.md`, `database_setup.md`.

**Usage:** Execute 12 phases systematically, fix all issues, re-verify - using ONLY this file.

---

## RULE 1: Critical Development Rules

### 1.1 Before ANY Development

**CRITICAL RULE:** MANDATORY steps before ANY development.

**RULE 1.1.1: Required Steps**
1. CORRECT Ask User for ALL Required Info: Module/model names, database credentials, API settings, environment config - USER PROVIDES ALL
2. CORRECT Module Development: Example names (organizations, members) are STRUCTURAL PATTERNS ONLY - NEVER build unless user requests. USER PROVIDES actual names - use those.
3. CORRECT Auth Module - MANDATORY BY DEFAULT: Include `src/user/` or `src/auth/` in EVERY project. ONLY skip if user explicitly says: "no auth", "skip auth", "without auth", "don't need auth". Include: User model, JWT tokens, OAuth2PasswordBearer, `/token` endpoint, password hashing.
4. CORRECT Optional Components: Redis/Celery - ONLY if user explicitly requests. If Celery requested but Redis not set up → ask user.
5. CORRECT FastAPI Best Practices: Follow https://github.com/zhanymkanov/fastapi-best-practices. Use `src/` root, async all the way, domain layering: models → schemas → repository → service → router.
6. CORRECT Workflow Order: Structure → Auth → Models → ONE migration → Requirements → Docker → Verification.

**RULE 1.1.2: Development Rules**
- CORRECT Always ask user for required information before proceeding
- CORRECT Use user-provided names (not example names)
- CORRECT Include auth module by default (unless user explicitly skips)
- CORRECT Only add optional components if user explicitly requests
- INCORRECT Proceed without user-provided information
- INCORRECT Use example names without user confirmation

---

## RULE 2: Quick Reference - Critical Patterns

### 2.1 Pattern Reference Table

**RULE 2.1.1: Critical Pattern Table**

| Pattern | Wrong | Correct | Error |
|---------|-------|---------|-------|
| **BaseSettings Field()** | `debug: bool = Field(default=True)` | `debug: bool = True` | RecursionError |
| **Generic Field()** | `items: List[T] = Field(...)` | `items: List[T]  # No Field()` | RecursionError |
| **Decimal Field()** | `hours: Decimal = Field(gt=0)` | `Annotated[Decimal, Field(gt=0)]` | RecursionError |
| **Primary Key** | `id: Mapped[int] = mapped_column(...)` | `id: Mapped[UUID] = mapped_column(..., default=uuid4)` | Type mismatch |
| **Timestamps** | `created_at: Mapped[datetime] = mapped_column(default_factory=datetime.utcnow)` | `created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())` | Doesn't work |
| **Enums in DB** | `status: Mapped[UserStatus] = mapped_column(Enum(UserStatus))` | `status: Mapped[UserStatus] = mapped_column(String(50), default=UserStatus.ACTIVE.value)` | KeyError |
| **Enum Comparison** | `.where(Member.role == MemberRole.OWNER)` | `.where(Member.role == MemberRole.OWNER.value)` | Type mismatch |
| **Route Order** | `GET "/{id}"` before `GET "/summary"` | `GET "/summary"` before `GET "/{id}"` | 422 error |
| **Query Params (dict)** | `filter_params: Optional[dict] = Query(None)` | `filter_params: Optional[str] = Query(None)` then `json.loads()` | AssertionError |
| **Alembic Config** | `config.config_file_path` | `config.config_file_name` | AttributeError |

### 2.2 Import-to-Package Mapping

**RULE 2.2.1: Import Mapping Table**

| Import | Required Package | Critical |
|--------|-----------------|----------|
| `EmailStr` from `pydantic` | `email-validator` | CORRECT |
| `BaseSettings` from `pydantic_settings` | `pydantic-settings` | CORRECT |
| `Form(...)` from `fastapi` | `python-multipart` | CORRECT |
| `redis.asyncio` | `redis` | CORRECT |
| `passlib.context` | `passlib[bcrypt]` + `bcrypt==4.0.1` | CORRECT CRITICAL |
| `jose` or `jwt` from `jose` | `python-jose[cryptography]` | CORRECT |
| `sqlalchemy.ext.asyncio` | `sqlalchemy[asyncio]` + `asyncpg` | CORRECT |

**RULE 2.2.2: Import Mapping Rules**
- CORRECT Map every import to required package
- CORRECT Verify package is in requirements/base.txt
- CORRECT Check special cases (EmailStr, BaseSettings, Form, etc.)
- INCORRECT Assume package is obvious from import name

### 2.3 Response Format

**RULE 2.3.1: Success Response Format**
- CORRECT Success: `{"data": {...}, "message": "..."}` - Order: `data`, `message`

**RULE 2.3.2: Error Response Format**
- CORRECT Error: `{"error": {"code": "...", "details": [...]}, "message": "..."}` - Order: `error`, `message` (error has NO message field)

**RULE 2.3.3: Response Format Rules**
- CORRECT Field order is CRITICAL: `data`/`error`, `message`
- CORRECT Error object has NO message field (only `code` and `details`)
- CORRECT Message is at root level only
- INCORRECT Wrong field order causes validation errors

### 2.4 Critical Implementation Patterns

**RULE 2.4.1: FK Validation Pattern (CRITICAL)**
```python
async def create_record(self, fk_id: UUID, data: CreateSchema):
    fk_entity = await self.session.get(ForeignEntity, fk_id)
    if not fk_entity or (hasattr(fk_entity, 'deleted_at') and fk_entity.deleted_at):
        raise NotFoundError("ForeignEntity", str(fk_id))
    record = Entity(fk_id=fk_id, ...)
    self.session.add(record)
    await self.session.commit()
    await self.session.refresh(record)
    return record
```

**RULE 2.4.2: selectinload Pattern (CRITICAL)**
```python
from sqlalchemy.orm import selectinload
result = await self.session.execute(select(User).options(selectinload(User.addresses)).where(...))
user = result.scalar_one()
addresses = user.addresses  # CORRECT Works (no MissingGreenlet error)
```

**RULE 2.4.3: Ambiguous Relationships Pattern (CRITICAL)**
```python
class User(Base):
    addresses: Mapped[list["Address"]] = relationship("Address", back_populates="user", primaryjoin="User.user_id == Address.user_id")
class Address(Base):
    user: Mapped["User"] = relationship("User", back_populates="addresses", foreign_keys=[user_id])
```

**RULE 2.4.4: Token Endpoint Pattern (CRITICAL)**
```python
@router.post("/token", status_code=status.HTTP_200_OK)
async def token(username: str = Form(...), password: str = Form(...)):
    try:
        user = await service.authenticate_user(username, password)
        return {"access_token": "...", "token_type": "bearer"}
    except (InvalidCredentialsException, InactiveUserException):
        raise HTTPException(status_code=401, detail="Invalid username or password", headers={"WWW-Authenticate": "Bearer"})
```

**RULE 2.4.5: get_current_user Pattern (CRITICAL)**
```python
async def get_current_user(token: Optional[str] = Depends(oauth2_scheme), ...):
    if not token:  # CORRECT CRITICAL: Check None
        raise UnauthenticatedError("Could not validate credentials")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user = await session.get(User, UUID(payload.get("sub")))
    if not user or UserStatus(user.status) != UserStatus.ACTIVE:
        raise InactiveUserError()
    return user
```

---

## RULE 3: Validation Workflow Overview

### 3.1 Workflow Phases

**CRITICAL RULE:** Execute ALL phases systematically. For each phase: Explain → Execute checks → Fix issues → Re-verify → Next phase.

**RULE 3.1.1: Phase Reference Table**

| Phase | Focus | Key Checks |
|-------|-------|------------|
| 1 | **Structure** | Root files, core files, domain modules, infra (if requested), file existence |
| 2 | **Configuration** | BaseSettings import, pydantic-settings package, NO Field(), model_config |
| 3 | **Dependencies** | All packages with versions, bcrypt==4.0.1, import-to-package mapping, complete audit |
| 4 | **Docker** | No version field, non-standard ports, migrate service, dependencies, DATABASE_URL |
| 5 | **Models** | UUID PKs, timestamps (server_default), enums (String), ambiguous relationships |
| 6 | **Schemas** | UUID IDs, optional updated_at, pagination (page_size, total_pages), NO Field() in Generic |
| 7 | **Repositories** | selectinload(), explicit JOIN ON, no business logic, async |
| 8 | **Services** | FK validation, enum .value, domain exceptions, transaction pattern |
| 9 | **Routers** | StandardResponse[T], route order, UUID params, no business logic, JSON strings for complex query params |
| 10 | **Exceptions** | Base exceptions, global handlers, error format, UnauthenticatedError |
| 11 | **Auth** | OAuth2PasswordBearer, Form data, token None check, JWT standards |
| 12 | **Runtime** | App starts, no ImportError, no mapper errors, all patterns verified |

**RULE 3.1.2: Workflow Rules**
- CORRECT Execute ALL phases systematically
- CORRECT For each phase: Explain → Execute checks → Fix issues → Re-verify → Next phase
- CORRECT Do not skip phases
- CORRECT Fix all issues before moving to next phase
- INCORRECT Skip phases or move forward with unfixed issues

---

## RULE 4: Phase 1 - Project Structure

### 4.1 Structure Checks

**RULE 4.1.1: CHECK 1.1 - Root Files**
- CORRECT Root files: `.env`, `.gitignore`, `logging.ini`, `alembic.ini`, `Dockerfile`, `docker-compose.yml`
- CORRECT Action: Create missing (ask before overwriting)
- CORRECT Check existence before creating

**RULE 4.1.2: CHECK 1.2 - Core Files**
- CORRECT Core files: `src/__init__.py`, `src/config.py`, `src/database.py`, `src/main.py`, `src/exceptions.py`, `src/schemas.py`, `src/api/__init__.py`, `src/api/router.py`
- CORRECT Action: Create missing
- CORRECT Verify all core files exist

**RULE 4.1.3: CHECK 1.3 - Domain Modules**
- CORRECT Each `src/<module>/` MUST have: `__init__.py`, `models.py`, `schemas.py`, `repository.py`, `service.py`, `router.py`, `dependencies.py`, `constants.py`, `exceptions.py`, `utils.py`
- CORRECT Action: Create missing
- CORRECT Use user-provided module names

**RULE 4.1.4: CHECK 1.4 - Infra Files (ONLY if requested)**
- CORRECT `src/infra/cache_redis.py` (Redis) - ONLY if explicitly requested
- CORRECT `src/infra/celery_app.py` (Celery) - ONLY if explicitly requested
- CORRECT Action: Create ONLY if explicitly requested
- INCORRECT Add infra files without user request

**RULE 4.1.5: CHECK 1.5 - File Existence Check (CRITICAL)**
- CORRECT CRITICAL - Always check if file exists before creating
- CORRECT Action: List existing files, ask user before overwriting
- CORRECT Report to user what exists and what will be created
- INCORRECT Create files without checking existence

---

## RULE 5: Phase 2 - Configuration

### 5.1 Configuration Checks

**RULE 5.1.1: CHECK 2.1 - Import Source**
- CORRECT Import is `from pydantic_settings import BaseSettings` (NOT `from pydantic`)
- CORRECT Action: Fix import if incorrect
- INCORRECT Import from `pydantic` causes ImportError

**RULE 5.1.2: CHECK 2.2 - Package Requirement**
- CORRECT `pydantic-settings==2.1.0` in `requirements/base.txt`
- CORRECT Action: Add if missing
- INCORRECT Missing package causes ImportError

**RULE 5.1.3: CHECK 2.3 - Field() in BaseSettings (CRITICAL)**
- CORRECT No `Field()` in BaseSettings → Causes `RecursionError`
- CORRECT Search: `Field(` in `Settings` class
- CORRECT Action: Remove all `Field()`, use direct assignment
- INCORRECT Using `Field()` in BaseSettings causes RecursionError

**RULE 5.1.4: CHECK 2.4 - Required Pattern**
```python
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:password@db:5432/dbname"
    api_title: str = "API Title"  # Ask user
    api_version: str = "1.0.0"  # Ask user
    api_prefix: str = "/v1"  # Ask user
    environment: str = "local"  # Ask user
    debug: bool = True  # CORRECT NO Field()
    SECRET_KEY: str = "super-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    model_config = {"env_file": ".env", "case_sensitive": False}
settings = Settings()  # Singleton
```
- CORRECT Action: Fix missing fields, ensure `model_config`, ensure singleton `settings`

---

## RULE 6: Phase 3 - Dependencies

### 6.1 Dependency Checks

**RULE 6.1.1: CHECK 3.1 - Required Packages**
- CORRECT Required packages: `fastapi==0.109.0`, `uvicorn[standard]==0.27.0`, `sqlalchemy[asyncio]==2.0.25`, `asyncpg==0.29.0`, `alembic==1.13.1`, `pydantic==2.5.3`, `pydantic-settings==2.1.0`, `email-validator==2.1.0`, `passlib[bcrypt]==1.7.4`, `bcrypt==4.0.1` (CRITICAL: NOT 5.0.0), `python-jose[cryptography]==3.3.0`, `python-multipart==0.0.6`
- CORRECT Action: Add missing, fix versions
- CORRECT Pin all package versions

**RULE 6.1.2: CHECK 3.2 - Import to Package Mapping**
- CORRECT Import → Package mapping (see Quick Reference table)
- CORRECT CRITICAL: OAuth2 token endpoints use `Form()` → requires `python-multipart`
- CORRECT Action: Add missing packages
- CORRECT Verify all imports have corresponding packages

**RULE 6.1.3: CHECK 3.3 - Complete Dependency Audit (CRITICAL)**
- CORRECT MANDATORY - Complete dependency audit: `grep -r "import\|from" src/`
- CORRECT Map each import to required package
- CORRECT Verify EVERY package is in `requirements/base.txt`
- CORRECT Action: Complete audit before declaring "ready"
- INCORRECT Missing dependencies = BLOCKER

---

## RULE 7: Phase 4 - Docker & Docker Compose

### 7.1 Docker Checks

**RULE 7.1.1: CHECK 4.1 - Version Field**
- CORRECT No `version:` field in `docker-compose.yml` (obsolete in v2+)
- CORRECT Action: Remove if present
- INCORRECT Including version field generates warnings

**RULE 7.1.2: CHECK 4.2 - Port Mapping**
- CORRECT Non-standard host ports: PostgreSQL `"5434:5432"`, Redis `"6380:6379"`, API `"8001:8000"` if 8000 in use
- CORRECT Action: Change if conflicts
- CORRECT Use non-standard ports to avoid conflicts

**RULE 7.1.3: CHECK 4.3 - Migrate Service**
- CORRECT `migrate` service exists with `restart: "no"`:
```yaml
migrate:
  build: .
  command: alembic upgrade head
  environment:
    DATABASE_URL: postgresql+asyncpg://postgres:1112@db:5432/test
  depends_on:
    db:
      condition: service_healthy
  restart: "no"
```
- CORRECT Action: Add if missing, fix if incorrect

**RULE 7.1.4: CHECK 4.4 - Service Dependencies**
- CORRECT `api` depends on `migrate` with `condition: service_completed_successfully`
- CORRECT `api` depends on `db` with `condition: service_healthy`
- CORRECT `migrate` depends on `db` with `condition: service_healthy`
- CORRECT Action: Fix dependencies

**RULE 7.1.5: CHECK 4.5 - DATABASE_URL Consistency**
- CORRECT `DATABASE_URL` in `migrate`/`api` matches `POSTGRES_PASSWORD`/`POSTGRES_USER`/`POSTGRES_DB` in `db` service
- CORRECT Action: Fix mismatches
- CORRECT Use same values provided by user

**RULE 7.1.6: CHECK 4.6 - Health Checks**
- CORRECT Health checks configured: `db` service has health check, `redis` service has health check (if Redis exists)
- CORRECT Action: Add health checks if missing

**RULE 7.1.7: CHECK 4.7 - Dockerfile**
- CORRECT Dockerfile exists: `FROM python:3.11-slim`, installs system dependencies, copies requirements, installs packages, copies code, exposes port 8000
- CORRECT Action: Verify Dockerfile structure

---

## RULE 8: Phase 5 - Domain Models

### 8.1 Model Checks

**RULE 8.1.1: CHECK 5.1 - Primary Keys**
- CORRECT Primary keys use UUID (NOT `int`)
- CORRECT Search: `primary_key=True` with `int` type
- CORRECT Action: Fix all `int` PKs to `UUID`

**RULE 8.1.2: CHECK 5.2 - Timestamps**
- CORRECT Timestamps use `server_default=func.now()` (NOT `default_factory=datetime.utcnow`)
- CORRECT Search: `default_factory=datetime.utcnow`
- CORRECT Action: Fix all timestamps

**RULE 8.1.3: CHECK 5.3 - Enums (CRITICAL)**
- CORRECT Enums stored as strings (NOT SQLAlchemy `Enum()`)
- CORRECT Search: `Enum(` or `SQLEnum(` in models
- CORRECT Action: Replace all `Enum()` with `String(n)`, use `.value` for defaults
- INCORRECT Using SQLAlchemy Enum() causes KeyError

**RULE 8.1.4: CHECK 5.4 - Ambiguous Relationships (CRITICAL)**
- CORRECT Ambiguous relationships fixed
- CORRECT For each model: Multiple FKs to same parent? Reverse relationship specifies `primaryjoin` or `foreign_keys`?
- CORRECT Action: Fix all ambiguous relationships

**RULE 8.1.5: CHECK 5.5 - Model Best Practices**
- CORRECT Indexes on frequently queried fields
- CORRECT Proper nullable constraints
- CORRECT `__repr__` method
- CORRECT Action: Add indexes, add `__repr__` methods

**RULE 8.1.6: CHECK 5.6 - Foreign Keys**
- CORRECT Foreign keys use UUID type and proper constraints
- CORRECT `ondelete="CASCADE"` for dependent records
- CORRECT `ondelete="SET NULL"` for optional FKs
- CORRECT `index=True` on FK columns
- CORRECT Action: Add proper FK constraints

**RULE 8.1.7: CHECK 5.7 - Model Imports**
- CORRECT All models import from correct base (`from src.database import Base`)
- CORRECT Use correct types (`Mapped`, `mapped_column`)
- CORRECT Import UUID correctly
- CORRECT Action: Verify all model imports are correct

---

## RULE 9: Phase 6 - Schemas

### 9.1 Schema Checks

**RULE 9.1.1: CHECK 6.1 - ID Types**
- CORRECT All IDs are `UUID` (NOT `int`)
- CORRECT Action: Fix all `int` IDs to `UUID`

**RULE 9.1.2: CHECK 6.2 - Updated At Field**
- CORRECT `updated_at` is `Optional[datetime] = None` (NOT required)
- CORRECT Action: Fix all `updated_at` to optional

**RULE 9.1.3: CHECK 6.3 - Enum Fields**
- CORRECT Enum fields are strings (matching DB values)
- CORRECT Action: Ensure enum fields are `str` type

**RULE 9.1.4: CHECK 6.4 - Pagination Fields**
- CORRECT Pagination uses `page_size`, `total_pages` (NOT `size`, `pages`)
- CORRECT Search: `size=` or `pages=` in `PaginatedResponse`
- CORRECT Action: Fix all pagination field names

**RULE 9.1.5: CHECK 6.5 - Generic Models**
- CORRECT No `Field()` in Generic models (causes `RecursionError`)
- CORRECT Search: `Field(` in Generic model definitions
- CORRECT Action: Remove `Field()` from Generic models

**RULE 9.1.6: CHECK 6.6 - Decimal Fields**
- CORRECT Decimal fields use `Annotated[Decimal, Field(...)]` (NOT direct `Field()`)
- CORRECT Search: `Decimal = Field(gt=0, ...)`
- CORRECT Action: Fix Decimal fields to use `Annotated`

**RULE 9.1.7: CHECK 6.7 - Schema Validation**
- CORRECT Use `EmailStr` for emails
- CORRECT Use `Field()` for constraints
- CORRECT Custom validators for complex rules
- CORRECT Action: Use `EmailStr` for all email fields

**RULE 9.1.8: CHECK 6.8 - Password Validation**
- CORRECT Minimum 8 chars
- CORRECT Require uppercase, lowercase, digit
- CORRECT Action: Add password validators to all password fields

**RULE 9.1.9: CHECK 6.9 - Schema Imports**
- CORRECT All schemas use `from pydantic import BaseModel, EmailStr, Field, field_validator`
- CORRECT Use `ConfigDict(from_attributes=True)` for response models
- CORRECT Action: Verify schema imports are correct

**RULE 9.1.10: CHECK 6.10 - Schema Naming**
- CORRECT Create schemas use `*Create`
- CORRECT Update schemas use `*Update`
- CORRECT Response schemas use `*Response`
- CORRECT Action: Verify schema naming conventions

---

## RULE 10: Phase 7 - Repositories

### 10.1 Repository Checks

**RULE 10.1.1: CHECK 7.1 - selectinload (CRITICAL)**
- CORRECT Relationships use `selectinload()` to prevent `MissingGreenlet`
- CORRECT Search: Relationship access without `selectinload()`
- CORRECT Action: Add `selectinload()` for all relationships accessed after query

**RULE 10.1.2: CHECK 7.2 - JOIN ON Clauses**
- CORRECT Explicit JOIN ON clauses to prevent `InvalidRequestError`
- CORRECT Search: `.join(Model)` without explicit ON
- CORRECT Action: Add explicit ON clauses to all joins

**RULE 10.1.3: CHECK 7.3 - No Business Logic**
- CORRECT No business logic (only DB operations)
- CORRECT Search: Business logic in repositories (validations, calculations, business rules)
- CORRECT Action: Move business logic to services if found

**RULE 10.1.4: CHECK 7.4 - Async Methods**
- CORRECT Repository methods are async: All methods use `async def`, use `await` for session operations
- CORRECT Action: Convert to async if needed

**RULE 10.1.5: CHECK 7.5 - Error Handling**
- CORRECT Repository error handling: Return `None` or raise exceptions (NOT return error responses)
- CORRECT Action: Ensure repositories don't return error responses

---

## RULE 11: Phase 8 - Services

### 11.1 Service Checks

**RULE 11.1.1: CHECK 8.1 - FK Validation (CRITICAL)**
- CORRECT Foreign key validation before insert/update to prevent `ForeignKeyViolationError`
- CORRECT For each method that creates/updates with FKs: Verify FK existence checked, soft delete checked (if applicable), clear exceptions raised
- CORRECT Action: Add FK validation to all create/update methods

**RULE 11.1.2: CHECK 8.2 - Enum Comparisons**
- CORRECT Enum comparisons use `.value` in SQLAlchemy queries
- CORRECT Search: Enum objects used directly in queries
- CORRECT Action: Fix all enum comparisons to use `.value`

**RULE 11.1.3: CHECK 8.3 - Service Separation**
- CORRECT Service separation: All business logic, no HTTP details, transaction management (commit + refresh)
- CORRECT Search: `HTTPException`, `status.HTTP_*` in services
- CORRECT Action: Remove HTTP details from services, use domain exceptions

**RULE 11.1.4: CHECK 8.4 - Transaction Pattern**
- CORRECT Transaction pattern: Always commit and refresh after create/update
- CORRECT Action: Add commit + refresh to all create/update methods

**RULE 11.1.5: CHECK 8.5 - Async Methods**
- CORRECT Service methods are async: All methods use `async def`, use `await` for async operations
- CORRECT Action: Convert to async if needed

**RULE 11.1.6: CHECK 8.6 - Error Handling**
- CORRECT Service error handling: Services raise exceptions (NOT return error responses or HTTPException)
- CORRECT Action: Replace with domain exceptions

---

## RULE 12: Phase 9 - Routers

### 12.1 Router Checks

**RULE 12.1.1: CHECK 9.1 - StandardResponse**
- CORRECT All responses use `StandardResponse[T]` with correct field order
- CORRECT Search: Endpoints without `response_model=StandardResponse[T]`
- CORRECT Action: Wrap all responses in `StandardResponse[T]` with correct field order (data, message)

**RULE 12.1.2: CHECK 9.2 - Route Order (CRITICAL)**
- CORRECT Route order: `POST` → `GET ""` → `GET "/specific-path"` → `GET "/{id}"` → `PATCH "/{id}"` → `DELETE "/{id}"`
- CORRECT Specific routes BEFORE parameterized to prevent 422 errors
- CORRECT Action: Reorder routes if incorrect

**RULE 12.1.3: CHECK 9.3 - Path Parameters**
- CORRECT Path params use `UUID` (NOT `str`)
- CORRECT FastAPI automatically validates UUID format
- CORRECT Action: Fix all path param IDs to `UUID` type

**RULE 12.1.4: CHECK 9.4 - Error Handling**
- CORRECT No manual error handling (let exceptions bubble to global handlers)
- CORRECT Action: Remove try-catch, let exceptions propagate

**RULE 12.1.5: CHECK 9.5 - Router Separation (CRITICAL)**
- CORRECT Router separation: No business logic, no DB queries, no password hashing, no token creation
- CORRECT Search: `db.query(`, `get_password_hash(`, `create_access_token(` in routers
- CORRECT Action: Move all business logic, DB queries, password hashing, token creation to services

**RULE 12.1.6: CHECK 9.6 - HTTP Methods and Status Codes**
- CORRECT HTTP methods and status codes: `POST` → 201 Created, `GET` → 200 OK, `PUT/PATCH` → 200 OK, `DELETE` → 200 OK (NOT 204 - FastAPI doesn't allow response body with 204)
- CORRECT Action: Fix status codes

**RULE 12.1.7: CHECK 9.7 - Router Imports**
- CORRECT Router imports: Routers import from correct modules
- CORRECT Action: Verify router imports are correct

**RULE 12.1.8: CHECK 9.8 - Dependency Injection**
- CORRECT Router dependency injection: Routers MUST use API dependency class pattern (e.g., `ResourceApiDep`) instead of direct service instantiation
- CORRECT Search: `service = ResourceService(session)` or direct service instantiation in routers
- CORRECT Action: Use API dependency class pattern (e.g., `api: ResourceApiDep` injected via `Depends()`)
- CORRECT Exception: If API dependency pattern is not used, verify `Depends(get_session)` is used for database session and `Depends(get_current_user)` for authentication

**RULE 12.1.9: CHECK 9.9 - Response Models**
- CORRECT Router response models: ALL endpoints specify `response_model` in decorator (e.g., `response_model=ResourceRead` or `response_model=StandardResponse[ResourceRead]`)
- CORRECT Action: Add correct response models to all endpoints

**RULE 12.1.10: CHECK 9.10 - Query Parameters with Complex Types (CRITICAL)**
- CORRECT Query parameters with complex types (dict/object) must be JSON strings
- CORRECT FastAPI cannot parse `dict` from query parameters → `AssertionError: can only be a request body`
- CORRECT Search: `Query(None)` with `dict`/`object` type
- CORRECT Action: Convert all complex query params to JSON strings and parse manually

**RULE 12.1.11: CHECK 9.11 - Request Body Schema Usage (CRITICAL)**
- CORRECT Request body schema usage: Routers MUST use Pydantic schemas for request bodies, NOT individual `Form()`/`Body()` parameters when schemas exist
- CORRECT Search: `Form(...)` or `Body(...)` with individual fields that match schema fields
- CORRECT Pattern to find: Multiple `Form()` parameters followed by manual schema construction like `Schema(field1=param1, field2=param2, ...)`
- CORRECT Action: Replace individual parameters with schema objects (e.g., `data: ResourceCreate` instead of `name: str = Form(...), address: str = Form(...)`)
- CORRECT Exceptions: OAuth2 token endpoints (`username: str = Form(...)`, `password: str = Form(...)`) and file-only upload endpoints are allowed
- CORRECT Rationale: Prevents schema duplication, ensures centralized validation, maintains DRY principle

**RULE 12.1.12: CHECK 9.12 - Query Parameter Schema Usage (CRITICAL)**
- CORRECT Query parameter schema usage: Routers MUST use query schemas with `Depends()` pattern when query schema exists, NOT individual `Query()` parameters
- CORRECT Search: Multiple `Query()` parameters when query schema exists (e.g., `page: int = Query(1)`, `page_size: int = Query(20)`, `search: str = Query(None)`)
- CORRECT Pattern to find: Individual `Query()` parameters that match fields in query schema
- CORRECT Action: Replace individual `Query()` parameters with query schema using `Depends()` (e.g., `query: ResourceListQuery = Depends(ResourceListQuery)`)
- CORRECT Exception: Simple single query parameters can use `Query()` directly (e.g., `id: UUID = Query(...)`)
- CORRECT Rationale: Centralizes query parameter validation, prevents duplication, maintains DRY principle

**RULE 12.1.13: CHECK 9.13 - Router Structure**
- CORRECT Router structure: Router MUST have `APIRouter` with `prefix` and `tags`, logger instance at module level, and comprehensive endpoint documentation (summary, description, operation_id)
- CORRECT Search: Routers without `prefix`/`tags`, missing logger, or endpoints without documentation
- CORRECT Action: Add router structure (prefix, tags), logger instance, and comprehensive endpoint documentation

---

## RULE 13: Phase 10 - Exceptions & Error Handling

### 13.1 Exception Checks

**RULE 13.1.1: CHECK 10.1 - Domain Exceptions**
- CORRECT Domain exceptions extend base exceptions (NOT `HTTPException`)
- CORRECT Search: `class X(HTTPException):` in domain exception files
- CORRECT Action: Fix all domain exceptions to extend base exceptions

**RULE 13.1.2: CHECK 10.2 - UnauthenticatedError**
- CORRECT Use `UnauthenticatedError` (NOT `UnauthorizedError`)
- CORRECT Action: Replace with `UnauthenticatedError`

**RULE 13.1.3: CHECK 10.3 - Global Handlers**
- CORRECT Global handlers registered in `src/main.py` in correct order (most specific first): `AppException` → `RequestValidationError` → `HTTPException` → `Exception` (catch-all last)
- CORRECT Action: Add missing handlers, fix order

**RULE 13.1.4: CHECK 10.4 - Error Response Format**
- CORRECT Error response format: `{"error": {"code": "...", "details": [...]}, "message": "..."}`
- CORRECT `error` object has NO `message` (only `code` and `details`)
- CORRECT `message` is at root level only
- CORRECT Field order is CRITICAL: `error`, `message` (in this exact order)
- CORRECT Action: Fix error response structure if incorrect

**RULE 13.1.5: CHECK 10.5 - Success Messages**
- CORRECT Success message standards: Use consistent messages - `"{Resource} created successfully"`, `"{Resource} retrieved successfully"`, `"{Resource} updated successfully"`, `"{Resource} deleted successfully"`
- CORRECT Action: Use consistent success message format

**RULE 13.1.6: CHECK 10.6 - Handler Order**
- CORRECT Exception handler order: Handlers registered in correct order (most specific first)
- CORRECT Action: Verify handler registration order in `src/main.py`

**RULE 13.1.7: CHECK 10.7 - Exception Base Classes**
- CORRECT Exception base classes: All domain exceptions extend base exceptions from `src.exceptions` (NOT `HTTPException` directly)
- CORRECT Action: Fix all exceptions to extend base classes

---

## RULE 14: Phase 11 - Authentication & Security

### 14.1 Auth Checks

**RULE 14.1.1: CHECK 11.1 - OAuth2PasswordBearer**
- CORRECT `OAuth2PasswordBearer(tokenUrl="/v1/users/token", auto_error=False)`
- CORRECT Action: Fix if incorrect

**RULE 14.1.2: CHECK 11.2 - Token Endpoint Form Data**
- CORRECT Token endpoint accepts Form data: `username: str = Form(...)`, `password: str = Form(...)`
- CORRECT CRITICAL: Requires `python-multipart==0.0.6` in `requirements/base.txt` - Without it, FastAPI raises `RuntimeError: Form data requires "python-multipart" to be installed` at startup
- CORRECT Action: Fix if using JSON, ensure python-multipart is in requirements

**RULE 14.1.3: CHECK 11.3 - Token Endpoint Response**
- CORRECT Token endpoint returns: `{"access_token": "...", "token_type": "bearer"}`
- CORRECT Action: Fix response format

**RULE 14.1.4: CHECK 11.4 - Token Endpoint Error Handling (CRITICAL)**
- CORRECT Token endpoint error handling: Must catch authentication exceptions and return OAuth2-compatible error format with `HTTPException`, proper status code (401), and `WWW-Authenticate` header
- CORRECT Action: Add OAuth2-compatible error handling to token endpoint

**RULE 14.1.5: CHECK 11.5 - Token None Check (CRITICAL)**
- CORRECT `get_current_user` has token None check before decoding to prevent `AttributeError`
- CORRECT Search: `jwt.decode(token, ...)` without `if not token:` check
- CORRECT Action: Add token None check before decoding

**RULE 14.1.6: CHECK 11.6 - User Status Comparison**
- CORRECT User status comparison: Convert string from DB to enum
- CORRECT Action: Fix status comparisons

**RULE 14.1.7: CHECK 11.7 - Password Security**
- CORRECT Password security: Use bcrypt (NOT MD5/SHA), minimum 8 chars, require uppercase/lowercase/digit, never log passwords
- CORRECT Action: Use bcrypt for all password hashing

**RULE 14.1.8: CHECK 11.8 - JWT Standards**
- CORRECT JWT standards: Separate access (30 min) and refresh (7 days) tokens, include token type in payload, verify token type on decode
- CORRECT Action: Implement separate access/refresh tokens with type verification

**RULE 14.1.9: CHECK 11.9 - OAuth2PasswordBearer for Swagger UI**
- CORRECT OAuth2PasswordBearer required for Swagger UI "Authorize" button
- CORRECT Search: `HTTPBearer` or manual header extraction
- CORRECT Action: Use `OAuth2PasswordBearer` (NOT `HTTPBearer`)

---

## RULE 15: Phase 12 - Error Prevention (Critical Runtime Issues)

### 15.1 Error Prevention Checks

**RULE 15.1.1: CHECK 12.1 - bcrypt Version**
- CORRECT `bcrypt==4.0.1` in `requirements/base.txt` (NOT 5.0.0 - incompatible with `passlib[bcrypt]==1.7.4`)
- CORRECT Action: Pin to 4.0.1

**RULE 15.1.2: CHECK 12.2 - JWT Token None Check**
- CORRECT JWT token None check in all `get_current_user` functions
- CORRECT Action: Add check if missing

**RULE 15.1.3: CHECK 12.3 - selectinload**
- CORRECT `selectinload()` for all relationships accessed after query
- CORRECT Action: Add if missing

**RULE 15.1.4: CHECK 12.4 - Ambiguous Relationships**
- CORRECT Ambiguous relationships fixed with `primaryjoin`/`foreign_keys`
- CORRECT Action: Fix if missing

**RULE 15.1.5: CHECK 12.5 - Enum Comparisons**
- CORRECT Enum comparisons use `.value` in SQLAlchemy queries
- CORRECT Action: Fix if missing

**RULE 15.1.6: CHECK 12.6 - PaginatedResponse**
- CORRECT PaginatedResponse uses `page_size` and `total_pages` (NOT `size` and `pages`)
- CORRECT Action: Fix field names

**RULE 15.1.7: CHECK 12.7 - Route Order**
- CORRECT Route order: Specific routes before parameterized
- CORRECT Action: Reorder if incorrect

**RULE 15.1.8: CHECK 12.8 - FK Validation**
- CORRECT FK validation in all service methods before insert/update
- CORRECT Action: Add if missing

**RULE 15.1.9: CHECK 12.9 - Exception Constructors (CRITICAL)**
- CORRECT Exception constructors match usage
- CORRECT Search: Exception raised with arguments when constructor takes none
- CORRECT Action: Fix exception constructor calls

**RULE 15.1.10: CHECK 12.10 - StandardErrorResponse (CRITICAL)**
- CORRECT `StandardErrorResponse` has `self.message` attribute
- CORRECT Search: `exc.message` access in handlers
- CORRECT Action: Add `self.message` to `StandardErrorResponse`

**RULE 15.1.11: CHECK 12.11 - Utilities Layer**
- CORRECT Utilities layer: Pure functions only, no database access, no global state modification, type hints required
- CORRECT Action: Remove DB access and side effects from utils

**RULE 15.1.12: CHECK 12.12 - Constants Layer**
- CORRECT Constants layer: UPPER_CASE naming, group by category, string literals only, no functions/logic
- CORRECT Action: Fix constant naming and remove functions

**RULE 15.1.13: CHECK 12.13 - Naming Conventions**
- CORRECT Naming conventions: Files (`router.py` NOT `auth_router.py`), Functions (`snake_case` with type hints), Classes (`PascalCase`), Variables (`snake_case`)
- CORRECT Action: Fix naming to match conventions

**RULE 15.1.14: CHECK 12.14 - Repository Query Patterns**
- CORRECT Repository query patterns: Use `select().where()` (NOT deprecated `.get()`)
- CORRECT Action: Replace `.get()` with `select().where()`

**RULE 15.1.15: CHECK 12.15 - Role Values Case Sensitivity**
- CORRECT Role values case sensitivity: Role values MUST be lowercase in API requests (`"owner"`, `"admin"`, `"member"`, `"viewer"` - NOT `"OWNER"`, `"Owner"`)
- CORRECT Action: Document and validate lowercase requirement for role values

**RULE 15.1.16: CHECK 12.16 - Query Params with Complex Types (CRITICAL)**
- CORRECT Query params with dict/object cause `AssertionError: can only be a request body`
- CORRECT FastAPI cannot parse complex types from query params
- CORRECT Action: Use JSON strings for all complex query params

**RULE 15.1.17: CHECK 12.17 - Alembic Config Attribute (CRITICAL)**
- CORRECT Alembic Config attribute name
- CORRECT Search: `config.config_file_path` in `alembic/env.py`
- CORRECT Action: Use `config.config_file_name` (NOT `config_file_path`)

**RULE 15.1.18: CHECK 12.18 - Database Constraint Violation Handling (CRITICAL)**
- CORRECT Database constraint violation handling
- CORRECT Search: `database_exception_handler` in `src/exceptions.py` and `src/main.py`
- CORRECT Action: Implement database constraint handling (see Database Implementation section below)

---

## RULE 16: Phase 13 - Development Build

### 16.1 Development Build Rules

**RULE 16.1.1: Default Approach**
- CORRECT Default: Use existing `docker-compose.yml` directly
- CORRECT Minimal dev: `docker compose up db migrate api`
- CORRECT Optional files (DO NOT create automatically): `.cursorrules`, `docker-compose.dev.yml` (only if explicitly requested)

**RULE 16.1.2: Development Build Rules**
- CORRECT Use docker-compose.yml directly
- CORRECT Start minimal services for development
- INCORRECT Create optional files automatically

---

## RULE 17: Database Implementation

### 17.1 Database Module

**RULE 17.1.1: Database Module Pattern**
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from src.config import settings

engine = create_async_engine(settings.database_url, pool_size=10, max_overflow=20, pool_timeout=30, pool_recycle=3600, echo=settings.debug)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

### 17.2 Migration File Structure

**RULE 17.2.1: Migration File Pattern**
```python
"""Initial migration"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial'
down_revision: Union[str, None] = None  # CORRECT Must be None for initial migration

def upgrade() -> None:
    op.create_table('table_name',  # Replace with user's actual table name
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('table_name')
```

### 17.3 Alembic Configuration

**RULE 17.3.1: Alembic env.py Pattern**
```python
from src.database import Base
from src.config import settings
from src.module_name.models import ModelName  # Replace with user's actual imports

config = context.config
if config.config_file_name is not None:  # CORRECT Use config_file_name (NOT config_file_path)
    fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", settings.database_url.replace("+asyncpg", ""))  # Remove +asyncpg for offline
target_metadata = Base.metadata
```

### 17.4 Database Constraint Handler

**RULE 17.4.1: Database Exception Handler Pattern**
```python
import re
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import UniqueViolationError, ForeignKeyViolationError, NotNullViolationError, CheckViolationError
from src.schemas import StandardResponse, ErrorInfo

async def database_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    def extract_field_name(error_msg: str, constraint_name: str = None) -> str:
        if constraint_name:
            field = constraint_name
            for prefix in ['ix_', 'fk_', 'pk_', 'uq_', 'ck_']:
                if field.startswith(prefix):
                    field = field[len(prefix):]
            if '_' in field:
                parts = field.split('_', 1)
                if len(parts) > 1:
                    field = parts[1]
            for suffix in ['_key', '_idx', '_constraint']:
                if field.endswith(suffix):
                    field = field[:-len(suffix)]
            return field
        match = re.search(r'Key \(([^)]+)\)', error_msg)
        if match:
            return match.group(1)
        match = re.search(r'constraint "([^"]+)"', error_msg)
        if match:
            return extract_field_name(error_msg, match.group(1))
        return "field"
    
    def create_error_response(status_code: int, error_code: str, message: str, details: list[dict]) -> JSONResponse:
        error_info = ErrorInfo(code=error_code, details=details)
        response = StandardResponse(error=error_info, message=message)
        return JSONResponse(status_code=status_code, content=response.model_dump(exclude_none=True))
    
    if isinstance(exc, IntegrityError):
        orig_exc = exc.orig if hasattr(exc, 'orig') else exc
        if isinstance(orig_exc, UniqueViolationError):
            field_name = extract_field_name(str(orig_exc))
            return create_error_response(409, f"DUPLICATE_{field_name.upper()}", f"A record with this {field_name} already exists.", [{"field": field_name, "issue": f"{field_name} must be unique"}])
        elif isinstance(orig_exc, ForeignKeyViolationError):
            error_msg = str(orig_exc)
            match = re.search(r'Key \(([^)]+)\)=\(([^)]+)\) is not present in table "([^"]+)"', error_msg)
            if match:
                field_name, key_value, table_name = match.group(1), match.group(2), match.group(3)
                resource_name = table_name.replace('_', ' ').title().replace(' ', '')
                return create_error_response(404, f"{resource_name.upper()}_NOT_FOUND", f"The referenced {resource_name} does not exist.", [{"field": field_name, "issue": f"Referenced {resource_name} with ID '{key_value}' not found"}])
            return create_error_response(404, "FOREIGN_KEY_VIOLATION", "The referenced record does not exist.", [{"field": "reference", "issue": "Referenced record not found"}])
        elif isinstance(orig_exc, NotNullViolationError):
            error_msg = str(orig_exc)
            match = re.search(r'column "([^"]+)"', error_msg)
            field_name = match.group(1) if match else "field"
            return create_error_response(422, "REQUIRED_FIELD_MISSING", f"The field '{field_name}' is required and cannot be null.", [{"field": field_name, "issue": f"{field_name} is required"}])
        elif isinstance(orig_exc, CheckViolationError):
            field_name = extract_field_name(str(orig_exc))
            return create_error_response(422, "CHECK_CONSTRAINT_VIOLATION", f"The value provided for '{field_name}' violates a validation rule.", [{"field": field_name, "issue": "Value violates check constraint"}])
    
    # Handle direct asyncpg exceptions (fallback)
    if isinstance(exc, UniqueViolationError):
        field_name = extract_field_name(str(exc))
        return create_error_response(409, f"DUPLICATE_{field_name.upper()}", f"A record with this {field_name} already exists.", [{"field": field_name, "issue": f"{field_name} must be unique"}])
    elif isinstance(exc, ForeignKeyViolationError):
        error_msg = str(exc)
        match = re.search(r'Key \(([^)]+)\)=\(([^)]+)\) is not present in table "([^"]+)"', error_msg)
        if match:
            field_name, key_value, table_name = match.group(1), match.group(2), match.group(3)
            resource_name = table_name.replace('_', ' ').title().replace(' ', '')
            return create_error_response(404, f"{resource_name.upper()}_NOT_FOUND", f"The referenced {resource_name} does not exist.", [{"field": field_name, "issue": f"Referenced {resource_name} with ID '{key_value}' not found"}])
        return create_error_response(404, "FOREIGN_KEY_VIOLATION", "The referenced record does not exist.", [{"field": "reference", "issue": "Referenced record not found"}])
    elif isinstance(exc, NotNullViolationError):
        error_msg = str(exc)
        match = re.search(r'column "([^"]+)"', error_msg)
        field_name = match.group(1) if match else "field"
        return create_error_response(422, "REQUIRED_FIELD_MISSING", f"The field '{field_name}' is required and cannot be null.", [{"field": field_name, "issue": f"{field_name} is required"}])
    elif isinstance(exc, CheckViolationError):
        field_name = extract_field_name(str(exc))
        return create_error_response(422, "CHECK_CONSTRAINT_VIOLATION", f"The value provided for '{field_name}' violates a validation rule.", [{"field": field_name, "issue": "Value violates check constraint"}])
    return create_error_response(409, "DATABASE_ERROR", "A database constraint violation occurred.", None)

# Register in src/main.py (BEFORE catch-all handler):
# app.add_exception_handler(IntegrityError, database_exception_handler)
# app.add_exception_handler(UniqueViolationError, database_exception_handler)
# app.add_exception_handler(ForeignKeyViolationError, database_exception_handler)
# app.add_exception_handler(NotNullViolationError, database_exception_handler)
# app.add_exception_handler(CheckViolationError, database_exception_handler)
```

**RULE 17.4.2: Database Constraint Handler Rules**
- CORRECT Register database handlers BEFORE catch-all handler
- CORRECT Handle both IntegrityError and direct asyncpg exceptions
- CORRECT Extract field names from constraint names
- CORRECT Use StandardResponse format for all error responses

---

## RULE 18: Pre-Deployment Checklist

### 18.1 Pre-Deployment Verification

**CRITICAL RULE:** MANDATORY - Verify ALL before declaring "ready".

**RULE 18.1.1: Checklist Item 1 - Dependencies**
- CORRECT ALL imports have packages in `requirements/base.txt`
- CORRECT `bcrypt==4.0.1`
- CORRECT Special cases (EmailStr, BaseSettings, Form, redis.asyncio)

**RULE 18.1.2: Checklist Item 2 - Docker**
- CORRECT `migrate` service with `restart: "no"`
- CORRECT `api`/`worker` depend on `migrate`
- CORRECT `DATABASE_URL` matches credentials
- CORRECT Health checks
- CORRECT Non-standard ports
- CORRECT NO `version` field

**RULE 18.1.3: Checklist Item 3 - Migrations**
- CORRECT ONLY ONE initial migration
- CORRECT UUID for all PKs (NOT INTEGER)
- CORRECT `server_default=sa.text('now()')`
- CORRECT `down_revision: None`
- CORRECT All models imported in `alembic/env.py`

**RULE 18.1.4: Checklist Item 4 - Code Consistency**
- CORRECT All PKs use `UUID`
- CORRECT All schema IDs use `UUID`
- CORRECT All path params use `UUID`
- CORRECT All `updated_at` are `Optional[datetime]`
- CORRECT All timestamps use `server_default=func.now()`

**RULE 18.1.5: Checklist Item 5 - End-to-End**
- CORRECT Fresh clone → `docker-compose up` → Works without manual steps
- CORRECT API accessible
- CORRECT Tables exist automatically

**RULE 18.1.6: Checklist Item 6 - File Structure**
- CORRECT All required domain files exist
- CORRECT All `__init__.py` files exist
- CORRECT ONLY ONE initial migration (no duplicates)
- CORRECT Descriptive migration name

**RULE 18.1.7: Mandatory Final Check**
- CORRECT Mentally simulate: User clones fresh repo → `docker-compose up` → Everything works without manual steps
- CORRECT All checks pass before declaring ready

---

## RULE 19: Final Validation Checklist

### 19.1 Complete Validation

**CRITICAL RULE:** MANDATORY - Before declaring complete, verify ALL.

**RULE 19.1.1: Structure Validation**
- CORRECT Structure: All required files exist, `src/config.py` uses `BaseSettings` correctly, `.env` exists, `requirements/base.txt` complete

**RULE 19.1.2: Docker Validation**
- CORRECT Docker: No `version` field, non-standard ports, `migrate` service, dependencies correct, `DATABASE_URL` matches

**RULE 19.1.3: Models Validation**
- CORRECT Models: UUID PKs, `server_default=func.now()`, enums as strings, ambiguous relationships fixed, indexes, FK constraints

**RULE 19.1.4: Schemas Validation**
- CORRECT Schemas: UUID IDs, `updated_at` Optional, `page_size`/`total_pages`, NO Field() in Generic, `Annotated[Decimal, Field(...)]`, `EmailStr`, password validators

**RULE 19.1.5: Repositories Validation**
- CORRECT Repositories: `selectinload()`, explicit JOIN ON, no business logic, async

**RULE 19.1.6: Services Validation**
- CORRECT Services: FK validation, enum `.value`, no HTTP details, commit + refresh, async, raise exceptions

**RULE 19.1.7: Routers Validation**
- CORRECT Routers: `StandardResponse[T]`, route order, UUID params, no business logic, JSON strings for complex query params, correct status codes, `response_model`

**RULE 19.1.8: Exceptions Validation**
- CORRECT Exceptions: Base exceptions, `UnauthenticatedError`, handlers in correct order, error format correct, success messages

**RULE 19.1.9: Auth Validation**
- CORRECT Auth: `OAuth2PasswordBearer`, Form data, token None check, JWT standards, password security

**RULE 19.1.10: Runtime Validation**
- CORRECT Runtime: App starts cleanly, no ImportError, no mapper errors, Docker works, all endpoints use `StandardResponse`, auth flow works

**RULE 19.1.11: Critical Validation Rule**
- CORRECT CRITICAL: If ANY check fails, the project is NOT ready. Fix ALL issues before declaring complete.
- INCORRECT Declare ready with unfixed issues

---

## Summary

This guide provides rule-based instructions for complete project validation. Each rule is numbered and contains specific, actionable requirements.

**Key Principles:**
- Execute all phases systematically
- Fix all issues before moving to next phase
- Verify all checks before declaring ready
- Use user-provided values (not placeholders)
- Follow exact patterns and conventions

**Critical Reminders:**
- This file is COMPLETE and can be used STANDALONE without the 12 source files
- All validation rules, implementation patterns, and error fixes from all 12 files are included
- Execute ALL phases systematically
- Fix ALL issues before declaring ready
- Verify ALL checks before marking complete
