# Project Structure Creation Guide

**Purpose:** Single source of truth for creating complete project structure. **ALWAYS check if files exist before creating them.**

## RULE 1: Before Creating Any Files
### 1.1 Pre-Creation Requirements
**CRITICAL RULE:** MUST complete these steps before creating any files.

**RULE 1.1.1: Required Steps**
1. CORRECT ASK user for ALL required information (database credentials, API settings, module names)
2. CORRECT CHECK if each file/directory exists before creating
3. CORRECT DO NOT overwrite existing files unless explicitly requested
4. CORRECT REPORT to user which files exist and which need to be created

**RULE 1.1.2: Optional Components Rules**
- CORRECT Redis: ONLY if user explicitly requests ("add redis", "develop redis", "include redis")
- CORRECT Celery: ONLY if user explicitly requests ("add celery", "develop celery", "include celery")
- CORRECT If Celery requested but Redis not set up → ask user if they want Redis added first
- INCORRECT Add optional components without user request

## RULE 2: Quick Reference - File Structure
### 2.1 Root Level Files
**RULE 2.1.1: Root Files List**
```
.env                    # Environment variables
.gitignore             # Git ignore patterns
logging.ini            # Logging configuration
alembic.ini            # Alembic migration config
Dockerfile             # Docker image definition
docker-compose.yml     # Docker Compose services
README.md              # Project documentation (optional)
```

**RULE 2.1.2: Root Files Rules**
- CORRECT Create all required root files
- CORRECT Check existence before creating
- CORRECT README.md is optional

### 2.2 Core Directories
**RULE 2.2.1: Core Directory Structure**
```
src/
├── __init__.py
├── config.py          # Application configuration (BaseSettings)
├── database.py        # Database engine and session
├── main.py            # FastAPI application entry point
├── exceptions.py      # Global exception handlers
├── pagination.py      # Pagination helpers (optional)
│
├── api/
│   ├── __init__.py
│   └── router.py      # Main API router
│
├── infra/             # OPTIONAL - only if Redis or Celery requested
│   ├── __init__.py    # Only if Redis or Celery requested
│   ├── cache_redis.py # OPTIONAL - ONLY if user explicitly requests Redis
│   └── celery_app.py  # OPTIONAL - ONLY if user explicitly requests Celery
│
└── <user_module>/     # USER PROVIDES ACTUAL MODULE NAME
    ├── __init__.py
    ├── models.py      # SQLAlchemy models
    ├── schemas.py     # Pydantic schemas
    ├── repository.py  # Database operations
    ├── service.py     # Business logic
    ├── router.py      # FastAPI endpoints
    ├── dependencies.py # Domain dependencies
    ├── constants.py   # Domain constants
    ├── exceptions.py  # Domain exceptions
    ├── utils.py       # Domain utilities
    └── config.py       # Domain configuration (optional)

alembic/
├── __init__.py
├── env.py             # Alembic environment configuration
├── script.py.mako     # Migration template
└── versions/          # Migration files (CRITICAL: Check if any exist - DO NOT create if they exist)

requirements/
├── base.txt           # Base dependencies
└── dev.txt            # Development dependencies

tests/                 # Test files (optional)
templates/             # Template files (optional)
```

**RULE 2.2.2: Core Directory Rules**
- CORRECT Create all required directories
- CORRECT Check existence before creating
- CORRECT Use user-provided module names (not examples)
- CORRECT infra/ directory is OPTIONAL - only if Redis or Celery requested

## RULE 3: File Creation Order
### 3.1 Creation Order Requirements
**CRITICAL RULE:** Follow this exact order and check existence at each step.

**RULE 3.1.1: Phase 1 - Project Foundation**
1. CORRECT Check/create root directories: `src/`, `alembic/`, `requirements/`, `tests/`
2. CORRECT Check/create all `__init__.py` files
3. CORRECT Check/create root config files: `.gitignore`, `.env`, `logging.ini`

**RULE 3.1.2: Phase 2 - Core Configuration**
4. CORRECT Check/create `src/config.py` (requires user input: database credentials, API settings)
5. CORRECT Check/create `src/database.py`
6. CORRECT Check/create `alembic.ini`
7. CORRECT Check/create `alembic/env.py`
8. CORRECT Check/create `alembic/script.py.mako`

**RULE 3.1.3: Phase 3 - Infrastructure (OPTIONAL)**
9. CORRECT ONLY if user requests Redis or Celery: Check/create `src/infra/__init__.py`
10. CORRECT ONLY if user explicitly requests Redis: Check/create `src/infra/cache_redis.py`
11. CORRECT ONLY if user explicitly requests Celery: Check/create `src/infra/celery_app.py`
    - CRITICAL: If Celery requested, check if Redis is set up (Celery requires Redis as broker)
    - CORRECT If Redis not set up, ask user if they want Redis added first

**RULE 3.1.4: Phase 4 - Domain Modules (User-Requested)**
12. CORRECT ASK user for module name and model name
13. CORRECT Check/create `src/<user_module>/` directory
14. CORRECT Check/create all domain module files (models, schemas, repository, service, router, etc.)

**RULE 3.1.5: Phase 5 - API Setup**
15. CORRECT Check/create `src/api/__init__.py`
16. CORRECT Check/create `src/api/router.py`
17. CORRECT Check/create `src/main.py`

**RULE 3.1.6: Phase 6 - Database Migrations**
18. CORRECT CRITICAL: Check if `alembic/versions/` contains any files
19. CORRECT If migration files exist: Review them, use them, DO NOT create new ones
20. CORRECT If no migration files exist: Create ONE initial migration manually
21. INCORRECT DO NOT run `alembic revision --autogenerate` for initial migration

**RULE 3.1.7: Phase 7 - Requirements**
22. CORRECT Check/create `requirements/base.txt`
23. CORRECT Check/create `requirements/dev.txt`
24. CORRECT Verify ALL imports have corresponding packages (see `dependencies_validate.md`)

**RULE 3.1.8: Phase 8 - Docker**
25. CORRECT Check/create `Dockerfile`
26. CORRECT Check/create `docker-compose.yml` (requires user input: database credentials)

## RULE 4: Critical Rules
### 4.1 File Existence Check
**CRITICAL RULE:** ALWAYS check existence before creating ANY file.

**RULE 4.1.1: Existence Check Pattern**
```python
from pathlib import Path

# Check if file exists
if Path("src/config.py").exists():
    # Report to user, ask if should be updated
    pass
else:
    # Create file
    pass
```

**RULE 4.1.2: Existence Check Rules**
- CORRECT ALWAYS check existence before creating
- CORRECT Report to user what exists and what will be created
- CORRECT Get user confirmation before overwriting
- INCORRECT NEVER create files without checking existence first

### 4.2 Optional Components
**CRITICAL RULE:** Only create optional components if user explicitly requests them.

**RULE 4.2.1: Redis Rules**
- CORRECT ONLY create if user explicitly requests ("add redis", "develop redis", "include redis")
- INCORRECT DO NOT add unless user explicitly requests

**RULE 4.2.2: Celery Rules**
- CORRECT ONLY create if user explicitly requests ("add celery", "develop celery", "include celery")
- CORRECT Check if Redis exists (Celery requires Redis as broker)
- CORRECT Ask user if they want Redis added first if not set up
- INCORRECT DO NOT add unless user explicitly requests

### 4.3 Domain Modules
**CRITICAL RULE:** MUST ask user for module and model names before creating.

**RULE 4.3.1: Domain Module Rules**
- CORRECT ASK user for module name (e.g., "organizations", "members", "users")
- CORRECT ASK user for model name (e.g., "Organization", "Member", "User")
- CORRECT Use user-provided names (examples are structural patterns only)
- INCORRECT NEVER create modules without asking user for names

### 4.4 Database Migrations

**CRITICAL RULE:** Check for existing migrations before creating new ones.

**RULE 4.4.1: Migration Rules**
- CORRECT Check if `alembic/versions/` contains any files
- CORRECT If migration files exist: Review them, use them, DO NOT create new ones
- CORRECT If no migration files exist: Create ONE initial migration manually
- INCORRECT NEVER run `alembic revision --autogenerate` for initial migration
- INCORRECT NEVER create multiple initial migration files

### 4.5 User Input Requirements

**RULE 4.5.1: Required User Input**
- CORRECT MUST ask user for: Database name, user, password
- CORRECT MUST ask user for: API title, version, prefix
- CORRECT MUST ask user for: Environment name, debug mode
- CORRECT MUST ask user for: Module name (if creating modules)
- CORRECT MUST ask user for: Model name (if creating modules)

## RULE 5: Required Files by Component
### 5.1 Minimal Project
**RULE 5.1.1: Minimal Project Files**
- CORRECT `.env`, `.gitignore`, `logging.ini`
- CORRECT `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`
- CORRECT `src/__init__.py`, `src/config.py`, `src/database.py`, `src/main.py`
- CORRECT `requirements/base.txt`

### 5.2 With Domain Module
**RULE 5.2.1: Domain Module Files**
- CORRECT All minimal files +
- CORRECT `src/<user_module>/` with all required files (models, schemas, repository, service, router, dependencies, constants, exceptions, utils)

### 5.3 With Redis (OPTIONAL)
**RULE 5.3.1: Redis Files**
- CORRECT All previous files +
- CORRECT `src/infra/__init__.py`
- CORRECT `src/infra/cache_redis.py`
- CORRECT Redis service in `docker-compose.yml`
- CORRECT Redis settings in `config.py`

**RULE 5.3.2: Redis Rules**
- CORRECT ONLY add if user explicitly requests Redis
- INCORRECT Add Redis without user request

### 5.4 With Celery (OPTIONAL)
**RULE 5.4.1: Celery Files**
- CORRECT All previous files +
- CORRECT `src/infra/celery_app.py` (requires Redis to be set up first)
- CORRECT Worker service in `docker-compose.yml`
- CORRECT Celery settings in `config.py`

**RULE 5.4.2: Celery Rules**
- CORRECT ONLY add if user explicitly requests Celery
- CORRECT Check if Redis is set up (Celery requires Redis as broker)
- CORRECT Ask user if they want Redis added first if not set up
- INCORRECT Add Celery without user request

### 5.5 With Docker
**RULE 5.5.1: Docker Files**
- CORRECT All previous files +
- CORRECT `Dockerfile`, `docker-compose.yml`

## RULE 6: Common Mistakes
### 6.1 Common Mistakes Reference Table
**RULE 6.1.1: Mistakes and Solutions**
| Mistake | Impact | Solution |
|---------|--------|----------|
| Creating files without checking existence | Overwrites existing files | Always check `Path(file).exists()` before creating |
| Overwriting existing files without confirmation | Data loss | Report to user, get confirmation before overwriting |
| Creating multiple initial migration files | Migration conflicts | Check if migration files exist, use existing ones |
| Creating domain modules without asking user for names | Wrong module/model names | Always ask user for module name and model name |
| Creating config files without user input | Missing required values | Ask user for all required configuration values |
| Creating files in wrong order | Dependencies not met | Follow exact file creation order |
| Adding Redis/Celery without user request | Unnecessary complexity | Only add if user explicitly requests |

**RULE 6.1.2: Prevention Rules**
- CORRECT Always check file existence before creating
- CORRECT Always ask user for confirmation before overwriting
- CORRECT Always ask user for module and model names
- CORRECT Always ask user for configuration values
- CORRECT Follow exact file creation order
- CORRECT Only add optional components if user explicitly requests

## RULE 7: Verification Checklist
### 7.1 Structure Verification
**RULE 7.1.1: Structure Checklist**
- CORRECT All required directories exist
- CORRECT All required `__init__.py` files exist
- CORRECT All core files exist (config.py, database.py, main.py)
- CORRECT All user-requested domain modules exist
- CORRECT Only ONE initial migration file exists (if any)
- CORRECT All requirements files exist
- CORRECT Docker files exist (if using Docker)
- CORRECT No duplicate files created
- CORRECT All files follow architectural patterns
- CORRECT User-provided values used (not placeholders)
- CORRECT Optional components only added if user requested

## RULE 8: Integration with Other Rules
### 8.1 Related Rulebooks
**RULE 8.1.1: Integration Points**
- CORRECT Configuration: `config_validate.md` - config.py structure
- CORRECT Database: `database_setup.md` - database.py and migrations
- CORRECT Domain Modules: `module_architecture_validate.md` - module file structure
- CORRECT Docker: `docker_validate.md` - Dockerfile and docker-compose.yml
- CORRECT Dependencies: `dependencies_validate.md` - requirements structure

**RULE 8.1.2: Integration Rules**
- CORRECT Follow related rulebooks for specific file structures
- CORRECT Verify consistency with other rulebooks
- CORRECT Use patterns from related rulebooks

## Summary
This guide provides rule-based instructions for creating complete project structure. Each rule is numbered and contains specific, actionable requirements.

**Key Principles:**
- Always check file existence before creating
- Always ask user for required information
- Only add optional components if user explicitly requests
- Follow exact file creation order
- Use user-provided values (not placeholders)

**Critical Reminders:**
- CHECK if each file/directory exists before creating
- ASK user for ALL required information before proceeding
- DO NOT overwrite existing files unless explicitly requested
- REPORT to user which files exist and which need to be created
- ONLY add Redis/Celery if user explicitly requests
- ALWAYS ask user for module and model names
- CHECK for existing migrations before creating new ones
- FOLLOW exact file creation order
