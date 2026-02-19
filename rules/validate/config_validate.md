# Configuration Setup Guide

**Purpose:** Application configuration using Pydantic BaseSettings with environment variable support.

## RULE 1: Before Starting
### 1.1 User Information Requirements
**CRITICAL RULE:** MUST ASK USER FOR required information before proceeding.

**RULE 1.1.1: Required Information**
- Database name, user, password (do not use defaults)
- API title, version, prefix
- Environment name (development/production/staging)
- Debug mode (true/false)

**RULE 1.1.2: Proceeding Rules**
- INCORRECT Proceed without user-provided values
- CORRECT Ask user for all required information first
- CORRECT Use user-provided values (not placeholders or defaults)
- INCORRECT Use example values unless user explicitly requests them

## RULE 2: Quick Reference
### 2.1 Required Package
**RULE 2.1.1: Package Requirement**
```txt
pydantic-settings==2.1.0
```

**RULE 2.1.2: Package Rules**
- CORRECT Include `pydantic-settings` package
- CORRECT Pin package version for consistency
- INCORRECT Use unpinned version

### 2.2 Import Pattern
**RULE 2.2.1: CORRECT Import Pattern**
```python
from pydantic_settings import BaseSettings  # CORRECT
```

**RULE 2.2.2: WRONG Import Pattern (DO NOT DO THIS)**
```python
# NOT: from pydantic import BaseSettings  # INCORRECT ERROR
```

**RULE 2.2.3: Import Rules**
- CORRECT Import from `pydantic_settings` module
- INCORRECT Import from `pydantic` module
- CORRECT Use `from pydantic_settings import BaseSettings`

### 2.3 Configuration Pattern
**RULE 2.3.1: CORRECT Configuration Pattern**
```python
class Settings(BaseSettings):
    field_name: str = "default_value"  # CORRECT Direct assignment
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }

settings = Settings()  # Singleton instance
```

**RULE 2.3.2: Configuration Pattern Rules**
- CORRECT Use direct assignment for field defaults
- CORRECT Use `model_config` dict for configuration
- CORRECT Create singleton `settings` instance
- CORRECT Set `env_file: ".env"` for environment file support
- CORRECT Set `case_sensitive: False` for case-insensitive variables

## RULE 3: Critical Rules
### 3.1 Package Requirement
**CRITICAL RULE:** If using `BaseSettings`, you MUST include `pydantic-settings`.

**RULE 3.1.1: Package Requirement Pattern**
```txt
# requirements/base.txt
pydantic-settings==2.1.0
```

**RULE 3.1.2: Package Requirement Rules**
- CORRECT MUST include `pydantic-settings` package
- CORRECT Pin version to `2.1.0` for consistency
- INCORRECT Without this, using `BaseSettings` will cause `ImportError`
- CORRECT Verify package is installed before using BaseSettings

### 3.2 Import Source
**CRITICAL RULE:** Import `BaseSettings` from `pydantic_settings` (NOT `pydantic`).

**RULE 3.2.1: CORRECT Import Pattern**
```python
# CORRECT
from pydantic_settings import BaseSettings
```

**RULE 3.2.2: WRONG Import Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG
from pydantic import BaseSettings  # INCORRECT ERROR: ImportError
```

**RULE 3.2.3: Import Source Rules**
- CORRECT MUST import from `pydantic_settings` module
- INCORRECT NEVER import from `pydantic` module
- CORRECT Verify import works before proceeding

### 3.3 RecursionError Prevention
**CRITICAL RULE:** NEVER use `Field()` in `BaseSettings` classes - causes `RecursionError`.

**RULE 3.3.1: WRONG Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG - Causes RecursionError
class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql+asyncpg://...",
        description="Database URL"
    )  # INCORRECT ERROR
```

**RULE 3.3.2: CORRECT Pattern**
```python
# CORRECT - Direct assignment
class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://..."  # CORRECT Direct assignment
    # Description can be added as comment if needed
```

**RULE 3.3.3: RecursionError Prevention Rules**
- CORRECT BaseSettings fields MUST use direct assignment (no `Field()`)
- INCORRECT NEVER use `Field()` in BaseSettings classes
- CORRECT Use comments for field descriptions if needed
- INCORRECT Using `Field()` will cause `RecursionError: maximum recursion depth exceeded`

### 3.4 Pydantic v2 Configuration
**CRITICAL RULE:** Use `model_config` dict (NOT `Config` class) for Pydantic v2.

**RULE 3.4.1: CORRECT Pattern (Pydantic v2)**
```python
# CORRECT - Pydantic v2
class Settings(BaseSettings):
    database_url: str = "..."
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }
```

**RULE 3.4.2: WRONG Pattern (DO NOT DO THIS)**
```python
# INCORRECT WRONG - Pydantic v1 (deprecated)
class Settings(BaseSettings):
    class Config:  # INCORRECT Deprecated in Pydantic v2
        env_file = ".env"
```

**RULE 3.4.3: Pydantic v2 Configuration Rules**
- CORRECT MUST use `model_config` dict for Pydantic v2
- INCORRECT NEVER use `Config` class (deprecated in Pydantic v2)
- CORRECT Use dictionary syntax for configuration
- CORRECT Set `env_file` and `case_sensitive` in `model_config`

## RULE 4: Implementation Pattern
### 4.1 Configuration Module
**RULE 4.1.1: Configuration Module Location**
- CORRECT Create `src/config.py` for application configuration
- CORRECT Use Pydantic BaseSettings for configuration
- CORRECT Ask user for values before creating

**RULE 4.1.2: Configuration Module Pattern**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database - USE USER-PROVIDED VALUES
    database_url: str = "postgresql+asyncpg://<user>:<password>@db:5432/<dbname>"
    # Replace <user>, <password>, <dbname> with user-provided values
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # Celery
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"
    
    # API - USE USER-PROVIDED VALUES
    api_title: str = "<user_provided_title>"  # Ask user
    api_version: str = "<user_provided_version>"  # Ask user
    api_prefix: str = "<user_provided_prefix>"  # Ask user (e.g., "/v1")
    
    # Environment - USE USER-PROVIDED VALUES
    environment: str = "<user_provided_environment>"  # Ask user
    debug: bool = <user_provided_debug>  # Ask user (true/false)
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }

settings = Settings()  # Singleton instance
```

**RULE 4.1.3: Configuration Module Rules**
- CORRECT Import from `pydantic_settings` (not `pydantic`)
- CORRECT Use `model_config` dict (not `Config` class)
- CORRECT Use direct assignment (not `Field()`)
- CORRECT `env_file: ".env"` enables loading from .env file
- CORRECT `case_sensitive: False` allows case-insensitive environment variables
- CORRECT Create singleton `settings` instance
- CORRECT Replace placeholders with user-provided values

### 4.2 Environment Variable Support
**RULE 4.2.1: Environment File Pattern**
```bash
# .env file
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/dbname
REDIS_URL=redis://redis:6379/0
DEBUG=true
```

**RULE 4.2.2: Environment Variable Rules**
- CORRECT Environment variables take precedence over defaults
- CORRECT Variable names are case-insensitive (due to `case_sensitive: False`)
- CORRECT Use `.env` file for local development
- CORRECT Use environment variables in production
- CORRECT Settings can be overridden via environment variables

## RULE 5: Common Issues & Solutions
### 5.1 Common Errors
**RULE 5.1.1: Error Reference Table**

| Error | Cause | Solution |
|-------|-------|----------|
| `ImportError: cannot import name 'BaseSettings' from 'pydantic'` | Wrong import source | Use `from pydantic_settings import BaseSettings` |
| `ImportError: cannot import name 'BaseSettings'` | Missing package | Add `pydantic-settings==2.1.0` to requirements |
| `RecursionError: maximum recursion depth exceeded` | Using `Field()` in BaseSettings | Use direct assignment instead of `Field()` |
| Settings not loading from .env | Missing config or file | Verify `.env` exists and `model_config` includes `"env_file": ".env"` |
| Settings use defaults instead of .env | Variable name mismatch | Check environment variable names (case-insensitive) |

**RULE 5.1.2: Error Prevention Rules**
- CORRECT Use correct import source (`pydantic_settings`)
- CORRECT Include `pydantic-settings` package
- CORRECT Use direct assignment (not `Field()`)
- CORRECT Verify `.env` file exists
- CORRECT Check environment variable names match settings

## RULE 6: Common Mistakes
### 6.1 Common Mistakes Reference Table
**RULE 6.1.1: Mistakes and Solutions**

| Mistake | Correct Approach |
|---------|------------------|
| Importing from `pydantic` | Import from `pydantic_settings` |
| Missing `pydantic-settings` package | Add `pydantic-settings==2.1.0` to requirements |
| Using `Field()` in BaseSettings | Use direct assignment |
| Using `Config` class | Use `model_config` dict |
| Hardcoding values | Ask user for values, use placeholders |
| Not creating singleton | Create `settings = Settings()` instance |

**RULE 6.1.2: Prevention Rules**
- CORRECT Review code for common mistakes before completion
- CORRECT Use correct import source
- CORRECT Use direct assignment for fields
- CORRECT Use `model_config` dict
- CORRECT Ask user for values before proceeding

---

## RULE 7: Verification Checklist
### 7.1 Package Verification
**RULE 7.1.1: Package Checklist**
- CORRECT `pydantic-settings==2.1.0` in `requirements/base.txt`
- CORRECT Package is installed and importable
- CORRECT No version conflicts with other packages

### 7.2 Configuration File Verification
**RULE 7.2.1: Configuration File Checklist**
- CORRECT `src/config.py` exists with `Settings` class
- CORRECT `Settings` class inherits from `BaseSettings` (from `pydantic_settings`)
- CORRECT `model_config` dict includes `"env_file": ".env"`
- CORRECT `settings = Settings()` singleton instance created
- CORRECT All required settings defined (database_url, redis_url, etc.)

### 7.3 Value Verification
**RULE 7.3.1: Value Checklist**
- CORRECT User-provided values used (not placeholders)
- CORRECT Database credentials are user-provided
- CORRECT API configuration is user-provided
- CORRECT Environment settings are user-provided

### 7.4 Code Quality Verification
**RULE 7.4.1: Code Quality Checklist**
- CORRECT No `Field()` used in BaseSettings fields
- CORRECT Settings can be imported: `from src.config import settings`
- CORRECT No deprecated `Config` class used
- CORRECT All imports are from correct modules

---

## RULE 8: Integration with Existing Project
### 8.1 Integration Steps
**RULE 8.1.1: Step-by-Step Integration**
1. CORRECT Check if `src/config.py` already exists
2. CORRECT If exists, verify it uses `BaseSettings` from `pydantic_settings`
3. CORRECT If not, create new with all required settings
4. CORRECT Add `pydantic-settings` to `requirements/base.txt` if not present
5. CORRECT Verify `settings` singleton is created and can be imported

**RULE 8.1.2: Integration Rules**
- CORRECT Review existing files before creating new ones
- CORRECT Enhance existing files if they don't follow patterns
- CORRECT Create new files only if they don't exist
- CORRECT Verify all dependencies are satisfied
- CORRECT Test configuration loading after integration

---

## Summary
This guide provides rule-based instructions for setting up application configuration using Pydantic BaseSettings. Each rule is numbered and contains specific, actionable requirements.

**Key Principles:**
- Use `pydantic-settings` package (not `pydantic`)
- Use direct assignment for fields (not `Field()`)
- Use `model_config` dict (not `Config` class)
- Ask user for values before proceeding
- Create singleton `settings` instance

**Critical Reminders:**
- Import from `pydantic_settings` (not `pydantic`)
- Never use `Field()` in BaseSettings classes
- Use `model_config` dict for Pydantic v2
- Replace placeholders with user-provided values
- Verify configuration loads correctly after setup
