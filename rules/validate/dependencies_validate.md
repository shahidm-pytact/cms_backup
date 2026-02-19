# Dependencies Management Guide

**Purpose:** Ensure all Python packages used in code are listed in `requirements/base.txt` to prevent ImportError at runtime.

## RULE 1: Quick Reference
### 1.1 Requirements File Structure
**RULE 1.1.1: File Structure**
```
requirements/
├── base.txt    # Production dependencies
└── dev.txt     # Development dependencies (includes base.txt)
```

**RULE 1.1.2: File Structure Rules**
- CORRECT Use `base.txt` for production dependencies
- CORRECT Use `dev.txt` for development dependencies
- CORRECT Include `base.txt` in `dev.txt` with `-r base.txt`
- INCORRECT Mix production and development dependencies

### 1.2 Import-to-Package Mapping
**CRITICAL RULE:** These imports require specific packages that may not be obvious.
**RULE 1.2.1: Import Mapping Table**
| Import | Required Package | Error if Missing |
|--------|-----------------|------------------|
| `EmailStr` from `pydantic` | `email-validator` | `ImportError: email-validator is not installed` |
| `BaseSettings` from `pydantic_settings` | `pydantic-settings` | `ImportError: cannot import name 'BaseSettings'` |
| `redis.asyncio` | `redis` | `ImportError: No module named 'redis'` |
| `celery` | `celery` | `ImportError: No module named 'celery'` |
| `sqlalchemy.ext.asyncio` | `sqlalchemy[asyncio]` | `ImportError: No module named 'sqlalchemy.ext.asyncio'` |
| `passlib.context` | `passlib[bcrypt]` | `ImportError: No module named 'passlib'` |
| `jose` or `jwt` from `jose` | `python-jose[cryptography]` | `ImportError: No module named 'jose'` |
| `Form(...)` from `fastapi` | `python-multipart` | `RuntimeError: Form data requires "python-multipart"` |
| `HTTPBearer` from `fastapi.security` | `fastapi` (included) | - |

**RULE 1.2.2: Import Mapping Rules**
- CORRECT Map every import to required package
- CORRECT Verify package is in requirements/base.txt
- CORRECT Check special cases (EmailStr, BaseSettings, Form, etc.)
- INCORRECT Assume package is obvious from import name

## RULE 2: Critical Rules
### 2.1 All Imports Must Have Packages
**CRITICAL RULE:** Every import in code MUST have corresponding package in `requirements/base.txt`.

**RULE 2.1.1: Verification Method**
```bash
# Scan all imports
grep -r "import\|from" src/

# Map each import to required package (see mapping table above)
# Verify EVERY package is in requirements/base.txt
```

**RULE 2.1.2: Import Verification Rules**
- CORRECT Scan all Python files for imports
- CORRECT Map each import to required package
- CORRECT Verify EVERY package is in requirements/base.txt
- CORRECT Add missing packages immediately
- INCORRECT Skip import verification
- INCORRECT Assume packages are already included

### 2.2 Special Cases
**CRITICAL RULE:** These imports require specific packages that are NOT obvious.
**RULE 2.2.1: Special Case Imports**
- CORRECT `EmailStr` → requires `email-validator` (NOT obvious)
- CORRECT `BaseSettings` → requires `pydantic-settings` (NOT obvious)
- CORRECT `Form(...)` → requires `python-multipart` (NOT obvious - OAuth2 token endpoints use Form)
- CORRECT `redis.asyncio` → requires `redis` (NOT obvious)
- CORRECT `passlib.context` → requires `passlib[bcrypt]` (NOT obvious)

**RULE 2.2.2: Special Case Rules**
- CORRECT Always check special cases when verifying dependencies
- CORRECT Add special case packages even if not obvious
- INCORRECT Skip special case verification
- INCORRECT Assume special cases are included automatically

### 2.3 Version Constraints
**CRITICAL RULE:** Pin these packages to specific versions.
**RULE 2.3.1: Version Constraints Pattern**
```txt
bcrypt==4.0.1  # CRITICAL: bcrypt 5.0.0 is incompatible with passlib 1.7.4
python-multipart==0.0.6  # Required for Form() parameters
```

**RULE 2.3.2: Version Constraint Rules**
- CORRECT Pin `bcrypt==4.0.1` (NOT 5.0.0)
- CORRECT Pin `python-multipart==0.0.6`
- CORRECT Pin all critical packages to specific versions
- INCORRECT Use unpinned versions for critical packages
- INCORRECT Use bcrypt 5.0.0 with passlib 1.7.4

## RULE 3: Base Requirements Template
### 3.1 Base Requirements Pattern
**RULE 3.1.1: Base Requirements Template**
```txt
# Core
fastapi==0.109.0
uvicorn[standard]==0.27.0

# Database
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
alembic==1.13.1

# Validation
pydantic==2.5.3
pydantic-settings==2.1.0
email-validator==2.2.0

# Security
passlib[bcrypt]==1.7.4
bcrypt==4.0.1  # CRITICAL: Pin to 4.0.1
python-jose[cryptography]==3.3.0
python-multipart==0.0.6  # CRITICAL: Required for Form() parameters

# Background Tasks (if used)
redis==5.0.1
celery==5.3.4

# Utils
python-dotenv==1.0.0
```

**RULE 3.1.2: Base Requirements Rules**
- CORRECT Group packages by category
- CORRECT Pin all package versions
- CORRECT Include critical version constraints
- CORRECT Add comments for critical packages
- INCORRECT Use unpinned versions
- INCORRECT Mix categories without organization

### 3.2 Development Requirements
**RULE 3.2.1: Development Requirements Pattern**
```txt
-r base.txt
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
black==24.1.1
ruff==0.1.11
```

**RULE 3.2.2: Development Requirements Rules**
- CORRECT Include base.txt with `-r base.txt`
- CORRECT Add development-only packages
- CORRECT Pin development package versions
- CORRECT Keep development packages separate from production

## RULE 4: Mandatory Verification Process=
### 4.1 Verification Requirement
**CRITICAL RULE:** You MUST complete this verification before declaring the project "ready".

**RULE 4.1.1: Verification Steps**
1. CORRECT Complete dependency audit
2. CORRECT Verify special cases
3. CORRECT Runtime verification
4. INCORRECT Skip verification steps
5. INCORRECT Declare ready without verification

### 4.2 Step 1: Complete Dependency Audit
**RULE 4.2.1: Dependency Audit Method**
```bash
# Scan ALL Python files for imports
grep -r "import\|from" src/

# For each import found:
# 1. Map to required package (use mapping table above)
# 2. Verify package is in requirements/base.txt
# 3. Add missing packages immediately
```

**RULE 4.2.2: Dependency Audit Rules**
- CORRECT Scan all Python files for imports
- CORRECT Map each import to required package
- CORRECT Verify package is in requirements/base.txt
- CORRECT Add missing packages immediately
- INCORRECT Skip dependency audit
- INCORRECT Assume all packages are included

### 4.3 Step 2: Verify Special Cases
**RULE 4.3.1: Special Cases Checklist**
- CORRECT `EmailStr` used → `email-validator` in requirements?
- CORRECT `BaseSettings` used → `pydantic-settings` in requirements?
- CORRECT `Form(...)` used → `python-multipart` in requirements?
- CORRECT `redis.asyncio` used → `redis` in requirements?
- CORRECT `celery` used → `celery` in requirements?
- CORRECT `passlib.context` used → `passlib[bcrypt]` in requirements?
- CORRECT `bcrypt==4.0.1` pinned (NOT 5.0.0)?

**RULE 4.3.2: Special Cases Verification Rules**
- CORRECT Check all special cases
- CORRECT Verify special case packages are included
- CORRECT Verify version constraints are correct
- INCORRECT Skip special cases verification

### 4.4 Step 3: Runtime Verification
**RULE 4.4.1: Runtime Verification Checklist**
- CORRECT Application can start without ImportError
- CORRECT All imports resolve correctly
- CORRECT No missing package errors
- CORRECT All dependencies are installed

**RULE 4.4.2: Runtime Verification Rules**
- CORRECT Test application startup
- CORRECT Verify all imports work
- CORRECT Check for missing package errors
- INCORRECT Skip runtime verification
- INCORRECT Assume dependencies work without testing

**RULE 4.4.3: Critical Verification Rule**
- CORRECT "Ready" means the application can START without ImportError
- CORRECT Code structure verification is NOT sufficient
- CORRECT Dependency verification is MANDATORY before declaring ready
- INCORRECT Declare ready without runtime verification

## RULE 5: Common Dependencies Checklist
### 5.1 Core Dependencies
**RULE 5.1.1: Core Dependencies Checklist**
- CORRECT `fastapi` - FastAPI framework
- CORRECT `uvicorn[standard]` - ASGI server
- CORRECT `python-dotenv` - Environment variable management

### 5.2 Database Dependencies
**RULE 5.2.1: Database Dependencies Checklist**
- CORRECT `sqlalchemy[asyncio]` - ORM with async support
- CORRECT `asyncpg` - PostgreSQL async driver
- CORRECT `alembic` - Database migrations

### 5.3 Validation Dependencies
**RULE 5.3.1: Validation Dependencies Checklist**
- CORRECT `pydantic` - Data validation
- CORRECT `pydantic-settings` - Settings management (if using BaseSettings)
- CORRECT `email-validator` - REQUIRED if using EmailStr

### 5.4 Security Dependencies
**RULE 5.4.1: Security Dependencies Checklist**
- CORRECT `passlib[bcrypt]` - Password hashing (if using password hashing)
- CORRECT `bcrypt==4.0.1` - CRITICAL: Pin to 4.0.1 (if using passlib)
- CORRECT `python-jose[cryptography]` - JWT tokens (if using JWT)
- CORRECT `python-multipart==0.0.6` - CRITICAL: REQUIRED if using Form() parameters

### 5.5 Background Task Dependencies
**RULE 5.5.1: Background Task Dependencies Checklist**
- CORRECT `redis` - If using Redis
- CORRECT `celery` - If using Celery

## RULE 6: Common Mistakes
### 6.1 Common Mistakes Reference Table
**RULE 6.1.1: Mistakes and Solutions**
| Mistake | Impact | Solution |
|---------|--------|----------|
| Declaring "ready" without verifying dependencies | ImportError at runtime | Complete dependency audit before declaring ready |
| Using `EmailStr` without `email-validator` | `ImportError: email-validator is not installed` | Add `email-validator==2.2.0` |
| Using `BaseSettings` without `pydantic-settings` | `ImportError: cannot import name 'BaseSettings'` | Add `pydantic-settings==2.1.0` |
| Using `Form(...)` without `python-multipart` | `RuntimeError: Form data requires "python-multipart"` | Add `python-multipart==0.0.6` |
| Using `redis.asyncio` without `redis` | `ImportError: No module named 'redis'` | Add `redis==5.0.1` |
| Using `celery` without `celery` package | `ImportError: No module named 'celery'` | Add `celery==5.3.4` |
| Using `bcrypt 5.0.0` with `passlib 1.7.4` | `ValueError: password cannot be longer than 72 bytes` | Pin `bcrypt==4.0.1` |
| Verifying only code structure | Missing dependencies cause runtime errors | Verify runtime dependencies too |

**RULE 6.1.2: Prevention Rules**
- CORRECT Review code for common mistakes before completion
- CORRECT Complete dependency audit before declaring ready
- CORRECT Verify special cases
- CORRECT Test runtime dependencies
- INCORRECT Skip dependency verification

## RULE 7: Integration with Existing Project
### 7.1 Integration Steps
**RULE 7.1.1: Step-by-Step Integration**
1. CORRECT Check if `requirements/base.txt` exists
2. CORRECT Review all Python files for imports: `grep -r "import\|from" src/`
3. CORRECT Map each import to required package (use mapping table)
4. CORRECT Add missing packages to `requirements/base.txt`
5. CORRECT Verify special cases (EmailStr, BaseSettings, Form(), etc.)
6. CORRECT Test that all imports work after adding packages

**RULE 7.1.2: Integration Rules**
- CORRECT Review existing files before creating new ones
- CORRECT Complete dependency audit for existing code
- CORRECT Add missing packages immediately
- CORRECT Verify all imports work after integration
- INCORRECT Skip dependency verification for existing code

## Summary
This guide provides rule-based instructions for managing Python dependencies. Each rule is numbered and contains specific, actionable requirements.

**Key Principles:**
- Every import must have corresponding package
- Special cases require specific packages
- Version constraints are critical for compatibility
- Runtime verification is mandatory

**Critical Reminders:**
- Complete dependency audit before declaring ready
- Verify special cases (EmailStr, BaseSettings, Form, etc.)
- Pin critical packages to specific versions
- Test runtime dependencies, not just code structure
- "Ready" means application can START without ImportError
