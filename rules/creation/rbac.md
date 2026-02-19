# RBAC Permission Management with ACM Module

**Purpose:** Core guide for implementing centralized RBAC (Role-Based Access Control) using the ACM (Access Control Management) module.

**Reference:** See `rbac-implementation-spec.md` in `cursor/guidelines/` for detailed implementation guide.

---

## RULE 1: Core Principle

**All RBAC logic MUST be centralized in the `acm` (Access Control Management) module. Permission validation happens ONLY in routers via `require_permission()` from `src/auth/dependencies.py`. Services should NEVER check permissions - they only read permissions for data scope determination.**

**Architecture Flow:**
- **Router** → `require_permission()` (auth/dependencies) → `PermissionClient` (auth/client) → `acm_require_permission()` (acm/dependencies) → `PermissionCache` (acm/permission_cache)
- This layered approach allows switching between local ACM and remote permission service via `PermissionClient` Protocol

---

## RULE 2: ACM Module Structure

### 2.1 Module Location
```
src/acm/
├── __init__.py              # Public API - exports all ACM functions
├── permissions.py           # Permission checking functions
├── permission_cache.py      # Redis cache operations
├── dependencies.py          # FastAPI dependencies (require_permission)
└── utils.py                 # Utility functions and scope helpers
```

### 2.2 Module Responsibilities

| File | Responsibility | Key Exports |
|------|---------------|-------------|
| `permissions.py` | Core permission validation logic (works with `Set[str]`) | `check_permission(permissions_set: Set[str], action: str)` - checks exact permission string match |
| `permission_cache.py` | Redis SET caching for user permissions via `PermissionCache` class | `PermissionCache.has_permission()`, `PermissionCache.get_user_permissions()`, `PermissionCache.set_user_permissions()`, `PermissionCache.invalidate_user_permissions()` |
| `dependencies.py` | ACM-level permission checking function | `acm_require_permission()` - called by `PermissionClient` to check permissions |
| `utils.py` | RBAC utility functions and scope helpers | `flatten_permissions()`, `get_cache_key()` |
| `__init__.py` | Public API - exports all ACM functions | All public functions from above modules |

### 2.3 Auth Module Integration

**Location:** `src/auth/`

| File | Responsibility | Key Exports |
|------|---------------|-------------|
| `dependencies.py` | FastAPI dependency factory for permission checking | `require_permission(module: str, action: str)` - **PRIMARY dependency for all routes** |
| `client.py` | Permission client abstraction (Protocol) | `PermissionClient` Protocol, `LocalPermissionClient`, `RemotePermissionClient`, `get_permission_client()` |

**Important:** `require_permission()` is in `src/auth/dependencies.py`, NOT in `src/acm/dependencies.py`. It uses `PermissionClient` Protocol to delegate to either local ACM or remote service.

**Important Notes:**
- `check_permission()` now accepts `Set[str]` (not `Dict[str, Any]`)
- All cache functions return `Set[str]` of permission strings
- System permissions are **NOT** cached in Redis SET
- All cache functions require `org_id` parameter

### 2.4 When to Create ACM Module
- **MANDATORY:** ACM module MUST be created for all projects with authentication
- **MUST** be created before implementing any domain modules that need permission checking
- **MUST** be included in project structure from the start

---

## RULE 3: Permission Checking Pattern

### 3.1 The Golden Rule

**✅ DO: Check permissions in router via `require_permission()`**  
**❌ DON'T: Check permissions in services, dependencies, or anywhere else**

### 3.2 Router Pattern (CORRECT)

```python
from fastapi import APIRouter, Depends
from src.auth.dependencies import require_permission
from src.schemas import AuthContext

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/")
async def list_users(
    query: UserListQuery = Depends(UserListQuery),
    ctx: AuthContext = Depends(require_permission("users.user", "read_all")),
    api: UserApiDep = Depends(UserApiDep),
):
    """List users - permission validated by require_permission()"""
    # Permission already checked - ctx contains user_id, org_id, role_id, role
    return await api.list_users(query, ctx)

@router.get("/{user_id}")
async def get_user(
    user_id: UUID,
    ctx: AuthContext = Depends(require_permission("users.user", "read")),
    api: UserApiDep = Depends(UserApiDep),
):
    """Get user - permission validated by require_permission()"""
    return await api.get_user(user_id, ctx)
```

**Key Points:**
- ✅ Permission check happens in `Depends(require_permission(...))`
- ✅ Returns `AuthContext` (not `User` model) - contains `user_id`, `org_id`, `role_id`, `role`
- ✅ Import `require_permission` from `src.auth.dependencies` (NOT from `src.acm.dependencies`)
- ✅ Permission format: `module.action` (e.g., `"users.user.read_all"`, `"users.user.read"`)
- ✅ No permission checking logic in route handler
- ✅ All routes that need permission checking MUST use `require_permission()`
- ✅ Pass `ctx: AuthContext` to service methods (not `current_user: User`)

### 3.3 Service Pattern (CORRECT)

```python
from src.schemas import AuthContext
from src.auth.dependencies import get_current_user_model
from src.users.models import User

class UserService:
    async def list_users(
        self,
        query: UserListQuery,
        ctx: AuthContext,
        session: AsyncSession,
    ) -> UserPaginatedResponse:
        """
        List users with pagination.
        
        Permission validation already done in router via require_permission().
        This method only determines data scope based on permissions.
        """
        # Permission validation already done in router via require_permission()
        # If you need User model with permissions_json, fetch it:
        user = await get_current_user_model(ctx, session)
        permissions_json = user.permissions_json or {}
        
        # Determine data scope based on permissions (not validation, just reading scope)
        # Use ctx.org_id for organization filtering (can be None for superadmin)
        org_id_filter = ctx.org_id  # None means superadmin (can see all)
        
        # Get users from repository with scope filter
        items, total = await self.repository.list_with_pagination(
            org_id_filter=org_id_filter,
            # ... other params
        )
        
        return UserPaginatedResponse(items=items, total=total)
```

**Key Points:**
- ✅ NO `check_permission()` or `check_system_permission()` calls
- ✅ Receives `ctx: AuthContext` from router (contains `user_id`, `org_id`, `role_id`, `role`)
- ✅ If you need `User` model with `permissions_json`, use `get_current_user_model(ctx, session)`
- ✅ Use `ctx.org_id` for organization filtering (None for superadmin means all orgs)
- ✅ Comments clearly state: "Permission validation already done in router"
- ✅ Only determines data scope (what data user can see), not access validation

### 3.4 Service Pattern (WRONG - DON'T DO THIS)

```python
# ❌ WRONG: Checking permissions in service
class ResourceService:
    async def list_resources(self, query: ResourceListQuery, current_user: User):
        # ❌ DON'T check permissions here
        if not check_permission(current_user.permissions_json, "module.resource", "read"):
            raise ForbiddenError(...)
        
        # ❌ DON'T use check_system_permission in service
        if not check_system_permission(current_user.permissions_json, "cross_org_access"):
            # ...
```

**Why This Is Wrong:**
- Permission validation should happen at the router level
- Services should focus on business logic, not access control
- Violates separation of concerns

### 3.5 Dependency Pattern (CORRECT)

```python
from fastapi import Depends
from src.schemas import AuthContext
from src.database import get_session

class UserApiDep:
    """API dependency for user operations"""
    
    def __init__(
        self,
        session: AsyncSession = Depends(get_session),
    ):
        self.service = UserService(session)
    
    async def list_users(self, query: UserListQuery, ctx: AuthContext):
        """List users - accepts ctx from require_permission dependency"""
        # Permission already validated in router
        # Just pass ctx to service
        return await self.service.list_users(query, ctx, self.session)
```

**Key Points:**
- ✅ NO permission checking in dependency class
- ✅ Permission check happens in router via `require_permission()`
- ✅ Accepts `ctx: AuthContext` from router's `require_permission()` dependency
- ✅ Pass `ctx` to service methods (service can fetch User model if needed)

---

## RULE 4: require_permission() Dependency

### 4.1 Usage Pattern

**Location:** `src/auth/dependencies.py` (NOT in `src/acm/dependencies.py`)

**Signature:**
```python
def require_permission(module: str, action: str):
    """
    FastAPI dependency factory for permission checking.
    
    - Authenticates the user via JWT token validation.
    - Delegates permission evaluation to the configured PermissionClient
      (local ACM vs remote service).
    
    Usage:
        @router.get("/users/{user_id}")
        async def get_user(
            user_id: UUID,
            ctx: AuthContext = Depends(require_permission("users.user", "read")),
        ):
            # User has permission, proceed with ctx containing user_id, org_id, role_id, role
            pass
    
    Args:
        module: Permission module (e.g., "users", "organizations")
        action: Permission action (e.g., "read", "read_all", "create", "update")
    
    Returns:
        Dependency function that validates permission and returns AuthContext
    
    Raises:
        PermissionDeniedError: If user doesn't have the required permission
    """
```

**Returns:** `AuthContext` (dataclass with `user_id`, `org_id`, `role_id`, `role`)
- `org_id` can be `None` for superadmin users
- Import from `src.auth.dependencies`, NOT from `src.acm.dependencies`

### 4.2 Common Permission Patterns

**Permission Format:** `{module}.{module_name}.{action}`

| Module | Module Name | Actions | Full Permission String | Description |
|--------|-------------|---------|------------------------|-------------|
| `users` | `user` | `read`, `read_all`, `invite`, `invite_all`, `update`, `update_all`, `remove`, `remove_all` | `users.user.read`, `users.user.read_all`, etc. | User management |
| `organizations` | `organization` | `read`, `read_all`, `create`, `update`, `update_all`, `delete` | `organizations.organization.read`, etc. | Organization management |
| `auth` | `role` | `read`, `read_all`, `create`, `update`, `update_all`, `delete` | `auth.role.read`, etc. | Role management |
| `audit` | `event` | `read`, `read_all` | `audit.event.read`, etc. | Audit log access |

**Usage in Router:**
```python
# Pass module and action separately
ctx: AuthContext = Depends(require_permission("users.user", "read_all"))
# Internally combines to: "users.user.read_all"
```

### 4.3 Implementation Flow

**Complete Flow: Router → Auth → Client → ACM**

1. **Router** calls `require_permission("users.user", "read")` dependency
2. **Auth Dependencies** (`src/auth/dependencies.py`):
   - Validates JWT token via `get_current_user()` → returns `AuthContext`
   - Gets `PermissionClient` via `get_permission_client()` dependency
   - Calls `perm_client.has_permission(action="users.user.read", ctx=ctx, session=session)`
3. **Auth Client** (`src/auth/client.py`):
   - `LocalPermissionClient.has_permission()` parses `"users.user.read"` → splits to `module="users.user"`, `action="read"`
   - Calls `acm_require_permission(module="users.user", action="read", user_id, org_id, session, request)`
4. **ACM Dependencies** (`src/acm/dependencies.py`):
   - Calls `PermissionCache.has_permission(user_id, org_id, permission="users.user.read", session)`
5. **Permission Cache** (`src/acm/permission_cache.py`):
   - Checks Redis SET using `SISMEMBER` for fast lookup
   - On cache miss → fetches from DB, flattens `permissions_json`, caches in Redis
   - Calls `check_permission(permissions_set, "users.user.read")`
6. **Permissions** (`src/acm/permissions.py`):
   - Checks if `"users.user.read"` exists in `permissions_set` (exact match)
7. **Result:**
   - If granted → return `True` → `AuthContext` returned to router
   - If denied → raise `PermissionDeniedError` (403 status)

**Permission Check with SET Format:**
```python
# In PermissionCache.has_permission():
cache_key = get_cache_key(user_id, org_id)  # e.g., "user:permissions:{org_id}:{user_id}"

# Try Redis SISMEMBER first (fast O(1) check)
in_cache = await redis_client.sismember(cache_key, "users.user.read")
if in_cache:
    return True

# Cache miss → fetch from DB
permissions_set, user = await self._get_from_db(user_id, session)
# permissions_set = {"users.user.read_all", "users.user.update", ...}

# Check exact permission string
return check_permission(permissions_set, "users.user.read")
# check_permission() does: "users.user.read" in permissions_set
```

**Key Points:**
- `check_permission(permissions_set: Set[str], action: str)` takes full permission string (e.g., `"users.user.read"`)
- Permission strings are in format: `"{module}.{module_name}.{action}"` (e.g., `"users.user.read_all"`)
- System permissions are **NOT** included in the SET (per requirements)
- Uses Redis `SISMEMBER` for O(1) permission checks (no need to fetch entire SET)
- `org_id` comes from `AuthContext` (extracted from JWT token, can be `None` for superadmin)

### 4.4 Complete Permission Checking Flow Diagram

**Flow: Router → Auth Dependencies → Permission Client → ACM Module → Permission Check**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ROUTER ENDPOINT                                  │
│  @router.get("/users/{user_id}")                                         │
│  async def get_user(                                                     │
│      user_id: UUID,                                                      │
│      ctx: AuthContext = Depends(require_permission("users.user", "read"))│
│  )                                                                       │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             │ FastAPI calls dependency
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              require_permission() DEPENDENCY FACTORY                     │
│              (src/auth/dependencies.py)                                 │
│                                                                          │
│  def require_permission(module: str, action: str):                     │
│      async def permission_checker(                                       │
│          ctx: AuthContext = Depends(get_current_user),                  │
│          session: AsyncSession = Depends(get_session),                   │
│          perm_client: PermissionClient = Depends(get_permission_client)  │
│      ) -> AuthContext:                                                  │
│          permission_value = f"{module}.{action}"  # "users.user.read"   │
│          allowed = await perm_client.has_permission(                    │
│              action=permission_value, ctx=ctx, session=session          │
│          )                                                               │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             │ Step 1: Get PermissionClient
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              get_permission_client()                                     │
│              (src/auth/client.py)                                       │
│                                                                          │
│  mode = os.getenv("ACM_MODE", "local")                                   │
│  if mode == "local":                                                     │
│      return LocalPermissionClient()                                      │
│  else:                                                                    │
│      return RemotePermissionClient(base_url)                             │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             │ Step 2: LocalPermissionClient.has_permission()
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              LocalPermissionClient.has_permission()                      │
│              (src/auth/client.py)                                        │
│                                                                          │
│  # Parse "users.user.read" → module="users.user", action="read"        │
│  parts = action.split(".", 1)  # ["users.user", "read"]                │
│  module, action_name = parts                                             │
│                                                                          │
│  await acm_require_permission(                                          │
│      module="users.user",                                                │
│      action="read",                                                      │
│      user_id=ctx.user_id,                                                │
│      org_id=ctx.org_id,  # Can be None for superadmin                   │
│      session=session,                                                    │
│      request=request                                                     │
│  )                                                                       │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             │ Step 3: ACM permission check
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              acm_require_permission()                                    │
│              (src/acm/dependencies.py)                                    │
│                                                                          │
│  permission_value = f"{module}.{action}"  # "users.user.read"         │
│  has_perm = await PermissionCache.has_permission(                       │
│      user_id=user_id,                                                    │
│      org_id=org_id,                                                      │
│      permission="users.user.read",                                      │
│      session=session                                                     │
│  )                                                                       │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             │ Step 4: PermissionCache.has_permission()
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              PermissionCache.has_permission()                            │
│              (src/acm/permission_cache.py)                              │
│                                                                          │
│  cache_key = get_cache_key(user_id, org_id)                             │
│  # "user:permissions:{org_id}:{user_id}"                               │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────┐        │
│  │ 1. Try Redis SISMEMBER (O(1) check)                         │        │
│  │    in_cache = await redis_client.sismember(                 │        │
│  │        cache_key, "users.user.read"                          │        │
│  │    )                                                          │        │
│  │    if in_cache: return True                                 │        │
│  └───────────────────────┬────────────────────────────────────┘        │
│                          │                                              │
│                          ├─── Cache HIT ──────────────────────────────┐ │
│                          │                                            │ │
│                          └─── Cache MISS ────────────────────────────┐ │ │
│                                                                    │ │ │
│  ┌──────────────────────────────────────────────────────────────┐ │ │ │
│  │ 2. Fallback to Database                                      │ │ │ │
│  │    permissions_set, user = await self._get_from_db(          │ │ │ │
│  │        user_id, session                                      │ │ │ │
│  │    )                                                          │ │ │ │
│  │    → SELECT permissions_json FROM users WHERE id = user_id  │ │ │ │
│  │    → flatten_permissions(permissions_json)                  │ │ │ │
│  │    → Returns Set[str]                                       │ │ │ │
│  └───────────────────────┬────────────────────────────────────┘ │ │ │
│                          │                                      │ │ │
│  ┌──────────────────────────────────────────────────────────────┐ │ │ │
│  │ 3. Cache for Next Request (best effort)                     │ │ │ │
│  │    await self._update_redis(user_id, permissions_set, org_id)│ │ │ │
│  │    → DEL user:permissions:{org_id}:{user_id}                │ │ │ │
│  │    → SADD user:permissions:{org_id}:{user_id} {perms...}   │ │ │ │
│  └───────────────────────┬────────────────────────────────────┘ │ │ │
│                          │                                      │ │ │
│  ┌──────────────────────────────────────────────────────────────┐ │ │ │
│  │ 4. Check Permission                                           │ │ │ │
│  │    return check_permission(permissions_set, "users.user.read")│ │ │ │
│  └───────────────────────┬────────────────────────────────────┘ │ │ │
│                          │                                      │ │ │
│                          └──────────────────────────────────────┘ │ │
│                                                                    │ │
│  Result: True or False ───────────────────────────────────────────┘ │
│  Example permissions_set: {"users.user.read_all", "users.user.update"}│
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Step 5: check_permission()
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              check_permission(permissions_set, action)                    │
│              (src/acm/permissions.py)                                    │
│                                                                          │
│  # Exact match check                                                     │
│  result = "users.user.read" in permissions_set                          │
│  # Example: "users.user.read" in {"users.user.read_all", ...}          │
│  # Returns: False (exact match only, no _all fallback)                   │
│                                                                          │
│  Result: True or False                                                   │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ├─── Permission GRANTED ────────────────────┐
                             │                                            │
                             │                                            ▼
                             │                          ┌─────────────────────────────┐
                             │                          │  Return AuthContext        │
                             │                          │  Continue to route handler  │
                             │                          │  ctx contains:             │
                             │                          │  - user_id                  │
                             │                          │  - org_id (can be None)     │
                             │                          │  - role_id                  │
                             │                          │  - role                     │
                             │                          └─────────────────────────────┘
                             │
                             └─── Permission DENIED ──────────────────────┐
                                                                          │
                                                                          ▼
                                                          ┌─────────────────────────────┐
                                                          │  Raise PermissionDeniedError│
                                                          │  Status: 403                │
                                                          │  Message: "Permission denied"│
                                                          │  Request stops here          │
                                                          └─────────────────────────────┘
```

**Key Points in the Flow:**

1. **Router Level**: FastAPI automatically calls `require_permission()` dependency before route handler executes

2. **Auth Layer**: `require_permission()` in `src/auth/dependencies.py` validates JWT token and gets `AuthContext`

3. **Client Abstraction**: `PermissionClient` Protocol allows switching between local ACM and remote service

4. **Permission Retrieval**: 
   - First tries Redis `SISMEMBER` for O(1) permission check (no need to fetch entire SET)
   - Falls back to database if cache miss
   - Caches permissions for future requests

5. **Permission Checking**: 
   - Uses `Set[str]` for O(1) lookup performance
   - Exact match only (e.g., `"users.user.read"` must exist in set)
   - No automatic `_all` fallback in `check_permission()` (handled at permission assignment level)

6. **Result**: 
   - **Granted**: Returns `AuthContext`, route handler executes
   - **Denied**: Raises `PermissionDeniedError`, request stops

**Cache Key Examples:**
- Regular user: `user:permissions:123e4567-e89b-12d3-a456-426614174000:8f0c423c-00b9-47fb-9da8-abe85934fbb4`
- Superadmin: `user:permissions:superadmin:8f0c423c-00b9-47fb-9da8-abe85934fbb4`

**Permission Set Example:**
```
{"users.user.read_all", "users.user.update", "organizations.organization.read"}
```

---

## RULE 5: AuthContext Structure

### 5.1 AuthContext Definition

**Location:** `src/schemas.py`

**Structure:**
```python
@dataclass
class AuthContext:
    """User identity and role context extracted from JWT"""
    user_id: UUID
    org_id: Optional[UUID]  # None for superadmin users
    role_id: UUID
    role: str
```

### 5.2 Usage in Routers

```python
from src.schemas import AuthContext
from src.auth.dependencies import require_permission

@router.get("/users")
async def list_users(
    ctx: AuthContext = Depends(require_permission("users.user", "read_all")),
):
    # ctx.user_id - User's UUID
    # ctx.org_id - Organization UUID (None for superadmin)
    # ctx.role_id - Role's UUID
    # ctx.role - Role name (e.g., "SuperAdmin", "OrganizationAdmin")
    
    # Use ctx.org_id for organization filtering
    # None means superadmin can see all organizations
    org_id_filter = ctx.org_id  # None = all orgs (superadmin)
```

### 5.3 Getting User Model When Needed

If your service needs the full `User` model with `permissions_json`:

```python
from src.auth.dependencies import get_current_user_model
from src.schemas import AuthContext

async def list_users(
    self,
    ctx: AuthContext,
    session: AsyncSession,
):
    # Fetch User model if you need permissions_json or other User attributes
    user = await get_current_user_model(ctx, session)
    permissions_json = user.permissions_json or {}
    
    # Now you can read permissions for data scope determination
    # ...
```

---

## RULE 6: Scope Helper Functions

### 6.1 Purpose

**Location:** `src/acm/utils.py`

**Purpose:** Utility functions for permission flattening and cache key generation

**Important:** Services primarily use `ctx.org_id` from `AuthContext` for organization filtering. If you need to read permissions JSON, fetch the User model first.

### 6.2 Available Utility Functions

```python
def flatten_permissions(permissions_json: Dict[str, Any]) -> Set[str]:
    """
    Flatten permissions JSON structure to a set of permission strings.
    
    Converts nested structure:
    {
        "modules": {
            "users": {
                "user": {
                    "read_all": True,
                    "update": True
                }
            }
        }
    }
    
    To: {"users.user.read_all", "users.user.update"}
    """

def get_cache_key(user_id: UUID, org_id: Optional[UUID] = None) -> str:
    """
    Generate cache key for user permissions.
    
    Returns:
        "user:permissions:{org_id}:{user_id}" or
        "user:permissions:superadmin:{user_id}" (if org_id is None)
    """
```

### 6.3 Usage in Services

**Primary Pattern (Recommended):**
```python
# ✅ CORRECT: Use ctx.org_id for organization filtering
async def list_users(
    self,
    ctx: AuthContext,
    session: AsyncSession,
):
    # ctx.org_id is None for superadmin (can see all orgs)
    # ctx.org_id is UUID for regular users (can only see their org)
    org_id_filter = ctx.org_id  # None = all orgs, UUID = specific org
    
    items, total = await self.repository.list_with_pagination(
        org_id_filter=org_id_filter,
        # ... other params
    )
```

**Alternative Pattern (If You Need to Read Permissions JSON):**
```python
# ✅ CORRECT: Fetch User model if you need permissions_json
from src.auth.dependencies import get_current_user_model

async def list_users(
    self,
    ctx: AuthContext,
    session: AsyncSession,
):
    # Fetch User model if you need to read permissions_json
    user = await get_current_user_model(ctx, session)
    permissions_json = user.permissions_json or {}
    
    # Read permissions for data scope (not validation)
    # Example: Check if user has read_all permission
    # (You would implement your own scope reading logic here)
    
    # Use ctx.org_id for organization filtering
    org_id_filter = ctx.org_id
    # ...
```

---

## RULE 7: Cache Strategy

### 7.1 Cache Design

- **Cache Key Pattern:** `user:permissions:{org_id}:{user_id}`
- **SuperAdmin Key Pattern:** `user:permissions:superadmin:{user_id}` (when `org_id` is `None`)
- **TTL:** None (infinite) - invalidate explicitly
- **Fallback:** Always fall back to DB if Redis fails
- **Storage:** Redis SET containing dot-separated permission strings (e.g., `org.user.read`, `org.organization.create`)
- **CRITICAL:** System permissions are **NOT** stored in the SET (per requirements)

**Key Generation:**
```python
def _get_cache_key(user_id: UUID, org_id: Optional[UUID] = None) -> str:
    """Generate Redis cache key for user permissions"""
    if org_id is None:
        # Superadmin case - use "superadmin" as org identifier
        return f"user:permissions:superadmin:{str(user_id)}"
    else:
        return f"user:permissions:{str(org_id)}:{str(user_id)}"
```

**Permission Storage Format:**
- Permissions are flattened from nested JSON to dot-separated strings using `flatten_permissions()`
- Format: `{module_group}.{module_name}.{action}` (e.g., `org.user.read`, `org.organization.create`)
- **System permissions are NOT included** in the SET (e.g., `system.super_admin` is not cached)
- Only permissions with `true` value are stored in the SET
- Example SET contents: `{"org.user.read", "org.user.update", "org.organization.read"}`

**Permission Flattening:**
```python
def flatten_permissions(permissions_json: Dict[str, Any]) -> Set[str]:
    """
    Flatten permissions JSON structure to a set of permission strings.
    
    Converts nested structure to flat set:
    {
        "modules": {
            "org": {
                "user": {
                    "read": True,
                    "update": True
                }
            }
        }
    }
    
    To: {"org.user.read", "org.user.update"}
    
    Note: System permissions are NOT included in the SET.
    """
```

**Redis Commands Used:**
- `SMEMBERS user:permissions:{org_id}:{user_id}` - Get all cached permissions (returns SET)
- `DEL user:permissions:{org_id}:{user_id}` - Delete existing SET (before updating)
- `SADD user:permissions:{org_id}:{user_id} {permission1} {permission2} ...` - Add all permissions to SET
- `DEL user:permissions:{org_id}:{user_id}` - Remove entire permission set (invalidation)

### 7.2 Cache Operations

**PermissionCache Class:** All cache operations are methods of `PermissionCache` class.

| Operation | Method | When to Use |
|-----------|--------|-------------|
| **Check Permission** | `PermissionCache.has_permission(user_id, org_id, permission, session)` | On every permission check (uses SISMEMBER) |
| **Get All Permissions** | `PermissionCache.get_user_permissions(user_id, org_id, session)` | When you need full permission set |
| **Set Permissions** | `PermissionCache.set_user_permissions(user_id, permissions_json, org_id)` | When user created/invited or permissions updated |
| **Remove Permissions** | `PermissionCache.invalidate_user_permissions(user_id, org_id)` | When user inactive/deleted |
| **Invalidate Role Users** | `PermissionCache.invalidate_role_users(role_id, session)` | When role permissions updated |

**Note:** All cache functions require `org_id` parameter. For superadmin users, pass `org_id=None`.

**Function Signatures:**
```python
# PermissionCache class (src/acm/permission_cache.py)
_permission_cache = PermissionCache()

async def has_permission(
    self,
    user_id: UUID,
    org_id: Optional[UUID],  # None for superadmin
    permission: str,  # Full permission string, e.g., "users.user.read"
    session: AsyncSession
) -> bool:
    """
    Check a single permission using Redis SISMEMBER first, then DB fallback.
    Uses O(1) Redis membership check - no need to fetch entire SET.
    """

async def get_user_permissions(
    self,
    user_id: UUID,
    org_id: Optional[UUID],  # None for superadmin
    session: AsyncSession
) -> Optional[Set[str]]:
    """
    Get user permissions from database (not cache).
    Returns SET of dot-separated permission strings or None if user not found.
    Note: For permission checks, use has_permission() which checks Redis first.
    """

async def set_user_permissions(
    self,
    user_id: UUID,
    permissions_json: Dict[str, Any],
    org_id: Optional[UUID] = None  # None for superadmin
) -> bool:
    """
    Cache user permissions in Redis SET.
    Converts JSON to flat SET of dot-separated identifiers using flatten_permissions().
    Returns True if successful, False otherwise.
    """

async def invalidate_user_permissions(
    self,
    user_id: UUID,
    org_id: Optional[UUID] = None  # None for superadmin
) -> bool:
    """
    Remove user permissions from Redis cache.
    Deletes the entire SET.
    Returns True if successful, False otherwise.
    """

# Utility function (src/acm/utils.py)
def flatten_permissions(permissions_json: Dict[str, Any]) -> Set[str]:
    """
    Flatten permissions JSON structure to a set of permission strings.
    Converts nested dict to flat set: {"users.user.read_all", "users.user.update", ...}
    System permissions are NOT included in the returned set.
    """
```

**Important Notes:**
- `has_permission()` uses Redis `SISMEMBER` for O(1) checks (doesn't fetch entire SET)
- `set_user_permissions()` handles both initial caching and updates (no separate `update_user_permissions()` function)
- All functions return `Set[str]` (not `Dict[str, Any]`)
- `flatten_permissions()` is a public function in `src/acm/utils.py` used for converting permissions_json to Set format
- System permissions are **NOT** included in the cached SET
- Use `PermissionCache` instance (typically `_permission_cache`) to call methods

### 7.3 Cache Invalidation Rules

**UPDATE Cache (SET) when:**
- ✅ User is **active** AND permissions changed (role change, activation)
- ✅ User is **invited** AND has permissions
- ✅ User status changed to **active**
- ✅ Role permissions updated (affects all active users with that role)

**REMOVE Cache (DELETE) when:**
- ✅ User status changed to **inactive**
- ✅ User is **deleted**
- ✅ User has **no permissions**

**Key Principle:**
- **Active users** → Always UPDATE cache using `set_user_permissions()`
- **Inactive users** → Always REMOVE from cache using `invalidate_user_permissions()`

**Implementation Example:**
```python
# In user service when updating user
if status_changed and user.status == STATUS_INACTIVE:
    # User deactivated → remove from cache
    await invalidate_user_permissions(user.id, user.organization_id)
elif role_changed or (status_changed and user.status == STATUS_ACTIVE):
    # Role changed OR user activated → update cache with new permissions
    if user.permissions_json:
        await set_user_permissions(user.id, user.permissions_json, user.organization_id)
```

---

## RULE 8: Implementation Checklist

### 8.1 Router Implementation Checklist

- [ ] Import `require_permission` from `src.auth.dependencies` (NOT from `src.acm.dependencies`)
- [ ] Add `ctx: AuthContext = Depends(require_permission("module", "action"))` to each route
- [ ] Use permission format: `module.action` (e.g., `"users.user.read_all"`)
- [ ] Remove all old permission-checking dependencies
- [ ] Remove all `is_superadmin()`, `check_permission()` calls from route handlers
- [ ] Pass `ctx: AuthContext` to service methods (not `current_user: User`)
- [ ] If service needs `User` model, fetch it using `get_current_user_model(ctx, session)`

### 8.2 Service Implementation Checklist

- [ ] Remove all `check_permission()` and `check_system_permission()` calls
- [ ] Accept `ctx: AuthContext` parameter (not `current_user: User`)
- [ ] Use `ctx.org_id` for organization filtering (None means superadmin - can see all)
- [ ] If you need `User` model with `permissions_json`, use `get_current_user_model(ctx, session)`
- [ ] Add comment: "Permission validation already done in router via require_permission()"
- [ ] Use `ForbiddenError` only for data scope violations (business logic), not permission validation

### 8.3 Dependency Implementation Checklist

- [ ] NO permission checking in dependency class
- [ ] Remove all permission-checking dependencies
- [ ] Remove all `is_superadmin()`, `check_permission()` calls
- [ ] Accept `ctx: AuthContext` from router's `require_permission()` dependency
- [ ] Pass `ctx` to service methods

### 8.4 Validation Checklist

After implementing a module, verify:

- [ ] All routes use `require_permission()` from `src.auth.dependencies` for permission checking
- [ ] All routes receive `ctx: AuthContext` (not `current_user: User`)
- [ ] No `check_permission()` or `check_system_permission()` in services
- [ ] Services use `ctx.org_id` for organization filtering
- [ ] No permission checks in dependencies
- [ ] Permission format is `module.action` (e.g., `"users.user.read_all"`)

---

## RULE 9: Common Mistakes to Avoid

### 9.1 Mistake 1: Checking Permissions in Service

**❌ WRONG:**
```python
class ResourceService:
    async def list_resources(self, current_user: User):
        if not check_permission(current_user.permissions_json, "module.resource", "read"):
            raise ForbiddenError(...)
```

**✅ CORRECT:**
```python
from src.auth.dependencies import require_permission
from src.schemas import AuthContext

@router.get("/resources")
async def list_resources(
    ctx: AuthContext = Depends(require_permission("resources.resource", "read")),
):
    # Permission already validated
    return await service.list_resources(ctx)
```

### 9.2 Mistake 2: Using check_permission() in Service for Data Scope

**❌ WRONG:**
```python
# Don't check permissions in service
has_read_all = check_permission(permissions_set, "resources.resource.read_all")
```

**✅ CORRECT:**
```python
# Use ctx.org_id for organization filtering
# None means superadmin (can see all orgs)
org_id_filter = ctx.org_id  # None for superadmin means all orgs
```

### 9.3 Mistake 3: Not Invalidating Cache on Permission Changes

**❌ WRONG:**
```python
user.role_id = new_role_id
await repository.update(user)
# Cache not updated!
```

**✅ CORRECT:**
```python
from src.acm.permission_cache import PermissionCache

_permission_cache = PermissionCache()

user.role_id = new_role_id
await repository.update(user)
if user.status == STATUS_ACTIVE:
    await _permission_cache.set_user_permissions(
        user.id, 
        user.permissions_json, 
        user.organization_id
    )
```

### 9.4 Mistake 4: Not Passing org_id to Cache Functions

**❌ WRONG:**
```python
# Missing org_id parameter
await _permission_cache.get_user_permissions(user_id, session)
await _permission_cache.set_user_permissions(user_id, permissions_json)
```

**✅ CORRECT:**
```python
from src.acm.permission_cache import PermissionCache

_permission_cache = PermissionCache()

# Always pass org_id (None for superadmin)
org_id = user.organization_id  # or get from ctx.org_id
await _permission_cache.get_user_permissions(user_id, org_id, session)
await _permission_cache.set_user_permissions(user_id, permissions_json, org_id)
```

### 9.5 Mistake 5: Importing require_permission from Wrong Location

**❌ WRONG:**
```python
# Wrong import location
from src.acm.dependencies import require_permission
```

**✅ CORRECT:**
```python
# Correct import location
from src.auth.dependencies import require_permission
```

### 9.6 Mistake 6: Using User Model Instead of AuthContext

**❌ WRONG:**
```python
@router.get("/users")
async def list_users(
    current_user: User = Depends(require_permission("users.user", "read")),
):
    # Wrong: require_permission returns AuthContext, not User
```

**✅ CORRECT:**
```python
from src.schemas import AuthContext

@router.get("/users")
async def list_users(
    ctx: AuthContext = Depends(require_permission("users.user", "read")),
):
    # Correct: require_permission returns AuthContext
    # If you need User model, fetch it in service using get_current_user_model(ctx, session)
```

---

## RULE 10: Quick Reference

### 10.1 Router Pattern
```python
from src.auth.dependencies import require_permission
from src.schemas import AuthContext

@router.get("/users")
async def list_users(
    ctx: AuthContext = Depends(require_permission("users.user", "read_all")),
    api: UserApiDep = Depends(UserApiDep),
):
    # Permission validated, ctx contains user_id, org_id, role_id, role
    return await api.list_users(query, ctx)
```

### 10.2 Service Pattern
```python
from src.schemas import AuthContext
from src.auth.dependencies import get_current_user_model

async def list_users(
    self,
    query: UserListQuery,
    ctx: AuthContext,
    session: AsyncSession,
):
    # Permission validation already done in router
    # Use ctx.org_id for organization filtering (None = superadmin = all orgs)
    org_id_filter = ctx.org_id
    
    # If you need User model with permissions_json:
    # user = await get_current_user_model(ctx, session)
    
    items, total = await self.repository.list_with_pagination(
        org_id_filter=org_id_filter,
        # ... other params
    )
    return UserPaginatedResponse(items=items, total=total)
```

### 10.3 Dependency Pattern
```python
from src.schemas import AuthContext

class UserApiDep:
    def __init__(
        self,
        session: AsyncSession = Depends(get_session),
    ):
        self.service = UserService(session)
    
    async def list_users(self, query: UserListQuery, ctx: AuthContext):
        # Accept ctx from router's require_permission dependency
        return await self.service.list_users(query, ctx, self.session)
```

---

## RULE 11: Key Takeaways

1. **Centralization:** All RBAC core logic in `src/acm/` module, but `require_permission()` is in `src/auth/dependencies.py`
2. **Router-Only Validation:** Permission checking ONLY via `require_permission()` from `src.auth.dependencies` in routers
3. **AuthContext Return Type:** `require_permission()` returns `AuthContext` (not `User` model) - contains `user_id`, `org_id`, `role_id`, `role`
4. **Permission Format:** Use `module.action` format (e.g., `"users.user.read_all"`) - passed as separate parameters to `require_permission()`
5. **Client Abstraction:** `PermissionClient` Protocol in `src/auth/client.py` allows switching between local ACM and remote service
6. **Service Scope Reading:** Services use `ctx.org_id` for organization filtering (None = superadmin = all orgs), don't validate permissions
7. **Separation of Concerns:** Router validates access, service enforces data scope
8. **Future-Ready:** ACM module can be extracted as separate service via `RemotePermissionClient`
9. **Cache Strategy:** Update for active users, remove for inactive users
10. **Cache Key Format:** `user:permissions:{org_id}:{user_id}` (or `user:permissions:superadmin:{user_id}` for superadmin)
11. **Storage Format:** Redis SET with dot-separated permission strings (e.g., `{"users.user.read_all", "users.user.update"}`)
12. **Permission Checking:** Uses Redis `SISMEMBER` for O(1) checks (no need to fetch entire SET)
13. **Return Types:** All cache functions return `Set[str]` (not `Dict[str, Any]`)
14. **Permission Checking Function:** `check_permission(permissions_set: Set[str], action: str)` takes full permission string (e.g., `"users.user.read"`)
15. **System Permissions:** System permissions are **NOT** stored in Redis SET (check from DB when needed)
16. **org_id Required:** All cache functions require `org_id` parameter (use `None` for superadmin)
17. **Flattening:** Use `flatten_permissions()` from `src/acm/utils.py` to convert nested permissions_json to flat Set of strings
18. **Token org_id:** `AuthContext.org_id` comes from JWT token (can be `None` for superadmin)
19. **PermissionCache Class:** Use `PermissionCache` instance methods (typically `_permission_cache`) for all cache operations
20. **Import Location:** Always import `require_permission` from `src.auth.dependencies`, NOT from `src.acm.dependencies`

---

## Additional Resources

- **Detailed Guide:** See `rbac-implementation-spec.md` in `cursor/guidelines/` for complete implementation details
- **Permission Reference:** See `roles-permissions-reference.md` for permission definitions
- **Code Examples:** See `src/acm/` module implementation

---

**Document Control:**
- **Purpose:** Core RBAC implementation guide for LLM code generation
- **Audience:** AI assistants implementing RBAC in FastAPI projects
- **Status:** Active - Follow these rules for all RBAC implementations

