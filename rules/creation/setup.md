# FastAPI Project Setup Guide

**Purpose:** Complete guide for creating FastAPI backend projects following best practices.

**Reference:** https://github.com/zhanymkanov/fastapi-best-practices

## RULE 1: Foundation Principles
### 1.1 Primary Reference
- **MUST** follow conventions from `fastapi-best-practices` repository
- **MUST** use it as single source of truth for:
  - Project structure (src/, domain packages, global modules)
  - Async route usage
  - Pydantic usage
  - Dependencies / DI
  - Database / migrations patterns
  - Testing and tooling preferences
- **DO NOT** invent architecture that conflicts with the repo
- If conflict exists, resolve in favor of repo's practices

### 1.2 Strict Architecture Rules (CRITICAL - SINGLE SOURCE OF TRUTH)
- **STRICT RULE:** Router MUST be thin - NO business logic, calculations, validations, or data processing
- **STRICT RULE:** ALL business logic MUST be in service layer
- **STRICT RULE:** Router only delegates to service - receives request, calls service, returns response
- **STRICT RULE:** NO multiple DB queries in router - if endpoint needs more than 1 query, ASK user before implementation
- **STRICT RULE:** Permission checking via `require_permission("module.resource", "action")` dependency only
- **STRICT RULE:** NO permission checking in router handlers or services - handled by dependency
- **STRICT RULE:** If role information needed, get it from JWT token (token contains role name)
- **NOTE:** These rules are referenced throughout this document - see RULE 8.5, 8.6, and 12 for implementation details

### 1.3 Module Development Approach
**CRITICAL WARNING:** All module/model names in examples are STRUCTURAL PATTERNS ONLY.

**MANDATORY UNDERSTANDING:**
- Examples like "organizations", "members", "Organization", "Member" are PATTERNS ONLY
- They demonstrate HOW to structure code, NOT WHAT to build
- **NEVER** build example modules unless user explicitly requests them
- **USER PROVIDES** actual module and model names
- Apply PATTERNS to USER'S ACTUAL MODULE/MODEL NAMES

**BEFORE DEVELOPMENT - MUST ASK USER FOR:**
- Module name (e.g., "products", "users", "orders")
- Model name(s) within that module
- Specific requirements or fields for the module
- Database name, user, password
- API title, version, prefix by default use /v1/ no (/api/v1)
- Environment name, debug mode
- Celery app name (ONLY if Celery requested)

**DO NOT** proceed with code generation until user provides all required information.

## RULE 2: Authentication Module

### 2.1 Default Behavior
- **MANDATORY:** Authentication module MUST be included by default
- **ONLY skip** if user explicitly says: "no auth", "skip auth", "without auth", "don't need auth", "no authentication"
- **If user doesn't mention auth:** Automatically include complete auth module
- **Reference:** See `auth_setup.md` for complete implementation details

### 2.2 Authentication Components
When including auth module, MUST include:
- User model with authentication fields (email, password_hash, etc.)
- JWT token generation (access + refresh tokens)
- OAuth2PasswordBearer for Swagger UI
- `/token` endpoint for OAuth2 compatibility
- Password hashing with bcrypt
- Authentication dependencies (`get_auth_context_from_token`, `get_current_user_model`, `require_permission`)
- `AuthContext` dataclass for user context from JWT token (user_id, org_id, role_id, role)

**Reference:** See `auth_setup.md` for complete implementation details.

## RULE 3: Optional Components
### 3.1 Redis
- **ONLY add** if user says: "add redis", "develop redis", or "include redis"
- **DO NOT add** unless user explicitly requests it
- **Reference:** See `redis_validate.md` for complete setup

### 3.2 Celery
- **ONLY add** if user says: "add celery", "develop celery", or "include celery"
- **DO NOT add** unless user explicitly requests it
- **CRITICAL:** Redis must be set up before Celery (Celery uses Redis as broker)
- **If user requests Celery but Redis not set up:** Ask if they want Redis added first
- **Reference:** See `celery_validate.md` for complete setup

## RULE 4: Setup Files Reference
### 4.1 Project Structure
- **File:** `project_structure_validate.md` in rules/validate folder
- **START HERE** - Single source of truth for file structure creation
- **CRITICAL:** Always check if files exist before creating them
- Contains: complete file checklist, creation order, existence checks, verification steps

### 4.2 Authentication Setup
- **File:** `auth_setup.md` in rules/creation folder
- Contains: OAuth2PasswordBearer, JWT tokens, password security, token endpoints, authentication dependencies

### 4.3 Database Setup
- **File:** `database_setup.md` in rules/creation folder
- Contains: database connection, pooling, Alembic migrations, UUID patterns

### 4.4 Domain Architecture
- **File:** `module_architecture_validate.md` in rules/validate folder
- Contains: patterns for models, schemas, repositories, services, routers

### 4.5 Docker Setup
- **File:** `docker_validate.md` in rules/validate folder
- Contains: Dockerfile, docker-compose.yml patterns, health checks, service dependencies

### 4.6 Dependencies Management
- **File:** `dependencies_validate.md` in rules/validate folder
- Contains: requirements structure, critical package dependencies, verification rules

### 4.7 Configuration Setup
- **File:** `config_validate.md` in rules/validate folder
- Contains: BaseSettings setup, environment variables, pydantic-settings requirements

### 4.8 Response and Error Handling
- **File:** `response_error_handling.md` in rules folder
- **CRITICAL:** ALL API responses MUST use `StandardResponse[T]` format
- **CRITICAL:** ALL exceptions MUST extend base exception classes from `src.exceptions`
- Contains: StandardResponse format, exception hierarchy, error handling patterns

### 4.9 Development Build
- **File:** `development_build.md` in rules folder
- Contains: development service configuration, minimal build strategies, hot-reload setup
- **CRITICAL:** During development, only build `db`, `migrate`, and `api` services by default

### 4.10 RBAC and Permission Management
- **File:** `rbac.md` in rules/creation folder
- **CRITICAL:** ALL routers MUST use `require_permission("module.resource", "action")` dependency (from ACM module)
- **CRITICAL:** Permission checking is handled by the `require_permission()` dependency - NO manual checking
- **Reference:** See RULE 12 for complete permission checking patterns and RULE 1.2 for strict architecture rules 

## RULE 5: Development Workflow
### 5.1 Workflow Order (CRITICAL - FOLLOW EXACTLY)

**Step 1: Create Project Structure**
- Refer to `project_structure_validate.md` for complete file structure checklist
- **ALWAYS** check if files/directories exist before creating them
- Report to user which files exist and which need to be created
- Create all directories (src/, alembic/, requirements/, etc.)
- Create all `__init__.py` files
- Create configuration files (.gitignore, logging.ini, etc.)



**Step 2: Create Models Before Migrations**
- Create all SQLAlchemy models first
- Ensure models use UUID for primary keys
- Ensure models use `server_default=func.now()` for timestamps
- Verify all relationships are correct

**Step 3: Create Initial Migration ONCE**
- **CRITICAL:** Check if `alembic/versions/` directory exists and has any files
- **If migration files exist:** Review them, use them, DO NOT create new ones
- **If no migration files exist:** Create ONE initial migration manually
- Use descriptive name: `001_initial_migration.py`
- Use simple revision ID: `'001_initial'`
- Set `down_revision: None` for initial migration
- **DO NOT** run `alembic revision --autogenerate` for initial migration
- **DO NOT** create multiple initial migrations

**Step 4: Create Requirements Files**
- List ALL packages used in code
- Include `email-validator` if using `EmailStr`
- Include `pydantic-settings` if using `BaseSettings`
- Verify every import has corresponding package in requirements

**Step 5: Create Docker Configuration**
- Create Dockerfile
- Create docker-compose.yml with ALL services (db, redis, migrate, api, worker)
- Ensure migrate service runs before api/worker
- Verify all environment variables match

**Step 6: Final Verification**
- Run through PRE-DEPLOYMENT CHECKLIST (see RULE 12)
- Verify no duplicate migration files
- Verify all dependencies are listed
- Test that `docker-compose up` works end-to-end

### 5.2 Common Workflow Mistakes to Avoid
- INCORRECT: Creating migrations before models are complete
- INCORRECT: Running `alembic revision --autogenerate` multiple times
- INCORRECT: Creating migration files without checking if they already exist
- INCORRECT: Forgetting to add packages to requirements.txt
- INCORRECT: Creating docker-compose without migrate service
- INCORRECT: Not verifying migration file uniqueness

## RULE 6: Project Structure=
### 6.1 Root Application Folder
- **MUST** use `src/` as the root application folder
- **MUST** place domain packages under `src/`

### 6.2 Directory Structure Pattern
```
fastapi-project
├── alembic/
│   ├── __init__.py
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── exceptions.py
│   ├── pagination.py  
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── router.py
│   │
│   ├── acm/  # MANDATORY - Access Control Management module
│   │   ├── __init__.py
│   │   ├── permissions.py
│   │   ├── permission_cache.py
│   │   ├── dependencies.py
│   │   └── utils.py
│   │
│   ├── infra/  # OPTIONAL - only if Redis or Celery requested
│   │   ├── __init__.py
│   │   ├── cache_redis.py  # OPTIONAL - only if Redis requested
│   │   └── celery_app.py  # OPTIONAL - only if Celery requested
│   │
│   └── <user_module>/  # USER PROVIDES ACTUAL MODULE NAME
│       ├── __init__.py
│       ├── models.py
│       ├── schemas.py
│       ├── repository.py
│       ├── service.py
│       ├── router.py
│       ├── dependencies.py
│       ├── constants.py
│       ├── exceptions.py
│       ├── utils.py
│       ├── config.py
│       └── documentations/  # Swagger/OpenAPI documentation classes
│           ├── __init__.py
│           └── {module}_api_doc.py (e.g., organization_api_doc.py)
├── requirements/
│   ├── base.txt
│   └── dev.txt

├── tests/
├── templates/
├── .env
├── .gitignore
├── logging.ini
├── alembic.ini
├── Dockerfile
└── docker-compose.yml
```

**CRITICAL NOTE:** Module names in structure are STRUCTURAL PATTERN EXAMPLES ONLY. USER PROVIDES ACTUAL MODULE NAMES.

## RULE 7: Architecture & Layering
### 7.1 Async All The Way
- **MUST** use async routes and async DB access
- **MUST** follow "Async Routes" recommendations from the repo
- **MUST NOT** do blocking I/O inside async routes
- If blocking I/O required, run it in a threadpool

### 7.2 Configuration (`src/config.py`)
- **Reference:** See `config_validate.md` in rules/validate folder
- **MUST** implement using Pydantic BaseSettings (from `pydantic_settings`)
- **CRITICAL:** Must include `pydantic-settings` in requirements/base.txt
- Settings for Postgres, Redis, and Celery must come from here
- **MUST** use `model_config` dict (not `Config` class) for Pydantic v2

### 7.3 Database (`src/database.py`)
- **MUST** implement as central place for:
  - Async SQLAlchemy engine: `create_async_engine(settings.database_url, ...)`
  - Connection pool configuration (pool_size, max_overflow, pool_timeout, pool_recycle)
  - Async session maker (`async_sessionmaker`)
- **MUST** provide `get_session()` dependency for FastAPI routes/services
- **Reference:** See `database_setup.md` for complete database setup instructions

### 7.4 Database Migrations (Alembic)
Reference RULE 5.1 – Step 3

## RULE 8: Domain Module Architecture
### 8.1 Module File Structure
For each domain module (USER PROVIDES ACTUAL MODULE NAME), MUST include:
- `models.py` → SQLAlchemy models
- `schemas.py` → Pydantic v2 models
- `repository.py` → Database operations
- `service.py` → Business logic
- `router.py` → FastAPI endpoints
- `dependencies.py` → Domain-specific dependencies
- `constants.py` → Domain-specific constants
- `exceptions.py` → Domain-specific exceptions
- `utils.py` → Domain-specific utilities
- `config.py` → Domain-specific configuration (optional)
- `documentations/` → Swagger/OpenAPI documentation classes
  - `__init__.py`
  - `{module}_api_doc.py` → API documentation class with `summary` and `description` for each endpoint

**Reference:** See `module_architecture_validate.md` for complete domain architecture patterns.

### 8.2 Models (`models.py`)
**RULE 8.2.1: Primary Keys**
- **MUST** use UUID type, NOT int
- **MUST** use `UUID` type with `default=uuid4` for primary keys
- **Correct pattern:**
  ```python
  from uuid import uuid4, UUID
  
  id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, index=True)
  ```

**RULE 8.2.2: Foreign Keys**
- **MUST** use UUID type matching the referenced primary key
- **Correct pattern:**
  ```python
  organization_id: Mapped[UUID] = mapped_column(
      ForeignKey("organizations.id", ondelete="CASCADE"),
      index=True,
  )
  ```

**RULE 8.2.3: Timestamp Fields**
- **CRITICAL:** MUST use `server_default=func.now()` NOT `default_factory`
- `default_factory` is a Python dataclass feature and does NOT work with SQLAlchemy 2.x Mapped types
- **Correct pattern:**
  ```python
  from sqlalchemy import DateTime, func
  from datetime import datetime
  
  created_at: Mapped[datetime] = mapped_column(
      DateTime(timezone=True),
      server_default=func.now(),
  )
  updated_at: Mapped[datetime | None] = mapped_column(
      DateTime(timezone=True),
      onupdate=func.now(),
  )
  ```

**RULE 8.2.4: Soft Delete Fields**
- **MANDATORY:** ALL models MUST support soft delete (except audit_logs which is immutable)
- **MUST** include `deleted_at` field for soft delete functionality
- **CRITICAL:** `deleted_at` MUST be Optional[datetime] and nullable
- **CRITICAL:** `deleted_at` MUST be indexed for query performance
- **Correct pattern:**
  ```python
  from typing import Optional
  from datetime import datetime
  from sqlalchemy import DateTime
  
  deleted_at: Mapped[Optional[datetime]] = mapped_column(
      DateTime(timezone=True),
      nullable=True,
      index=True,
  )
  ```
- **Soft Delete Logic:**
  - `deleted_at = NULL` → Record is active (not deleted)
  - `deleted_at = <timestamp>` → Record is soft deleted
  - Repository queries MUST filter: `WHERE deleted_at IS NULL` for active records
- **Exception:** Audit logs (audit_logs table) MUST NOT have `deleted_at` field - they are immutable and append-only

### 8.3 Schemas (`schemas.py`)
**RULE 8.3.1: Schema Organization**
- **Request Schemas:** Define input validation for API endpoints (e.g., `ResourceCreate`, `ResourceUpdate`, `ResourceListQuery`)
- **Response Schemas:** Define output structure for API responses (e.g., `ResourceRead`, `ResourceList`)
- **Purpose:** Request schemas validate input, Response schemas structure output
- **Business Logic:** Implemented in `service.py`, NOT in schemas

**RULE 8.3.2: ID Fields**
- **MUST** use UUID type for all ID fields
- **MUST** use `ConfigDict(from_attributes=True)` for Pydantic v2

**RULE 8.3.3: Request Schema Pattern**
```python
from uuid import UUID
from pydantic import BaseModel

class ResourceCreate(BaseModel):  # Request schema
    name: str
    organization_id: UUID  # CORRECT: Must be UUID

class ResourceUpdate(BaseModel):  # Request schema
    name: Optional[str] = None

class ResourceListQuery(BaseModel):  # Query schema
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None
```

**RULE 8.3.4: Response Schema Pattern**
```python
from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ResourceRead(BaseModel):  # Response schema
    id: UUID  # CORRECT: Must be UUID
    name: str
    created_at: datetime
    updated_at: Optional[datetime] = None  # CORRECT: Must be Optional (None on creation)
    model_config = ConfigDict(from_attributes=True)
```

**RULE 8.3.5: Updated At Field**
- **CRITICAL:** `updated_at` field MUST be Optional in response schemas
- `updated_at` is `None` when a record is first created (before any updates)
- `onupdate=func.now()` only triggers on UPDATE operations, not on INSERT
- **WRONG pattern:**
  ```python
  updated_at: datetime  # INCORRECT: ERROR: None on creation will fail validation
  ```

### 8.4 Repository (`repository.py`)
**RULE 8.4.1: Purpose**
- **Data Access Layer** - Handle database operations only (CRUD using AsyncSession)
- **Pure database operations** - no business logic, no validation, no HTTP concerns
- **Single Responsibility**: Only database queries and data persistence

**RULE 8.4.2: What Repository SHOULD Contain**
- Database queries (SELECT, INSERT, UPDATE, DELETE)
- SQLAlchemy operations using AsyncSession
- Eager loading relationships with `selectinload()`
- Filtering, sorting, pagination at database level
- **Soft delete filtering** - MUST filter `WHERE deleted_at IS NULL` for active records
- Flushing changes to database (using `flush()`, NOT `commit()`)
- Query building and optimization

**RULE 8.4.3: What Repository MUST NOT Contain**
- **Business logic** (validation rules, business rules, calculations)
- **HTTP concerns** (status codes, request/response handling)
- **Validation** (use schemas and service layer for validation)
- **Business rules** (e.g., "cannot delete if has dependencies" - this is service layer)
- **Error messages** (use constants.py for messages)
- **Configuration** (use config.py for settings)

**RULE 8.4.4: ID Parameters**
- **MUST** use UUID type for all ID parameters, not int

**RULE 8.4.5: CORRECT Repository Pattern**
```python
# src/organizations/repository.py
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from datetime import datetime

class OrganizationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, org_id: UUID) -> Optional[Organization]:
        """Get organization by ID - pure database operation"""
        result = await self.session.execute(
            select(Organization)
            .where(Organization.id == org_id, Organization.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()
    
    async def create(self, org: Organization) -> Organization:
        """Create organization - pure database operation (flushes, does not commit)"""
        self.session.add(org)
        await self.session.flush()
        await self.session.refresh(org)
        return org
    
    async def list_with_pagination(
        self, 
        page: int, 
        page_size: int,
        filters: dict = None
    ) -> tuple[list[Organization], int]:
        """List organizations with pagination - pure database operation"""
        query = select(Organization).where(Organization.deleted_at.is_(None))
        # Apply filters (database-level filtering)
        if filters:
            if filters.get("status"):
                query = query.where(Organization.status == filters["status"])
        # Count total
        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(query)
        items = result.scalars().all()
        return list(items), total
```
**RULE 8.4.6: Key Principles**
- **Repository is thin** - only database operations
- **No business logic** - all business rules go in service.py
- **No validation** - validation happens in schemas and service layer
- **No error messages** - use constants.py for messages
- **Pure data access** - repository methods should be reusable and testable

**RULE 8.4.6.1: Soft Delete Filtering (CRITICAL)**
- **CRITICAL:** ALL repository queries MUST filter out soft-deleted records by default
- **MUST** add `WHERE deleted_at IS NULL` to all SELECT queries (except audit_logs)
- **CORRECT Pattern:**
  ```python
  # CORRECT: Filter soft-deleted records
  query = select(Organization).where(Organization.deleted_at.is_(None))
  
  # CORRECT: Combined with other filters
  query = select(Organization).where(
      Organization.id == org_id,
      Organization.deleted_at.is_(None)
  )
  ```
- **Exception:** audit_logs table does NOT have deleted_at field (immutable audit trail)
- **Soft Delete Operations:**
  - Soft delete: Set `deleted_at = datetime.now(timezone.utc)` (do NOT use `session.delete()`)
  - Hard delete: Only use `session.delete()` if explicitly required (not recommended)
- **WRONG Pattern:**
  ```python
  # INCORRECT: Missing soft delete filter
  query = select(Organization).where(Organization.id == org_id)
  
  # INCORRECT: Using session.delete() for soft delete
  await self.session.delete(org)  # WRONG: This is hard delete
  ```

**RULE 8.4.7: Transaction Management (CRITICAL)**
- **CRITICAL:** Repository methods MUST use `flush()` instead of `commit()`
- **CRITICAL:** Repository MUST NOT commit transactions - service layer controls commits
- **CRITICAL:** Repository methods MUST NOT call `await self.session.commit()` - this breaks transaction boundaries
- **Purpose:** Ensures proper transaction boundaries - service can perform multiple operations in a single transaction
- **Common Violation:** Using `await self.session.commit()` in repository `create()` or `update()` methods - this is WRONG
- **CORRECT Pattern:**
  ```python
  async def create(self, org: Organization) -> Organization:
      """Create organization - pure database operation (flushes, does not commit)"""
      self.session.add(org)
      await self.session.flush()  # CORRECT: Flush changes without committing
      await self.session.refresh(org)
      return org
  
  async def update(self, org: Organization) -> Organization:
      """Update organization - pure database operation (flushes, does not commit)"""
      self.session.add(org)
      await self.session.flush()  # CORRECT: Flush changes without committing
      await self.session.refresh(org)
      return org
  
  async def soft_delete(self, org: Organization) -> None:
      """Soft delete organization - pure database operation (flushes, does not commit)"""
      from datetime import datetime, timezone
      org.deleted_at = datetime.now(timezone.utc)  # CORRECT: Soft delete by setting deleted_at (timezone-aware)
      self.session.add(org)
      await self.session.flush()  # CORRECT: Flush changes without committing
  ```
- **WRONG Pattern:**
  ```python
  # INCORRECT: Repository committing transactions
  async def create(self, org: Organization) -> Organization:
      self.session.add(org)
      await self.session.commit()  # WRONG: Repository should not commit
      await self.session.refresh(org)
      return org
  ```
- **Rationale:**
  - Service layer may need to perform multiple repository operations in a single transaction
  - If repository commits, each operation becomes a separate transaction (breaks transaction boundaries)
  - Service layer controls when to commit, ensuring all-or-nothing behavior
  - If an error occurs after one repository commit but before service completes, partial commits occur
  - Proper pattern: Repository flushes → Service commits once at the end

### 8.5 Service (`service.py`)
**RULE 8.5.1: Business Logic Location**
- **ALL business logic MUST be in service.py** - NOT in router, NOT in repository
- Service methods receive request schemas and `ctx: AuthContext`, return response schemas
- Service uses repository for data access
- Service handles validation, business rules, transactions
- **Purpose:** Business logic layer - validates input, applies rules, orchestrates data operations
- **CRITICAL:** **MUST NOT** check permissions in service - permission validation happens in router via `require_permission()` dependency (see RULE 1.2)
- **CRITICAL:** Service uses `ctx: AuthContext` parameter (not `current_user: User`)
- **CRITICAL:** Service uses `ctx.org_id` for organization filtering (None for superadmin = all orgs)
- **CRITICAL:** If User model is needed (e.g., for email in audit logs), fetch it using `get_current_user_model(ctx, session)`
- **Reference:** See RULE 1.2 for strict architecture rules and `REFACTORING_PATTERN.md` for complete guide

**RULE 8.5.4: Transaction Management (CRITICAL)**
- **CRITICAL:** Service layer MUST control transaction commits - repository uses `flush()`, service uses `commit()`
- **CRITICAL:** Service MUST commit transactions once at the end of operations, after all repository calls and audit logs
- **Purpose:** Ensures proper transaction boundaries - all operations in a service method execute in a single transaction
- **CORRECT Pattern:**
  ```python
  async def create_resource(
      self,
      data: ResourceCreate,
      ctx: AuthContext,
      request: Optional[Request] = None,
  ) -> ResourceRead:
      """Create resource"""
      # Permission validation already done in router via require_permission()
      
      # Validate business rules
      existing = await self.repository.get_by_organization_and_name(...)
      if existing:
          raise DuplicateResourceName(...)
      
      # Create resource (repository uses flush, not commit)
      resource = Resource(...)
      resource = await self.repository.create(resource)
      
      # Create audit log (also uses flush internally)
      await create_audit_log(
          session=self.session,
          action="create",
          entity_type="resource",
          entity_id=resource.id,
          ...
      )
      
      # Commit transaction (repository uses flush, service controls commit)
      await self.session.commit()
      await self.session.refresh(resource)
      
      return ResourceRead.model_validate(resource)
  ```
- **WRONG Pattern:**
  ```python
  # INCORRECT: No commit in service, repository commits separately
  async def create_resource(self, data: ResourceCreate, ctx: AuthContext) -> ResourceRead:
      resource = Resource(...)
      resource = await self.repository.create(resource)  # WRONG: Repository commits here
      await create_audit_log(...)  # Separate transaction if audit log also commits
      # WRONG: No commit in service - partial commits if error occurs
      return ResourceRead.model_validate(resource)
  
  # INCORRECT: Multiple commits in service
  async def update_resource(self, resource_id: UUID, data: ResourceUpdate, ctx: AuthContext) -> ResourceRead:
      resource = await self.repository.get_by_id(resource_id)
      resource.name = data.name
      await self.repository.update(resource)  # WRONG: Repository commits here
      await self.session.commit()  # WRONG: Multiple commits break transaction boundaries
      await create_audit_log(...)
      await self.session.commit()  # WRONG: Another commit
  ```
- **Rationale:**
  - Service methods often perform multiple operations (create/update resource + create audit log)
  - All operations should be in a single transaction for atomicity
  - If repository commits, each operation becomes a separate transaction
  - Service commits once at the end ensures all-or-nothing behavior
  - If an error occurs, the entire transaction can be rolled back (no partial commits)
  - Proper pattern: Repository flushes → Service commits once at the end
- **Exception Handling:**
  - Service methods should use try/except blocks to handle errors
  - On error, call `await self.session.rollback()` to undo all changes
  - Example:
    ```python
    try:
        resource = await self.repository.create(resource)
        await create_audit_log(...)
        await self.session.commit()
        await self.session.refresh(resource)
        return ResourceRead.model_validate(resource)
    except Exception as e:
        await self.session.rollback()
        raise
    ```

**RULE 8.5.2: Service Separation**
- Services must NOT know HTTP details (no FastAPI imports)
- Services work with domain models, repositories, and infra (like Celery)
- Services must NOT check permissions - permission validation happens in router via `require_permission()` dependency
- Services use `ctx: AuthContext` for user identification and organization filtering

**RULE 8.5.3: Permission Handling in Service (CRITICAL)**
- **MUST NOT** use `check_permission()` or `check_system_permission()` in service
- **MUST NOT** check permissions in service - permission validation happens in router via `require_permission()`
- **MUST** use `ctx: AuthContext` parameter instead of `current_user: User`
- **MUST** use `ctx.org_id` for organization filtering (None for superadmin means all orgs)
- **MUST** add comment: "Permission validation already done in router via require_permission()"
- **CORRECT Pattern:**
  ```python
  from src.schemas import AuthContext
  from src.auth.dependencies import get_current_user_model  # Only if you need User model with permissions_json
  
  class ResourceService:
      async def list_resources(
          self,
          query: ResourceListQuery,
          ctx: AuthContext,
          session: AsyncSession,
      ) -> ResourcePaginatedResponse:
          """
          List resources with pagination.
          
          Permission validation already done in router via require_permission("resources.resource", "read_all").
          This method only determines data scope based on organization.
          """
          # Permission validation already done in router via require_permission()
          # Use ctx.org_id for organization filtering (None = superadmin = all orgs)
          org_id_filter = ctx.org_id  # None for superadmin means all orgs
          
          # Get resources from repository with scope filter
          items, total = await self.repository.list_with_pagination(
              org_id_filter=org_id_filter,
              page=query.page,
              page_size=query.page_size,
              # ... other params
          )
          return ResourcePaginatedResponse(items=items, total=total)
      
      async def create_resource(
          self,
          data: ResourceCreate,
          ctx: AuthContext,
      ) -> ResourceRead:
          """Create resource"""
          # Permission validation already done in router via require_permission("resources.resource", "create")
          
          resource = Resource(
              name=data.name,
              created_by=ctx.user_id,  # Use ctx.user_id
              updated_by=ctx.user_id,
              organization_id=ctx.org_id,
          )
          resource = await self.repository.create(resource)
          return ResourceRead.model_validate(resource)
  ```
- **WRONG Pattern:**
  ```python
  # ❌ WRONG: Checking permissions in service
  class ResourceService:
      async def list_resources(self, current_user: User):
          # ❌ DON'T check permissions here
          if not check_permission(current_user.permissions_json, "resources.resource", "read"):
              raise ForbiddenError(...)
  
  # ❌ WRONG: Using User model instead of AuthContext
  async def list_resources(self, current_user: User):
      # ❌ Should use ctx: AuthContext
      pass
  ```

### 8.6 Router (`router.py`)
**RULE 8.6.1: Router Development Flow**
- **Flow:** Router → Request Schema → Service (Business Logic) → Response Schema
- **Main Purpose:**
  - Define **request schemas** in `schemas.py` for input validation
  - Define **response schemas** in `schemas.py` for output structure
  - Implement **business logic** in `service.py`
  - Router is **thin** - only handles HTTP concerns and delegates to service
- **CRITICAL:** Permission validation happens ONLY via `require_permission()` dependency (see RULE 12)
- **Reference:** See RULE 1.2 for strict architecture rules (router thin, no business logic, no multiple DB queries, role from JWT token)

**RULE 8.6.2: Router Structure Pattern**
```python
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, Response, status
from fastapi.responses import Response as FastAPIResponse

from src.schemas import StandardResponse, AuthContext
from src.auth.dependencies import require_permission
from src.module.dependencies import ResourceApiDep
from src.module.documentations.resource_api_doc import ResourceApiDocs
from src.module.schemas import ResourceCreate, ResourceUpdate, ResourceListQuery, ResourceRead
from src.module.constants import SUCCESS_RESOURCE_RETRIEVED

router = APIRouter(
    prefix="/resources",
    tags=["Resources"],
)
```

**RULE 8.6.3: Router Endpoint Pattern**
- **MUST** use API dependency class pattern (e.g., `ResourceApiDep`) instead of direct service instantiation
- **MUST** use Pydantic schemas for request bodies (e.g., `data: ResourceCreate`) - defines input validation
- **MUST** use Pydantic schemas for response models (e.g., `ResourceRead`) - defines output structure
- **MUST** use `Depends()` pattern for query parameters when query schema exists
- **MUST** include comprehensive endpoint documentation (summary, description) for Swagger from documentation class
- **MUST** specify response_model and status_code in decorator
- **CRITICAL:** **MUST** use `require_permission("module.resource", "action")` dependency for ALL routes that need permission checking (see RULE 12)
- **CRITICAL:** **MUST NOT** check permissions in route handlers - permission checking is handled by `require_permission()` dependency
- **CRITICAL:** **MUST** include `request: Request = None` parameter in all endpoints that use `set_etag_headers_and_return()` (see RULE 14 and RULE 15)
- **CRITICAL:** **MUST** use centralized `set_etag_headers_and_return()` helper function from `src.utils` - NO inline header setting (see RULE 14)
- **CRITICAL:** **MUST** pass `request` parameter to `set_etag_headers_and_return()` for X-Request-ID header support (see RULE 15)
- **Reference:** See RULE 1.2 for strict architecture rules (no business logic in router, no multiple DB queries, role from JWT token)

**RULE 8.6.4: Correct Endpoint Pattern**
```python
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, Response, Request, status
from fastapi.responses import Response as FastAPIResponse

from src.schemas import StandardResponse, AuthContext  # CORRECT: Import StandardResponse and AuthContext
from src.auth.dependencies import require_permission  # CORRECT: Import require_permission from auth.dependencies
from src.module.dependencies import ResourceApiDep
from src.module.documentations.resource_api_doc import ResourceApiDocs
from src.module.schemas import ResourceCreate, ResourceUpdate, ResourceListQuery, ResourceRead
from src.module.constants import SUCCESS_RESOURCE_RETRIEVED
from src.utils import set_etag_headers_and_return, set_request_id_header  # CORRECT: Import centralized utilities

router = APIRouter(
    prefix="/resources",
    tags=["Resources"],
)

# GET RESOURCE BY ID
@router.get(
    "/{resource_id}",
    response_model=StandardResponse[ResourceRead],
    status_code=status.HTTP_200_OK,
    summary=ResourceApiDocs.get["summary"],
    description=ResourceApiDocs.get["description"],
)
async def get_resource(
    resource_id: UUID,
    ctx: AuthContext = Depends(require_permission("resources.resource", "read")),  # CORRECT: AuthContext from require_permission
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    api: ResourceApiDep = Depends(ResourceApiDep),
    request: Request = None,  # CORRECT: Request parameter for X-Request-ID header
    response: Response = None,
) -> StandardResponse[ResourceRead] | FastAPIResponse:
    """Get resource details"""
    result = await api.get_resource(resource_id, ctx, if_none_match)
    
    # Handle 304 response
    if isinstance(result, FastAPIResponse):
        set_request_id_header(request, result)  # CORRECT: Set X-Request-ID for 304 responses
        return result
    
    # CORRECT: Use centralized helper function with request parameter
    return set_etag_headers_and_return(response, result, SUCCESS_RESOURCE_RETRIEVED, request)

# CREATE RESOURCE
@router.post(
    "",
    response_model=StandardResponse[ResourceRead],
    status_code=status.HTTP_201_CREATED,
    summary=ResourceApiDocs.create["summary"],
    description=ResourceApiDocs.create["description"],
)
async def create_resource(
    data: ResourceCreate,
    ctx: AuthContext = Depends(require_permission("resources.resource", "create")),  # CORRECT: AuthContext from require_permission
    api: ResourceApiDep = Depends(ResourceApiDep),
    request: Request = None,  # CORRECT: Request parameter for X-Request-ID header
    response: Response = None,
) -> StandardResponse[ResourceRead]:
    """Create a new resource"""
    result = await api.create_resource(data, ctx)
    
    # CORRECT: Use centralized helper function with request parameter
    return set_etag_headers_and_return(response, result, SUCCESS_RESOURCE_CREATED, request)

# LIST RESOURCES
@router.get(
    "",
    response_model=StandardResponse[ResourcePaginatedResponse],
    status_code=status.HTTP_200_OK,
    summary=ResourceApiDocs.list["summary"],
    description=ResourceApiDocs.list["description"],
)
async def list_resources(
    query: ResourceListQuery = Depends(ResourceListQuery),
    ctx: AuthContext = Depends(require_permission("resources.resource", "read_all")),  # CORRECT: AuthContext from require_permission
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    api: ResourceApiDep = Depends(ResourceApiDep),
    request: Request = None,  # CORRECT: Request parameter for X-Request-ID header
    response: Response = None,
) -> StandardResponse[ResourcePaginatedResponse] | FastAPIResponse:
    """List resources with pagination, filtering, search, and sorting"""
    result = await api.list_resources(query, ctx, if_none_match)
    
    # Handle 304 response
    if isinstance(result, FastAPIResponse):
        set_request_id_header(request, result)  # CORRECT: Set X-Request-ID for 304 responses
        return result
    
    # CORRECT: Use centralized helper function with request parameter
    return set_etag_headers_and_return(response, result, SUCCESS_RESOURCES_RETRIEVED, request)
```

**RULE 8.6.5: WRONG Patterns (DO NOT DO THIS)**
```python
# INCORRECT: Direct service instantiation (should use API dependency)
@router.post("")
async def create_resource(
    data: ResourceCreate,
    session: AsyncSession = Depends(get_session),
):
    service = ResourceService(session)  # INCORRECT: Direct service instantiation
    result = await service.create_resource(data)
    return StandardResponse(data=result, message="...")

# INCORRECT: Individual Query() parameters (should use query schema with Depends())
@router.get("")
async def list_resources(
    page: int = Query(1),  # INCORRECT: Individual Query() parameters
    page_size: int = Query(20),
    search: str = Query(None),
    session: AsyncSession = Depends(get_session),
):
    ...

# INCORRECT: Using User model instead of AuthContext
@router.get("")
async def list_resources(
    current_user: User = Depends(require_permission("resources.resource", "read")),  # INCORRECT: Should use AuthContext
    api: ResourceApiDep = Depends(ResourceApiDep),
):
    return await api.list_resources(query, current_user)

# INCORRECT: Checking permissions in route handler (should use require_permission() dependency)
@router.get("")
async def list_resources(
    ctx: AuthContext = Depends(get_auth_context_from_token),  # INCORRECT: Missing require_permission
    api: ResourceApiDep = Depends(ResourceApiDep),
):
    # INCORRECT: Permission check in route handler
    if not check_permission(ctx.permissions_json, "resources.resource", "read"):
        raise ForbiddenError(...)
    return await api.list_resources(query, ctx)

# INCORRECT: Business logic in router (should be in service)
@router.post("")
async def create_resource(
    data: ResourceCreate,
    ctx: AuthContext = Depends(require_permission("resources.resource", "create")),
    api: ResourceApiDep = Depends(ResourceApiDep),
):
    # INCORRECT: Business logic in router
    if data.price < 0:
        raise ValueError("Price cannot be negative")
    # Should be in service, not router
    return await api.create_resource(data, ctx)

# INCORRECT: Multiple DB queries in router (should ask before implementation)
@router.get("/{resource_id}")
async def get_resource(
    resource_id: UUID,
    ctx: AuthContext = Depends(require_permission("resources.resource", "read")),
    session: AsyncSession = Depends(get_session),
):
    # INCORRECT: Multiple queries in router - should ask user before implementing
    resource = await session.get(Resource, resource_id)
    user = await session.get(User, ctx.user_id)
    org = await session.get(Organization, resource.org_id)
    # Should consolidate in service or ask user if this is acceptable

# INCORRECT: Missing require_permission() dependency
@router.post("")
async def create_resource(
    data: ResourceCreate,
    ctx: AuthContext = Depends(get_auth_context_from_token),  # INCORRECT: No permission check
    api: ResourceApiDep = Depends(ResourceApiDep),
):
    return await api.create_resource(data, ctx)

# INCORRECT: Importing require_permission from wrong location
from src.acm.dependencies import require_permission  # INCORRECT: Should import from src.auth.dependencies

# CORRECT: Import require_permission from auth.dependencies
from src.auth.dependencies import require_permission  # CORRECT: Import from src.auth.dependencies

# INCORRECT: Inline header setting (should use centralized helper function)
@router.get("/{resource_id}")
async def get_resource(
    resource_id: UUID,
    ctx: AuthContext = Depends(require_permission("resources.resource", "read")),
    api: ResourceApiDep = Depends(ResourceApiDep),
    response: Response = None,
):
    result = await api.get_resource(resource_id, ctx)
    # INCORRECT: Setting headers directly in router
    if response and hasattr(result, '_etag'):
        response.headers["ETag"] = result._etag
        response.headers["Last-Modified"] = result._last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
    return StandardResponse(data=result, message=SUCCESS_MESSAGE)

# INCORRECT: Missing request parameter in set_etag_headers_and_return() call
@router.get("/{resource_id}")
async def get_resource(
    resource_id: UUID,
    ctx: AuthContext = Depends(require_permission("resources.resource", "read")),
    api: ResourceApiDep = Depends(ResourceApiDep),
    response: Response = None,
    # INCORRECT: Missing request: Request = None parameter
):
    result = await api.get_resource(resource_id, ctx)
    # INCORRECT: Missing request parameter - X-Request-ID header won't be set
    return set_etag_headers_and_return(response, result, SUCCESS_MESSAGE)  # WRONG: Missing request parameter

# CORRECT: Include request parameter and pass it to helper function
@router.get("/{resource_id}")
async def get_resource(
    resource_id: UUID,
    ctx: AuthContext = Depends(require_permission("resources.resource", "read")),
    api: ResourceApiDep = Depends(ResourceApiDep),
    request: Request = None,  # CORRECT: Request parameter for X-Request-ID header
    response: Response = None,
):
    result = await api.get_resource(resource_id, ctx)
    # CORRECT: Pass request parameter to set X-Request-ID header
    return set_etag_headers_and_return(response, result, SUCCESS_MESSAGE, request)
```

**RULE 8.6.6: Query Parameters Pattern**
- **MUST** use query schema with `Depends()` when query schema exists
- **CORRECT:** `query: ResourceListQuery = Depends(ResourceListQuery)`
- **WRONG:** Individual `Query()` parameters when query schema exists
- **Exception:** Simple single query parameters can use `Query()` directly

**RULE 8.6.7: API Dependency Pattern (CRITICAL)**

**CRITICAL VIOLATION:** All routers MUST use API dependency pattern instead of direct service instantiation.

**Current Pattern (WRONG - DO NOT USE):**
```python
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)  #WRONG: Direct instantiation
    result = await service.get_user(user_id)
    return result
```

**Required Pattern (CORRECT - MUST USE):**
```python
async def get_resource(
    resource_id: UUID,
    ctx: AuthContext = Depends(require_permission("resources.resource", "read")),  # CORRECT: AuthContext from require_permission
    api: ResourceApiDep = Depends(ResourceApiDep),  # CORRECT: API dependency injection
):
    return await api.get_resource(resource_id, ctx)  # CORRECT: Delegate to API dependency with ctx
```

**Key Requirements:**
- **MUST** use API dependency class (e.g., `ResourceApiDep`, `UserApiDep`) injected via `Depends()`
- **MUST NOT** directly instantiate services in router endpoints (e.g., `service = UserService(session)`)
- **MUST NOT** inject `AsyncSession` directly in router endpoints for service instantiation
- API dependency handles service instantiation and business logic delegation
- Router endpoints delegate directly to API dependency methods
- **CORRECT:** `api: ResourceApiDep` → `return await api.create_resource(data=data)`
- **WRONG:** `session: AsyncSession = Depends(get_session)` → `service = ResourceService(session)`

**RULE 8.6.8: Development Flow Summary**
```
Router (router.py)
  ↓
Request Schema (schemas.py) - Input Validation
  ↓
Service (service.py) - Business Logic
  ↓
Repository (repository.py) - Data Access
  ↓
Response Schema (schemas.py) - Output Structure
  ↓
Router (router.py) - Returns Response
```

**RULE 8.6.9: Single Router File - No Separate my_router.py Files**
- **MUST consolidate all endpoints in a single `router.py` file** - do not create separate `my_router.py` files for operator endpoints
- **Operator endpoints MUST use `/me` path pattern** (e.g., `GET /warmup-plans/me` instead of `GET /my-warmup-plans`)
- **Route ordering**: Place `/me` routes before `/{resource_id}` routes to avoid route conflicts (e.g., `/me` before `/{plan_id}`)
- **CORRECT**: All endpoints in `router.py` with operator endpoints using `/resource/me` pattern
- **WRONG**: Separate `my_router.py` file with `/my-resource` prefix
- **Rationale**: Reduces code duplication, simplifies maintenance, and follows RESTful resource-based URI patterns

**RULE 8.6.10: Rationale**
- **Request schemas** define input validation - single source of truth for request structure
- **Response schemas** define output structure - single source of truth for response structure
- **Business logic in service.py** - clear separation of concerns, testable, reusable
- **Router is thin** - only handles HTTP concerns (routing, validation, documentation, Swagger)
- **Service contains ALL business logic** - validation, business rules, transactions, orchestration
- API dependency pattern provides better separation of concerns
- Query schema with `Depends()` centralizes query parameter validation
- Prevents field definition duplication between router and schema
- Ensures validation is centralized in Pydantic schemas
- Maintains DRY principle (Don't Repeat Yourself)
- Makes maintenance easier (change schema once, not in multiple places)
- FastAPI automatically validates and parses request bodies using schemas
- Comprehensive documentation improves API discoverability (Swagger)
- Consistent, clean router code that delegates to service

**RULE 8.6.11: ETag Logic Location (CRITICAL)**
- **CRITICAL:** ETag logic MUST be in service layer, NOT in router layer
- **ETag is business logic concern** - version validation, conditional updates belong in service
- **Service layer handles ETag validation** - checks If-Match/If-None-Match, generates ETag, validates version conflicts
- **CORRECT:** Service methods accept HTTP headers, generate ETag, validate version conflicts, return Response objects with status codes (304, 412)
- **WRONG:** Router handles ETag generation, validation, or conditional request logic
- **Reference:** See `error_prevention.md` RULE 19 for complete ETag implementation patterns

### 8.7 Constants (`constants.py`)
**RULE 8.7.1: Purpose**
- **Domain-specific constants** - Static values used across the module
- **Error codes and messages** - Centralized error message strings
- **Status values** - Enum-like string constants
- **Magic numbers/strings** - Static values that should not be hardcoded

**RULE 8.7.2: What Constants SHOULD Contain**
- Error message strings (e.g., `ERROR_ORGANIZATION_NOT_FOUND = "Organization not found"`)
- Success message strings (e.g., `SUCCESS_ORGANIZATION_CREATED = "Organization created successfully"`)
- Status values (e.g., `STATUS_ACTIVE = "active"`, `STATUS_INACTIVE = "inactive"`)
- Error codes (e.g., `ERROR_CODE_ORG_NOT_FOUND = "ORGANIZATION_NOT_FOUND"`)
- Enum-like constants (e.g., `ROLE_ADMIN = "admin"`, `ROLE_CREATOR = "creator"`)
- Magic numbers/strings that are used in multiple places

**RULE 8.7.3: What Constants MUST NOT Contain**
- **Functions or logic** (use utils.py for functions)
- **Computed values** (only static string/number literals)
- **Database access** (use repository.py for database operations)
- **Configuration** (use config.py for environment-based settings)
- **Business logic** (use service.py for business logic)

**RULE 8.7.4: CORRECT Constants Pattern**
```python
# src/organizations/constants.py
# Error Messages
ERROR_ORGANIZATION_NOT_FOUND = "Organization not found"
ERROR_ORGANIZATION_ALREADY_EXISTS = "Organization with this name already exists"
ERROR_INVALID_STATUS = "Invalid organization status"
ERROR_ORGANIZATION_HAS_USERS = "Cannot delete organization. It has active users."

# Success Messages
SUCCESS_ORGANIZATION_CREATED = "Organization created successfully"
SUCCESS_ORGANIZATION_UPDATED = "Organization updated successfully"
SUCCESS_ORGANIZATION_DELETED = "Organization deleted successfully"

# Status Values
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"

# Error Codes
ERROR_CODE_ORG_NOT_FOUND = "ORGANIZATION_NOT_FOUND"
ERROR_CODE_DUPLICATE_NAME = "DUPLICATE_ORGANIZATION_NAME"
ERROR_CODE_INVALID_STATUS = "INVALID_STATUS"
ERROR_CODE_ORG_HAS_DEPENDENCIES = "ORGANIZATION_HAS_DEPENDENCIES"

# Industry Types
INDUSTRY_ECOMMERCE = "Ecommerce"
INDUSTRY_AGENCY = "Agency"
INDUSTRY_RETAIL = "Retail"
```

**RULE 8.7.5: WRONG Constants Pattern (DO NOT DO THIS)**
```python
# INCORRECT: Functions in constants.py
def get_error_message(code: str) -> str:  # WRONG: Functions belong in utils.py
    return ERROR_MESSAGES.get(code, "Unknown error")

# INCORRECT: Computed values
MAX_FILE_SIZE = 2 * 1024 * 1024  # WRONG: Computed value, use config.py or hardcode

# INCORRECT: Database access
ACTIVE_ORGS_COUNT = await get_active_orgs_count()  # WRONG: Database access belongs in repository.py
```

**RULE 8.7.6: Key Principles**
- **Static values only** - no functions, no computed values, no logic
- **UPPER_CASE naming** - follow Python constant naming convention
- **Group by category** - organize constants logically (errors, success, status, etc.)
- **Centralized** - all domain-specific constants in one place
- **Reusable** - import and use across service, router, exceptions

### 8.8 Config (`config.py`)
**RULE 8.8.1: Purpose**
- **Domain-specific configuration** - Settings that vary by environment
- **Environment-based values** - Loaded from `.env` file or environment variables
- **Feature flags** - Enable/disable features per environment
- **Domain-specific defaults** - Default values for domain operations

**RULE 8.8.2: When to Use Config**
- **OPTIONAL** - Only create if module needs domain-specific configuration
- **Use when**: Module has settings that differ between environments (dev, staging, prod)
- **Use when**: Module has feature flags or toggles
- **Use when**: Module has configurable limits, timeouts, or thresholds
- **Don't use**: If all values are static constants (use constants.py instead)

**RULE 8.8.3: What Config SHOULD Contain**
- Environment-based settings (API keys, URLs, timeouts)
- Feature flags (e.g., `ENABLE_LOGO_UPLOAD: bool = True`)
- Configurable limits (e.g., `MAX_LOGO_SIZE_MB: int = 2`)
- Default values (e.g., `DEFAULT_PAGE_SIZE: int = 20`)
- Domain-specific API settings
- Settings loaded from `.env` file

**RULE 8.8.4: What Config MUST NOT Contain**
- **Hardcoded secrets** (use environment variables)
- **Business logic** (use service.py for business logic)
- **Static constants** (use constants.py for static values)
- **Functions** (use utils.py for functions)
- **Database access** (use repository.py for database operations)

**RULE 8.8.5: CORRECT Config Pattern**
```python
# src/organizations/config.py
from pydantic_settings import BaseSettings

class OrganizationSettings(BaseSettings):
    """Organization-specific configuration"""
    # File upload settings
    MAX_LOGO_SIZE_MB: int = 2
    ALLOWED_LOGO_FORMATS: list[str] = ["PNG", "JPEG", "JPG"]
    LOGO_UPLOAD_PATH: str = "/uploads/logos"
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Feature flags
    ENABLE_LOGO_UPLOAD: bool = True
    ENABLE_ORGANIZATION_ANALYTICS: bool = False
    
    # Timeouts and limits
    ORGANIZATION_CREATION_TIMEOUT_SECONDS: int = 30
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_prefix": "ORG_",  # Optional: prefix for env vars
    }

org_settings = OrganizationSettings()
```

**RULE 8.8.6: WRONG Config Pattern (DO NOT DO THIS)**
```python
# INCORRECT: Hardcoded secrets
class OrganizationSettings(BaseSettings):
    API_KEY = "secret-key-12345"  # WRONG: Should be in .env file

# INCORRECT: Business logic
class OrganizationSettings(BaseSettings):
    def validate_org_name(self, name: str) -> bool:  # WRONG: Logic belongs in service.py
        return len(name) > 0

# INCORRECT: Static constants (use constants.py instead)
class OrganizationSettings(BaseSettings):
    STATUS_ACTIVE = "active"  # WRONG: Static constant, use constants.py
```

**RULE 8.8.7: Key Principles**
- **Optional file** - only create if needed
- **Environment-based** - values loaded from .env or environment variables
- **Pydantic BaseSettings** - use pydantic-settings for configuration management
- **Type hints required** - all fields must have type hints
- **Defaults provided** - provide sensible defaults for all settings
- **Separate from constants** - config is for environment-based values, constants.py is for static values

### 8.9 Other Module Files
- `dependencies.py` → Domain-specific dependencies that routers need
  - **CRITICAL:** **MUST NOT** check permissions in dependencies
  - **MUST NOT** use `get_current_user` or `get_current_user_model` in dependencies
  - **MUST** accept `ctx: AuthContext` from router's `require_permission()` dependency
  - **MUST** pass `ctx` to service methods
  - **CORRECT Pattern:**
    ```python
    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.database import get_session
    from src.schemas import AuthContext
    from src.module.service import ResourceService
    from src.module.schemas import ResourceListQuery, ResourceCreate
    
    class ResourceApiDep:
        """API dependency for resource operations"""
        
        def __init__(
            self,
            session: AsyncSession = Depends(get_session),
        ):
            self.service = ResourceService(session)
            self.session = session
        
        async def list_resources(
            self,
            query: ResourceListQuery,
            ctx: AuthContext,
            if_none_match: Optional[str] = None,
        ):
            """List resources - accepts ctx from require_permission dependency"""
            # Permission already validated in router
            return await self.service.list_resources(query, ctx, self.session)
        
        async def create_resource(
            self,
            data: ResourceCreate,
            ctx: AuthContext,
        ):
            """Create resource - accepts ctx from require_permission dependency"""
            # Permission already validated in router
            return await self.service.create_resource(data, ctx)
    ```
- `exceptions.py` → Domain-specific exceptions (consistent with repo structure)
- `utils.py` → Non-business helpers (response normalization, minor transformations)

### 8.10 Swagger Documentation (`documentations/{module}_api_doc.py`)

**RULE 8.10.1: Swagger Documentation Standardization**
- **MUST create a documentation class for each resource module** to centralize Swagger/OpenAPI documentation
- **Purpose**: Keeps Swagger documentation consistent, maintainable, and centralized (not hardcoded in routers)
- **Structure**: Create a documentation class with ClassVar attributes for each endpoint operation
- **Required Fields**: Each endpoint operation MUST have `summary` and `description` fields
- **Flexibility**: Structure can vary (dict, ApiSummary object, custom class) as long as `summary` and `description` are accessible

**RULE 8.10.2: Documentation Class Requirements**
- **Location**: `src/{module}/documentations/{module}_api_doc.py`
- **Class Naming**: `{Resource}ApiDocs` (e.g., `OrganizationApiDocs`, `UserApiDocs`, `AssetGroupApiDocs`)
- **Structure**: Use ClassVar attributes for each endpoint operation (e.g., `create`, `list`, `get`, `update`, `delete`)
- **Required Fields per Operation**:
  * `summary`: Brief, clear purpose statement (e.g., "Purpose of this API is to create a new organization")
  * `description`: Detailed description (can include permissions, usage notes, business rules, etc.)

**RULE 8.10.3: Router Decorator Requirements**
- **MUST use `summary` from documentation class** (not hardcoded strings)
- **MUST use `description` from documentation class** (not hardcoded strings)
- **Pattern**: `summary=ResourceApiDocs.operation_name.<path_to_summary>`
- **Pattern**: `description=ResourceApiDocs.operation_name.<path_to_description>`
- **Exact path depends on implementation structure** (flexible - can be dict access, object attribute, etc.)

**RULE 8.10.4: CORRECT Implementation Examples**

**Example 1 - Using Dictionary Structure:**
```python
# src/organizations/documentations/organization_api_doc.py
from typing import ClassVar

class OrganizationApiDocs:
    """API documentation for Organization endpoints"""
    
    create: ClassVar[dict] = {
        "summary": "Purpose of this API is to create a new organization",
        "description": "Creates a new organization with required details. Only SuperAdmin can create organizations."
    }
    list: ClassVar[dict] = {
        "summary": "Purpose of this API is to list organizations with pagination",
        "description": "Retrieves a paginated list of organizations. Supports filtering, searching, and sorting."
    }
    update: ClassVar[dict] = {
        "summary": "Purpose of this API is to update organization details",
        "description": "Updates organization information. Only SuperAdmin can update organizations."
    }
```

```python
# src/organizations/routers.py
from src.organizations.documentations.organization_api_doc import OrganizationApiDocs

@router.post(
    "",
    response_model=OrganizationRead,
    summary=OrganizationApiDocs.create["summary"],
    description=OrganizationApiDocs.create["description"]
)
async def create_organization(...):
    """Create a new organization"""
    pass
```

**Example 2 - Using ApiSummary Object Structure:**
```python
# src/organizations/documentations/organization_api_doc.py
from typing import ClassVar
from src.core.docs.operation_docs import ApiSummary

class OrganizationApiDocs:
    """API documentation for Organization endpoints"""
    
    create: ClassVar[ApiSummary] = ApiSummary(
        summary="Purpose of this API is to create a new organization",
        description="Creates a new organization with required details. Only SuperAdmin can create organizations."
    )
    update: ClassVar[ApiSummary] = ApiSummary(
        summary="Purpose of this API is to update organization details",
        description="Updates organization information. Only SuperAdmin can update organizations."
    )
```

```python
# src/organizations/routers.py
from src.organizations.documentations.organization_api_doc import OrganizationApiDocs

@router.post(
    "",
    summary=OrganizationApiDocs.create.summary,
    description=OrganizationApiDocs.create.description
)
async def create_organization(...):
    """Create a new organization"""
    pass
```

**RULE 8.10.5: WRONG Patterns (DO NOT DO THIS)**
```python
# WRONG - Hardcoded strings in router decorator
@router.post(
    "",
    response_model=OrganizationRead,
    summary="Create organization",  # WRONG - hardcoded string
    description="Creates a new organization"  # WRONG - hardcoded string
)
async def create_organization(...):
    pass
```

**RULE 8.10.6: Benefits**
- **Centralized Management**: All Swagger documentation in one place per resource
- **Consistency**: Ensures consistent Swagger UI appearance across all endpoints
- **Easy Maintenance**: Update documentation in one place, not scattered across routers
- **Better Developer Experience**: Clear, structured documentation for API consumers
- **Reusability**: Documentation can be reused or extended for other purposes

**RULE 8.10.7: Implementation Flexibility**
- **Structure can vary**: Use dict, ApiSummary object, custom class, or any structure that exposes `summary` and `description`
- **Access pattern can vary**: Use dict access (`["summary"]`), object attributes (`.summary`), or any pattern that works
- **Only requirement**: `summary` and `description` must be accessible and used in router decorators
- **No specific class structure enforced**: Adapt to your project's existing patterns

**RULE 8.10.8: Verification Checklist**
- CORRECT: Documentation class exists in `src/{module}/documentations/{module}_api_doc.py`
- CORRECT: Documentation class has ClassVar attributes for each endpoint operation
- CORRECT: Each operation has both `summary` and `description` fields
- CORRECT: Router decorators use documentation class attributes (not hardcoded strings)
- CORRECT: `summary` and `description` are properly accessible via the chosen structure

**RULE 8.10.9: When to Use**
- **REQUIRED** for ALL API endpoints - every router endpoint MUST use documentation class for `summary` and `description`
- **Rationale**: Centralizes Swagger documentation management, ensures consistency, makes documentation easier to maintain and update

## RULE 9: Python Dependencies / Requirements
### 9.1 Requirements File Structure
- **MUST** have `requirements/base.txt` for production dependencies
- **MUST** have `requirements/dev.txt` for development dependencies
- **Reference:** See `dependencies_validate.md` for complete dependencies management rules

### 9.2 Critical Package Dependencies
- **CRITICAL:** If using `EmailStr` → MUST have `email-validator` in requirements/base.txt
- **CRITICAL:** If using `BaseSettings` → MUST have `pydantic-settings` in requirements/base.txt
- **CRITICAL:** If using `redis.asyncio` → MUST have `redis` in requirements/base.txt
- **CRITICAL:** If using `celery` → MUST have `celery` in requirements/base.txt
- **MUST** verify ALL imports have corresponding packages in requirements

## RULE 10: API Design
### 10.1 RESTful Endpoints
- **MUST** follow "Follow the REST" and response serialization guidance from the repo
- **MUST** use clean RESTful endpoints:
  - `/v1/<user_module_name>` (CRUD)
  - `/v1/<user_module_name>/by-<relation>/{relation_id}` (CRUD + query by relation)
- **MUST** use async routes, Pydantic request/response models, and proper status codes
**CRITICAL NOTE:** Endpoint patterns are STRUCTURAL EXAMPLES ONLY - implement using USER'S ACTUAL MODULE NAMES.

## RULE 11: Docker / Docker-Compose
### 11.1 Dockerfile
- **MUST** create Dockerfile for running `api`, `worker`, and `migrate` services
- **MUST** use Python 3.11-slim base image
- **MUST** install system dependencies (gcc, postgresql-client)
- **MUST** copy requirements and install packages
- **MUST** copy application code
- **MUST** expose port 8000

### 11.2 Docker-Compose Services
- **MUST** include `db` service (Postgres)
- **MUST** include `migrate` service (Alembic migrations - REQUIRED, runs before api/worker)
- **MUST** include `api` service (FastAPI app via Uvicorn)
- **OPTIONAL:** `redis` service (only if user requests Redis)
- **OPTIONAL:** `worker` service (only if user requests Celery)

### 11.3 Docker-Compose Rules
**RULE 11.3.1: Version Field**
- **MUST NOT** include `version` field
- Modern docker-compose (v2+) does not require or use the `version` field
- Including it will generate warnings: "the attribute `version` is obsolete"

**RULE 11.3.2: Port Mapping Strategy**
- **MUST** use non-standard host ports to avoid conflicts with local services
- PostgreSQL: Use `"5433:5432"` (host:container) instead of `"5432:5432"`
- Redis: Use `"6380:6379"` (host:container) instead of `"6379:6379"`
- Container-to-container communication still uses standard ports (5432, 6379) via service names

**RULE 11.3.3: Health Checks**
- **MUST** include health checks for `db` service
- **MUST** include health checks for `redis` service (if Redis is included)
- **MUST** use `depends_on` with `condition: service_healthy` for services that depend on them

**RULE 11.3.4: Service Dependencies**
- **MUST** use `depends_on` with health check conditions for proper startup order
- `migrate` depends on `db` with `condition: service_healthy`
- `api` depends on:
  - `db` with `condition: service_healthy`
  - `migrate` with `condition: service_completed_successfully`
  - `redis` with `condition: service_healthy` (if Redis service exists)
- `worker` depends on (if Celery requested):
  - `db` with `condition: service_healthy`
  - `redis` with `condition: service_healthy` (required - Celery needs Redis)
  - `migrate` with `condition: service_completed_successfully`

**RULE 11.3.5: Environment Variables**
- **MUST** use service names (e.g., `db`, `redis`) for internal container communication
- Database URL: `postgresql+asyncpg://postgres:password@db:5432/dbname`
- Redis URL: `redis://redis:6379/0`
- **CRITICAL: Password Consistency**
  - Password in `DATABASE_URL` MUST match `POSTGRES_PASSWORD` in `db` service environment
  - Username in `DATABASE_URL` MUST match `POSTGRES_USER` in `db` service environment
  - Database name in `DATABASE_URL` MUST match `POSTGRES_DB` in `db` service environment
  - **MUST** verify consistency between db service environment variables and DATABASE_URL

**RULE 11.3.6: Migrate Service**
- **MUST** include `migrate` service that runs `alembic upgrade head`
- **MUST** have `restart: "no"` (runs once and exits)
- **MUST** depend on `db` with `condition: service_healthy`
- **MUST** use same DATABASE_URL environment variable as api/worker
- **CRITICAL:** Without this, application will fail with "relation does not exist" errors

**RULE 11.3.7: Redis Memory Overcommit Warning**
- Redis will show warning: "WARNING Memory overcommit must be enabled!"
- This is a **warning, not an error** - Redis will function normally
- **Best practice:** Add Redis command with memory limits: `redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru --save ""`
- **MUST NOT** use `privileged: true` or `sysctls` in docker-compose (security risk)

### 11.4 Docker-Compose Summary
**MUST-DO items:**
- CORRECT: Omit `version` field
- CORRECT: Use port 5433 for PostgreSQL host mapping (not 5432)
- CORRECT: Use port 6380 for Redis host mapping (not 6379)
- CORRECT: Include health checks for db and redis
- CORRECT: Use `depends_on` with health check conditions
- CORRECT: Configure Redis with memory limits and `--save ""` to minimize warnings
- CORRECT: Ensure DATABASE_URL password/username/dbname matches POSTGRES_PASSWORD/POSTGRES_USER/POSTGRES_DB
- CORRECT: Include `migrate` service that runs before `api` and `worker`

**Reference:** See `docker_validate.md` for complete Docker verification rules.

## RULE 12: RBAC and Permission Management
### 12.1 Permission Checking (CRITICAL - SIMPLIFIED)
- **MANDATORY:** ACM module MUST be included in all projects with authentication
- **Location:** `src/acm/` directory (see `rbac.md` for complete structure)
- **Reference:** See `rbac.md` for complete RBAC implementation guide

### 12.2 Router Permission Pattern (CRITICAL)
- **CORRECT:** Use `require_permission("module.resource", "action")` dependency in router
- **MUST** import `require_permission` from `src.auth.dependencies` (NOT from `src.acm.dependencies`)
- **MUST** use `ctx: AuthContext` instead of `current_user: User`
- **Permission checking is handled by the dependency** - no manual checking needed
- **Example:**
  ```python
  from src.auth.dependencies import require_permission
  from src.schemas import AuthContext
  
  @router.get("/")
  async def list_resources(
      query: ResourceListQuery = Depends(ResourceListQuery),
      ctx: AuthContext = Depends(require_permission("resources.resource", "read_all")),
      api: ResourceApiDep = Depends(ResourceApiDep),
  ):
      # Permission already validated by require_permission() dependency
      # ctx contains user_id, org_id, role_id, role
      # Just delegate to service - no permission checking here
      return await api.list_resources(query, ctx)
  ```

### 12.3 Key Rules
- **Router:** **MUST** use `require_permission("module.resource", "action")` dependency from `src.auth.dependencies`
- **Router:** **MUST** use `ctx: AuthContext` (not `current_user: User`) from `require_permission()` dependency
- **Router:** **MUST NOT** check permissions manually - dependency handles it
- **Service:** **MUST** use `ctx: AuthContext` parameter (not `current_user: User`)
- **Service:** **MUST NOT** check permissions - permission validation done in router via dependency
- **Service:** **MUST** use `ctx.org_id` for organization filtering (None for superadmin = all orgs)
- **Dependencies:** **MUST** accept `ctx: AuthContext` and pass it to service methods
- **Pattern:** Router uses dependency → Dependency checks permission → Returns `AuthContext` → Service receives `ctx`
- **Reference:** See RULE 1.2 for strict architecture rules and `REFACTORING_PATTERN.md` for complete refactoring guide

## RULE 13: Pre-Deployment Checklist
### 13.1 Dependencies Verification
- CORRECT: Check ALL imports in ALL Python files for required packages
- CORRECT: Verify ALL packages used in code are listed in requirements/base.txt
- CORRECT: Special cases: EmailStr → email-validator, BaseSettings → pydantic-settings, redis.asyncio → redis, celery → celery
- **Reference:** See `dependencies_validate.md` for complete dependencies verification rules

### 13.2 Docker-Compose Verification
- CORRECT: `migrate` service exists and runs `alembic upgrade head`
- CORRECT: `migrate` service has `restart: "no"`
- CORRECT: `api` and `worker` depend on `migrate` with `condition: service_completed_successfully`
- CORRECT: All services have correct DATABASE_URL matching db service credentials
- CORRECT: Health checks are configured for `db` and `redis`
- CORRECT: Port mappings use non-standard host ports (5433, 6380)
- CORRECT: NO `version` field in docker-compose.yml
- **Reference:** See `docker_validate.md` for complete Docker verification rules

### 13.3 Database Migration Verification
- CORRECT: **ONLY ONE initial migration file exists** in `alembic/versions/` (check for duplicates)
- CORRECT: Initial migration file has descriptive name (e.g., `001_initial_migration.py`)
- CORRECT: **NO auto-generated duplicate migration files** (e.g., files with hash-based names)
- CORRECT: Initial migration uses UUID for all primary keys (not INTEGER)
- CORRECT: Initial migration uses `postgresql.UUID(as_uuid=True)` for UUID columns
- CORRECT: Timestamp columns use `server_default=sa.text('now()')` (not `default_factory`)
- CORRECT: Alembic env.py properly imports all models
- CORRECT: `down_revision` in initial migration is `None`
- **Reference:** See `database_setup.md` for complete migration verification rules

### 13.4 Code Consistency Verification
- CORRECT: All model primary keys use `UUID` type (not `int`)
- CORRECT: All schema ID fields use `UUID` type (not `int`)
- CORRECT: All router path parameters for IDs use `UUID` type (not `int`)
- CORRECT: All `updated_at` fields in schemas are `Optional[datetime]` (not required)
- CORRECT: All timestamp fields in models use `server_default=func.now()` (not `default_factory`)
- CORRECT: All foreign keys use `UUID` type matching the referenced primary key
- **Reference:** See `module_architecture_validate.md` for complete code consistency patterns

### 13.5 RBAC Implementation Verification
- CORRECT: ACM module exists with all required files
- CORRECT: All routes use `require_permission("module.resource", "action")` dependency
- CORRECT: No permission checking in router handlers or services
- CORRECT: Permission checking handled by `require_permission()` dependency
- **Reference:** See RULE 1.2 for strict architecture rules and RULE 12 for permission patterns

### 13.6 End-to-End Verification
- CORRECT: The codebase can be dropped into a fresh repo
- CORRECT: Running `docker-compose up` should work without manual intervention
- CORRECT: No manual migration commands needed
- CORRECT: No manual dependency installation needed
- CORRECT: API should be accessible at http://localhost:8000/docs after startup
- CORRECT: Database tables should exist automatically
- **Test scenario:** Fresh clone → `docker-compose up` → Should work immediately

### 13.7 File Structure Verification
- CORRECT: All required domain files exist (models, schemas, repository, service, router, dependencies, constants, exceptions, utils, config)
- CORRECT: All `__init__.py` files exist for Python packages
- CORRECT: Alembic configuration files exist (alembic.ini, alembic/env.py, alembic/script.py.mako)
- CORRECT: **ONLY ONE initial migration file exists** in `alembic/versions/` (no duplicates)
- CORRECT: Migration file has descriptive name (not auto-generated hash name)
- CORRECT: Requirements files exist (requirements/base.txt, requirements/dev.txt)
- CORRECT: Docker files exist (Dockerfile, docker-compose.yml)
- CORRECT: Configuration files exist (.gitignore, logging.ini, .env)
- CORRECT: `src/main.py` exists with FastAPI app
- CORRECT: `src/config.py` exists with BaseSettings from `pydantic_settings`
- CORRECT: `alembic/env.py` properly handles async URL conversion

### 13.8 Core Files Usage Verification
- CORRECT: **Repository files (`repository.py`)** are properly used - all database operations go through repository layer
- CORRECT: **Service files (`service.py`)** are properly used - all business logic is in service layer, not in router or repository
- CORRECT: **Utils files (`utils.py`)** are properly used - centralized utilities from `src/utils.py` are imported and used (e.g., ETag functions)
- CORRECT: **Module-specific utils** (`src/{module}/utils.py`) are used only for domain-specific utilities, NOT for core functionality like ETag
- CORRECT: **Constants files (`constants.py`)** are properly used - error messages, success messages, and status values come from constants.py
- CORRECT: **Exceptions files (`exceptions.py`)** are properly used - domain-specific exceptions extend base exception classes from `src.exceptions`
- CORRECT: **Dependencies files (`dependencies.py`)** are properly used - API dependency classes (e.g., `ResourceApiDep`) are used in routers
- CORRECT: **Schemas files (`schemas.py`)** are properly used - request schemas for input validation, response schemas for output structure
- CORRECT: **Documentation files (`documentations/{module}_api_doc.py`)** are properly used - Swagger documentation comes from documentation classes, not hardcoded strings
- CORRECT: **No duplicate functionality** - core utilities (like ETag) are centralized in `src/utils.py`, not duplicated in module-specific utils
- CORRECT: **Proper import patterns** - imports from centralized files (`src/utils.py`, `src.database`, `src.schemas`) are used correctly
- CORRECT: **Repository pattern followed** - routers use API dependencies, which use services, which use repositories (proper layering)
- **Reference:** See RULE 8.4 for repository patterns, RULE 8.5 for service patterns, RULE 8.6 for router patterns, RULE 14 for ETag utilities

### 13.9 Mandatory Final Check
Before marking as complete, mentally simulate:
1. User clones fresh repo
2. User runs `docker-compose up`
3. Everything works without any manual steps
4. If ANY manual step is needed, the codebase is incomplete

## RULE 14: Router Thin Pattern - ETag Header Handling

### 14.1 Router Must Be Thin - Extract ETag Logic to Centralized Utils
**MANDATORY:** Router endpoints MUST NOT contain ETag header setting logic. This logic MUST be extracted to a centralized utility function in `src/utils.py`.

**CRITICAL Rules:**
- Router endpoints should ONLY call service methods and return responses
- ETag and Last-Modified header setting logic MUST be in a centralized helper function in `src/utils.py`
- Router endpoints MUST import and use the helper function from `src.utils` instead of inline header setting
- This keeps routers thin, clean, and maintainable (follows RULE 7)
- **CRITICAL:** ETag utilities are centralized in `src/utils.py` - do NOT create module-specific ETag functions in module `utils.py` files

### 14.2 Centralized ETag Utilities in src/utils.py
**MANDATORY:** ETag utilities are centralized in `src/utils.py`. This file contains:

1. `generate_etag(updated_at: datetime) -> str` - Generates ETag from timestamp
2. `format_last_modified(updated_at: datetime) -> str` - Formats Last-Modified header (RFC 7231)
3. `set_etag_headers_and_return()` - Main helper function for routers (also sets X-Request-ID header)

**Location:** `src/utils.py` (project root, not module-specific)

**CORRECT Pattern:**
```python
# src/utils.py (CENTRALIZED - shared across all modules)
from datetime import datetime
from typing import TypeVar
from fastapi import Response

from src.schemas import StandardResponse

T = TypeVar('T')


def generate_etag(updated_at: datetime) -> str:
    """Generate ETag from updated_at timestamp
    
    Centralized ETag generation function for use across all modules.
    Uses ISO 8601 format with timestamp.
    
    Args:
        updated_at: The datetime when the resource was last updated
        
    Returns:
        ETag string in format: YYYYMMDDTHHMMSSZ
    """
    return updated_at.strftime("%Y%m%dT%H%M%SZ")


def format_last_modified(updated_at: datetime) -> str:
    """Format datetime for Last-Modified header (RFC 7231 format)
    
    Centralized function for formatting Last-Modified HTTP header.
    Uses RFC 7231 format as required by HTTP specification.
    
    Args:
        updated_at: The datetime when the resource was last updated
        
    Returns:
        Formatted datetime string in RFC 7231 format
    """
    return updated_at.strftime("%a, %d %b %Y %H:%M:%S GMT")


def set_etag_headers_and_return(
    response: Response | None,
    result: T,
    message: str,
    request: Optional[Request] = None,
) -> StandardResponse[T]:
    """Set ETag, Last-Modified, and X-Request-ID headers and return StandardResponse
    
    This helper function extracts the header setting logic from routers
    to keep them thin and clean. This is the centralized implementation for
    use across all modules.
    
    Args:
        response: FastAPI Response object (can be None)
        result: The result data from service layer (should have _etag and optionally _last_modified attributes)
        message: Success message for StandardResponse
        request: FastAPI Request object (optional, used to set X-Request-ID header)
        
    Returns:
        StandardResponse with data and message, with headers set if applicable
    """
    # Set ETag and Last-Modified headers
    if response and hasattr(result, '_etag'):
        response.headers["ETag"] = result._etag
        if hasattr(result, '_last_modified'):
            response.headers["Last-Modified"] = format_last_modified(result._last_modified)
    
    # Set X-Request-ID header
    set_request_id_header(request, response)
    
    return StandardResponse(
        data=result,
        message=message,
    )
```

### 14.3 Router Endpoint Pattern
**MANDATORY:** Router endpoints MUST import from centralized `src.utils` and use the helper function:

**CRITICAL REQUIREMENTS:**
- **MUST** include `request: Request = None` parameter in endpoint function signature
- **MUST** pass `request` parameter to ALL `set_etag_headers_and_return()` calls (not optional)
- **MUST** use `set_request_id_header(request, result)` for 304 responses
- **MUST NOT** set headers inline - always use centralized helper functions

**CORRECT Pattern:**
```python
# router.py
from fastapi import APIRouter, Depends, Header, Response, Request, status  # CORRECT: Import Request
from fastapi.responses import Response as FastAPIResponse
from src.utils import set_etag_headers_and_return, set_request_id_header  # CORRECT: Import from centralized src.utils

@router.get(
    "/{resource_id}",
    response_model=StandardResponse[ResourceRead],
    status_code=status.HTTP_200_OK,
    summary="Get resource",
    description="Get resource detail",
)
async def get_resource(
    resource_id: UUID,
    ctx: AuthContext = Depends(require_permission("module.resource", "read")),
    api: ResourceApiDep = Depends(ResourceApiDep),
    request: Request = None,  # CORRECT: Request parameter required for X-Request-ID header
    response: Response = None,
) -> StandardResponse[ResourceRead] | FastAPIResponse:
    """Get resource detail"""
    result = await api.get_resource_by_id(resource_id, ctx)
    
    # Handle 304 response (if applicable)
    if isinstance(result, FastAPIResponse):
        set_request_id_header(request, result)  # CORRECT: Use centralized function for 304 responses
        return result
    
    # CORRECT: Pass request parameter to set_etag_headers_and_return (MANDATORY, not optional)
    return set_etag_headers_and_return(response, result, SUCCESS_RESOURCE_RETRIEVED, request)
```

**WRONG Pattern:**
```python
# INCORRECT: Importing from module-specific utils
from src.module.utils import set_etag_headers_and_return  # WRONG: Should be from src.utils
```

**WRONG Pattern:**
```python
# INCORRECT: Inline ETag header setting in router
@router.get("/{resource_id}")
async def get_resource(...):
    result = await api.get_resource_by_id(resource_id, ctx)
    
    # INCORRECT: Setting headers directly in router
    if response and hasattr(result, '_etag'):
        response.headers["ETag"] = result._etag
        if hasattr(result, '_last_modified'):
            response.headers["Last-Modified"] = format_last_modified(result._last_modified)
    
    return StandardResponse(data=result, message=SUCCESS_MESSAGE)
```

### 14.4 Service Layer ETag Attachment
**MANDATORY:** Service methods MUST attach `_etag` and `_last_modified` attributes to response objects:

**CORRECT Pattern:**
```python
# service.py
from src.utils import generate_etag  # CORRECT: Import from centralized src.utils

async def get_resource_by_id(self, resource_id: UUID, ctx: AuthContext) -> ResourceRead:
    resource = await self.repository.get_by_id(resource_id)
    if not resource:
        raise ResourceNotFound(str(resource_id))
    
    response = ResourceRead(...)
    
    # Attach ETag for router to set header
    response._etag = generate_etag(resource.updated_at)
    response._last_modified = resource.updated_at
    
    return response
```

**WRONG Pattern:**
```python
# INCORRECT: Creating module-specific ETag functions
# service.py
def generate_etag(updated_at: datetime) -> str:  # WRONG: Should import from src.utils
    return updated_at.strftime("%Y%m%dT%H%M%SZ")

# INCORRECT: Importing from module-specific utils
from src.module.utils import generate_etag  # WRONG: Should be from src.utils
```

### 14.5 Endpoints That Require ETag
**MANDATORY:** The following endpoint types MUST have ETag support:
- GET endpoints (single resource and list)
- POST endpoints that create/modify resources
- PATCH/PUT endpoints that update resources
- Endpoints that return data that can be cached

**Endpoints That DON'T Require ETag:**
- DELETE endpoints (204 No Content - no body)
- Bulk operations (not cacheable resources)
- Query endpoints with frequently changing results (if not cacheable)

### 14.6 Verification Checklist
Before marking router as complete, verify:
- [ ] `set_etag_headers_and_return()`, `generate_etag()`, and `format_last_modified()` functions exist in `src/utils.py` (centralized)
- [ ] Router imports ETag utilities from `src.utils` (not from module-specific utils)
- [ ] Router imports `Request` from `fastapi` for request parameter
- [ ] Service imports `generate_etag` from `src.utils` (not from module-specific utils)
- [ ] **ALL router endpoints include `request: Request = None` parameter** (required for X-Request-ID header)
- [ ] **ALL `set_etag_headers_and_return()` calls include `request` parameter** (MANDATORY, not optional)
- [ ] **ALL 304 response handlers use `set_request_id_header(request, result)`** before returning
- [ ] X-Request-ID header is set via `set_etag_headers_and_return()` when `request` parameter is provided (see RULE 15)
- [ ] Service methods attach `_etag` and `_last_modified` to response objects
- [ ] Router endpoints are thin and clean (only call service and return response)
- [ ] No ETag header setting logic in router endpoints (no inline header setting)
- [ ] No duplicate ETag utility functions in module-specific `utils.py` files

### 14.7 Benefits
- **Clean Router:** No repeated header-setting code
- **DRY Principle:** Single source of truth for ETag handling across all modules
- **Centralized Maintenance:** Change ETag logic in one place (`src/utils.py`) - affects all modules
- **Readability:** Endpoints focus on their core logic
- **Type Safety:** Uses TypeVar for proper typing
- **Consistency:** All modules use the same ETag generation and formatting logic
- **No Duplication:** Avoids creating duplicate ETag functions in each module's utils.py

### 14.8 Import Guidelines
**CRITICAL:** All ETag-related imports MUST come from `src.utils`:

**CORRECT Imports:**
```python
# router.py
from src.utils import set_etag_headers_and_return

# service.py or dependencies.py
from src.utils import generate_etag
```

**WRONG Imports:**
```python
# INCORRECT: Module-specific imports
from src.module.utils import set_etag_headers_and_return  # WRONG
from src.module.utils import generate_etag  # WRONG
from src.module.service import generate_etag  # WRONG
```

## RULE 15: Router Thin Pattern - X-Request-ID Header Handling

### 15.1 Router Must Be Thin - Extract X-Request-ID Logic to Centralized Utils
**MANDATORY:** Router endpoints and exception handlers MUST NOT contain X-Request-ID header setting logic. This logic MUST be extracted to centralized utility functions in `src/utils.py`.

**CRITICAL Rules:**
- Router endpoints should ONLY call service methods and return responses
- X-Request-ID header setting logic MUST be in centralized helper functions in `src/utils.py`
- Router endpoints and exception handlers MUST import and use the helper functions from `src.utils` instead of inline header setting
- This keeps routers thin, clean, and maintainable (follows RULE 7)
- **CRITICAL:** X-Request-ID utilities are centralized in `src/utils.py` - do NOT create module-specific X-Request-ID functions in module `utils.py` files

### 15.2 Centralized X-Request-ID Utilities in src/utils.py
**MANDATORY:** X-Request-ID utilities are centralized in `src/utils.py`. This file contains:

1. `set_request_id_header(request: Optional[Request], response: Response | FastAPIResponse | None) -> None` - Sets X-Request-ID header on any response object
2. `set_etag_headers_and_return()` - Main helper function for routers (also sets X-Request-ID header when request is provided)
3. `set_304_response_headers()` - Helper for 304 responses (sets ETag, Last-Modified, and X-Request-ID headers)

**Location:** `src/utils.py` (project root, not module-specific)

**CORRECT Pattern:**
```python
# src/utils.py (CENTRALIZED - shared across all modules)
from typing import Optional, TypeVar
from fastapi import Response, Request
from fastapi.responses import Response as FastAPIResponse

from src.schemas import StandardResponse

T = TypeVar('T')


def set_request_id_header(
    request: Optional[Request],
    response: Response | FastAPIResponse | None,
) -> None:
    """Set X-Request-ID header on response from request state
    
    Centralized function for setting X-Request-ID header on responses.
    This ensures the header is set consistently across all endpoints,
    even when middleware might not handle edge cases (e.g., 304 responses).
    
    Args:
        request: FastAPI Request object (can be None)
        response: FastAPI Response or FastAPIResponse object (can be None)
    """
    if request and response:
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            response.headers["X-Request-ID"] = request_id


def set_304_response_headers(
    request: Optional[Request],
    response: FastAPIResponse,
    etag: str,
    last_modified: Optional[datetime] = None,
) -> FastAPIResponse:
    """Set headers for 304 Not Modified response
    
    Centralized function for setting headers on 304 responses.
    Sets ETag, Last-Modified (if provided), and X-Request-ID headers.
    
    Args:
        request: FastAPI Request object (can be None)
        response: FastAPIResponse object (304 response)
        etag: ETag value to set
        last_modified: Optional datetime for Last-Modified header
        
    Returns:
        FastAPIResponse with headers set
    """
    response.headers["ETag"] = etag
    if last_modified:
        response.headers["Last-Modified"] = format_last_modified(last_modified)
    set_request_id_header(request, response)
    return response
```

### 15.3 Router Endpoint Pattern
**MANDATORY:** Router endpoints MUST import from centralized `src.utils` and use the helper functions:

**CORRECT Pattern:**
```python
# router.py
from src.utils import set_etag_headers_and_return, set_request_id_header  # CORRECT: Import from centralized src.utils

@router.get(
    "/{resource_id}",
    response_model=StandardResponse[ResourceRead],
    status_code=status.HTTP_200_OK,
    summary="Get resource",
    description="Get resource detail",
)
async def get_resource(
    resource_id: UUID,
    ctx: AuthContext = Depends(require_permission("module.resource", "read")),
    api: ResourceApiDep = Depends(ResourceApiDep),
    request: Request = None,
    response: Response = None,
) -> StandardResponse[ResourceRead] | FastAPIResponse:
    """Get resource detail"""
    result = await api.get_resource_by_id(resource_id, ctx)
    
    # Handle 304 response
    if isinstance(result, FastAPIResponse):
        set_request_id_header(request, result)  # CORRECT: Use centralized function
        return result
    
    return set_etag_headers_and_return(response, result, SUCCESS_RESOURCE_RETRIEVED, request)  # CORRECT: Pass request parameter
```

**WRONG Pattern:**
```python
# INCORRECT: Manual X-Request-ID header setting in router
@router.get("/{resource_id}")
async def get_resource(
    request: Request = None,
    response: Response = None,
    ...
):
    result = await api.get_resource_by_id(resource_id, ctx)
    
    # INCORRECT: Setting X-Request-ID header directly in router
    if request and response:
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            response.headers["X-Request-ID"] = request_id
    
    return StandardResponse(data=result, message=SUCCESS_MESSAGE)
```

### 15.4 Exception Handler Pattern
**MANDATORY:** Exception handlers MUST use the centralized `set_request_id_header()` function:

**CORRECT Pattern:**
```python
# exceptions.py
from src.utils import set_request_id_header  # CORRECT: Import from centralized src.utils

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error": error_info.model_dump(),
            "message": exc.message,
        },
    )
    
    # CORRECT: Use centralized function
    set_request_id_header(request, response)
    
    return response
```

**WRONG Pattern:**
```python
# INCORRECT: Manual X-Request-ID header setting in exception handler
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)  # INCORRECT: Manual extraction
    
    response = JSONResponse(...)
    
    # INCORRECT: Setting X-Request-ID header directly
    if request_id:
        response.headers["X-Request-ID"] = request_id
    
    return response
```

### 15.5 Integration with ETag Helper
**MANDATORY:** The `set_etag_headers_and_return()` function automatically sets X-Request-ID header when `request` parameter is provided:

**CORRECT Pattern:**
```python
# router.py
@router.post("")
async def create_resource(
    data: ResourceCreate,
    ctx: AuthContext = Depends(require_permission("module.resource", "create")),
    api: ResourceApiDep = Depends(ResourceApiDep),
    request: Request = None,
    response: Response = None,
) -> StandardResponse[ResourceRead]:
    """Create a new resource"""
    result = await api.create_resource(data, ctx)
    
    # CORRECT: set_etag_headers_and_return automatically sets X-Request-ID when request is provided
    return set_etag_headers_and_return(response, result, SUCCESS_RESOURCE_CREATED, request)
```

### 15.6 Verification Checklist
Before marking router or exception handler as complete, verify:
- [ ] `set_request_id_header()` function exists in `src/utils.py` (centralized)
- [ ] `set_etag_headers_and_return()` accepts `request` parameter and sets X-Request-ID (parameter is MANDATORY, not optional)
- [ ] Router imports `Request` from `fastapi` for request parameter
- [ ] Router imports X-Request-ID utilities from `src.utils` (not from module-specific utils)
- [ ] Exception handlers import `set_request_id_header` from `src.utils` (not from module-specific utils)
- [ ] **ALL router endpoints include `request: Request = None` parameter** (required for X-Request-ID header)
- [ ] **ALL `set_etag_headers_and_return()` calls include `request` parameter** (MANDATORY - must be passed, even if None)
- [ ] **ALL 304 response handlers use `set_request_id_header(request, result)`** before returning (no inline X-Request-ID setting)
- [ ] All exception handlers use `set_request_id_header()` (no inline X-Request-ID setting)
- [ ] Router endpoints are thin and clean (only call service and return response)
- [ ] No X-Request-ID header setting logic in router endpoints or exception handlers (no inline header setting)
- [ ] No duplicate X-Request-ID utility functions in module-specific `utils.py` files

### 15.7 Benefits
- **Clean Router:** No repeated X-Request-ID header-setting code
- **DRY Principle:** Single source of truth for X-Request-ID handling across all modules
- **Centralized Maintenance:** Change X-Request-ID logic in one place (`src/utils.py`) - affects all modules
- **Readability:** Endpoints focus on their core logic
- **Consistency:** All modules use the same X-Request-ID header setting logic
- **No Duplication:** Avoids creating duplicate X-Request-ID functions in each module's utils.py
- **Exception Handling:** Consistent X-Request-ID header setting in all error responses

### 15.8 Import Guidelines
**CRITICAL:** All X-Request-ID-related imports MUST come from `src.utils`:

**CORRECT Imports:**
```python
# router.py
from src.utils import set_etag_headers_and_return, set_request_id_header

# exceptions.py
from src.utils import set_request_id_header
```

**WRONG Imports:**
```python
# INCORRECT: Module-specific imports
from src.module.utils import set_request_id_header  # WRONG
from src.module.exceptions import set_request_id_header  # WRONG
```

## RULE 16: Output Format

### 16.1 Before Generating Code
**MUST ASK user for ALL required information:**
Reference it from RULE 1.2

**CRITICAL: DO NOT use example names like "organizations" or "members" unless explicitly requested by user**
- These are STRUCTURAL PATTERN EXAMPLES ONLY - understand the pattern, use user's actual names
- DO NOT use placeholder values like "password", "dbname" - always ask user for actual values

### 16.2 Code Generation Order
1. FIRST show the final folder structure
2. THEN provide all important code files:
   - src/config.py
   - src/database.py
   - src/infra/cache_redis.py (if Redis requested)
   - src/infra/celery_app.py (if Celery requested)
   - src/<user_requested_modules>/* (router, schemas, models, dependencies, config, constants, exceptions, service, utils)
   - src/api/router.py
   - src/main.py
   - docker-compose.yml
3. All code must be **complete and consistent**, with valid imports
4. Do NOT include commentary or explanations unless explicitly asked
5. Do NOT generate anything that conflicts with the practices in `fastapi-best-practices`
6. **CRITICAL:** Only develop modules that the user explicitly requests

## Summary

This guide provides rule-based instructions for creating FastAPI backend projects. Each rule is numbered and contains specific, actionable requirements. Follow rules in order and refer to referenced validation files for detailed implementation patterns.

**Key Principles:**
- Request schemas define input validation
- Response schemas define output structure
- Business logic goes in service.py
- Router is thin and delegates to service
- Clear separation: Router → Request Schema → Service → Response Schema
- All imports at top, not inside function or class
- **Soft delete support** - ALL models (except audit_logs) MUST have `deleted_at` field with soft delete filtering in repositories (RULE 8.2.4, RULE 8.4.6.1)
- ETag header setting logic in centralized `src/utils.py` helper function (RULE 14) - imports from `src.utils`, not module-specific utils
- X-Request-ID header setting logic in centralized `src/utils.py` helper functions (RULE 15) - imports from `src.utils`, not module-specific utils
**Strict Rules Summary (See RULE 1.2 for details):**
- Router MUST be thin - NO business logic, only delegates to service
- Permission checking via `require_permission("module.resource", "action")` dependency from `src.auth.dependencies` only
- Router MUST use `ctx: AuthContext` (not `current_user: User`) from `require_permission()` dependency
- Service MUST use `ctx: AuthContext` parameter (not `current_user: User`)
- Service uses `ctx.org_id` for organization filtering (None for superadmin = all orgs)
- NO multiple DB queries in router - ASK user before implementation if needed
- Role information from `ctx.role` (from JWT token)
- NO permission checking in router handlers or services
- **Reference:** See `REFACTORING_PATTERN.md` for complete guide on using `AuthContext` instead of `User` model
