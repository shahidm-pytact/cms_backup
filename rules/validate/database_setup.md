# Database Setup Guide

**Purpose:** PostgreSQL with SQLAlchemy 2.x async engine, Alembic migrations, and UUID primary keys.

## RULE 1: Before Starting
### 1.1 User Information Requirements
**CRITICAL RULE:** MUST ASK USER FOR required information before proceeding.

**RULE 1.1.1: Required Information**
- Module name and model name (examples are structural patterns only)
- Database name, user, password (do not use defaults)

**RULE 1.1.2: Proceeding Rules**
- INCORRECT Proceed without user-provided values
- CORRECT Ask user for all required information first
- CORRECT Use user-provided values (not placeholders or defaults)
- INCORRECT Use example names unless user explicitly requests them

## RULE 2: Quick Reference
### 2.1 Required Packages
**RULE 2.1.1: Package Requirements**
```txt
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
alembic==1.13.1
```

**RULE 2.1.2: Package Rules**
- CORRECT Include `sqlalchemy[asyncio]` for async SQLAlchemy support
- CORRECT Include `asyncpg` for PostgreSQL async driver
- CORRECT Include `alembic` for database migrations
- CORRECT Pin package versions for consistency

### 2.2 Database URL Format
**RULE 2.2.1: URL Format Pattern**
```
postgresql+asyncpg://[user]:[password]@[host]:[port]/[database]
```

**RULE 2.2.2: URL Rules**
- CORRECT Use `postgresql+asyncpg://` protocol for async connections
- CORRECT Use service name `db` for Docker container communication
- CORRECT Use `localhost` or `127.0.0.1` for local development
- CORRECT Replace placeholders with user-provided values

### 2.3 Migration Rules
**RULE 2.3.1: Critical Migration Rules**
- CORRECT ONLY ONE initial migration file
- CORRECT ALWAYS use UUID for primary keys (not INTEGER)
- CORRECT ALWAYS verify all model fields are in migration
- CORRECT ALWAYS verify relationships for ambiguity

## RULE 3: Implementation Steps
### 3.1 Step 1: Database Configuration
**RULE 3.1.1: Configuration Location**
- CORRECT Add database configuration to `src/config.py`
- CORRECT Use Pydantic BaseSettings for configuration
- CORRECT Ask user for database name, user, and password before proceeding

**RULE 3.1.2: Configuration Pattern**
```python
class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://<user>:<password>@db:5432/<dbname>"
    # Replace <user>, <password>, <dbname> with user-provided values
```

**RULE 3.1.3: Configuration Rules**
- CORRECT Use user-provided values (not placeholders)
- CORRECT Use service name `db` for Docker communication
- CORRECT Use standard port `5432` for container communication
- INCORRECT Use placeholder values like `<user>`, `<password>`, `<dbname>`

### 3.2 Step 2: Database Module
**RULE 3.2.1: Database Module Location**
- CORRECT Create `src/database.py` for database configuration
- CORRECT Implement async engine with connection pooling
- CORRECT Create async session maker
- CORRECT Define Base class for models

**RULE 3.2.2: Database Module Pattern**
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from src.config import settings

# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=settings.debug,
)
# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
# Base class for models
class Base(DeclarativeBase):
    pass

# Dependency for FastAPI routes
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

**RULE 3.2.3: Connection Pooling Rules**
- CORRECT Configure `pool_size=10` for base connection pool
- CORRECT Configure `max_overflow=20` for additional connections
- CORRECT Configure `pool_timeout=30` for connection timeout
- CORRECT Configure `pool_recycle=3600` to recycle connections
- CORRECT Use `echo=settings.debug` for SQL query logging

**RULE 3.2.4: Session Maker Rules**
- CORRECT Use `async_sessionmaker` for async sessions
- CORRECT Set `expire_on_commit=False` for better performance
- CORRECT Set `autocommit=False` for transaction control
- CORRECT Set `autoflush=False` for manual flush control

### 3.3 Step 3: Add Packages
**RULE 3.3.1: Package Requirements**
```txt
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
alembic==1.13.1
```

**RULE 3.3.2: Package Rules**
- CORRECT Add all required packages to `requirements/base.txt`
- CORRECT Pin package versions for consistency
- CORRECT Verify all imports have corresponding packages

## RULE 4: Alembic Migrations
### 4.1 Migration File Structure
**RULE 4.1.1: Initial Migration Pattern**
```python
"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial'
down_revision: Union[str, None] = None  # CORRECT Must be None for initial migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Use user's actual table name (not example names)
    op.create_table(
        'table_name',  # Replace with user's actual table name
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_table_name_id'), 'table_name', ['id'], unique=False)

def downgrade() -> None:
    op.drop_table('table_name')
```

**RULE 4.1.2: Migration File Rules**
- CORRECT Use descriptive name: `001_initial_migration.py` (not hash-based)
- CORRECT Use simple revision ID: `'001_initial'` (not hash-based)
- CORRECT Set `down_revision: None` for initial migration
- CORRECT Use `postgresql.UUID(as_uuid=True)` for primary keys
- CORRECT Use `server_default=sa.text('now()')` for timestamps

### 4.2 Critical Migration Rules
**RULE 4.2.1: Initial Migration Rules**
- CORRECT ONLY ONE initial migration - Check `alembic/versions/` before creating
- CORRECT UUID from start - Use `postgresql.UUID(as_uuid=True)` for primary keys
- CORRECT Descriptive names - Use `001_initial_migration.py` (not hash-based)
- CORRECT Verify all fields - Every `Mapped[Type]` must have corresponding `sa.Column`

**RULE 4.2.2: WRONG Patterns (Will Cause Errors)**
```python
# INCORRECT ERROR: Using INTEGER instead of UUID
sa.Column('id', sa.Integer(), nullable=False)  # INCORRECT Use postgresql.UUID instead

# INCORRECT ERROR: Using default_factory for timestamps (doesn't work with SQLAlchemy 2.x)
created_at: Mapped[datetime] = mapped_column(default_factory=datetime.utcnow)  # INCORRECT ERROR
# CORRECT: Use server_default
created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

### 4.3 Alembic Configuration
**RULE 4.3.1: Alembic env.py Location**
- CORRECT Configure `alembic/env.py` for async migrations
- CORRECT Handle async URL conversion
- CORRECT Use correct config attribute

**RULE 4.3.2: Alembic env.py Pattern**
```python
from src.database import Base
from src.config import settings
# Import user's actual models (not example names)
from src.module_name.models import ModelName  # Replace with user's actual imports

config = context.config

# CORRECT CRITICAL: Use config_file_name (NOT config_file_path)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# CORRECT CRITICAL: Remove +asyncpg for offline migrations
config.set_main_option("sqlalchemy.url", settings.database_url.replace("+asyncpg", ""))

target_metadata = Base.metadata

# For online migrations, keep +asyncpg for async engine
async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.database_url  # Keep +asyncpg
    # ... rest of async migration code
```

**RULE 4.3.3: Alembic Configuration Rules**
- CORRECT Offline migrations: Remove `+asyncpg` from URL
- CORRECT Online migrations: Keep `+asyncpg` in URL
- CORRECT Use `config.config_file_name` (NOT `config.config_file_path`)
- CORRECT Import all models in `alembic/env.py` for autogenerate

## RULE 5: Migration-Model Field Verification
### 5.1 Field Verification Requirement
**CRITICAL RULE:** Every `Mapped[Type] = mapped_column(...)` MUST have corresponding `sa.Column(...)` in migration.

**RULE 5.1.1: Verification Method**
```bash
# Check model fields
grep -n "Mapped\[" src/module_name/models.py

# Check migration columns
grep -n "sa.Column" alembic/versions/001_initial_migration.py | grep table_name

# Manually verify each field exists in both
```

**RULE 5.1.2: Common Missing Fields**
- Business: `name`, `phone`, `description`, `price`, `quantity`
- Status: `is_active`, `is_verified`, `status`
- Audit: `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`

**RULE 5.1.3: Impact**
- Missing fields cause `UndefinedColumnError` at runtime
- Application will fail when querying missing columns
- Must verify all fields before declaring complete

**RULE 5.1.4: Verification Checklist**
- CORRECT Every model field has corresponding migration column
- CORRECT All business fields are included
- CORRECT All status fields are included
- CORRECT All audit fields are included
- CORRECT No missing columns in migration

## RULE 6: SQLAlchemy Relationship Verification
### 6.1 Relationship Ambiguity
**CRITICAL RULE:** Verify all relationships for ambiguity before declaring complete.

**RULE 6.1.1: Ambiguity Scenario 1 - Multiple FKs to Same Table**
```python
# User has multiple FKs to Order (customer_id, created_by, updated_by)
# Solution: Use primaryjoin
orders: Mapped[list["Order"]] = relationship(
    "Order",
    back_populates="customer",
    primaryjoin="User.id == Order.customer_id"  # CORRECT Specify which FK
)
```

**RULE 6.1.2: Ambiguity Scenario 2 - Bidirectional Foreign Keys**
```python
# Payment and Order both have FKs to each other
# Solution: Use foreign_keys on BOTH sides

# Payment side
order: Mapped["Order"] = relationship(
    "Order",
    back_populates="payment",
    foreign_keys=[order_id]  # CORRECT Specify FK
)

# Order side
payment: Mapped["Payment | None"] = relationship(
    "Payment",
    back_populates="order",
    foreign_keys=[payment_id]  # CORRECT Specify FK
)
```

**RULE 6.1.3: Verification Steps**
1. CORRECT Scan relationships: `grep -r "relationship" src/*/models.py`
2. CORRECT Identify ambiguous relationships (multiple FKs or bidirectional FKs)
3. CORRECT Add `primaryjoin` or `foreign_keys` parameters
4. CORRECT Test application startup - This is a RUNTIME error

**RULE 6.1.4: Impact**
- Ambiguous relationships cause `AmbiguousForeignKeysError` or `ArgumentError` at startup
- Application will fail to start if relationships are ambiguous
- Must verify all relationships before declaring complete

## RULE 7: Common Issues & Solutions
### 7.1 Common Database Errors
**RULE 7.1.1: Error Reference Table**

| Error | Cause | Solution |
|-------|-------|----------|
| `table already exists` | Duplicate migration files | Remove auto-generated duplicates, keep only one |
| UUID vs INTEGER mismatch | Initial migration used INTEGER | Use `postgresql.UUID(as_uuid=True)` from start |
| `UndefinedColumnError` | Migration missing columns | Verify all model fields have corresponding `sa.Column` |
| `AmbiguousForeignKeysError` | Multiple FKs or bidirectional FKs | Add `primaryjoin` or `foreign_keys` parameters |
| `ArgumentError: Relationship Direction Conflict` | Bidirectional FKs without disambiguation | Add `foreign_keys` on BOTH relationship sides |
| `AttributeError: 'Config' object has no attribute 'config_file_path'` | Wrong config attribute | Use `config.config_file_name` (NOT `config_file_path`) |
| Autogenerate doesn't detect models | Missing model imports | Import all models in `alembic/env.py` |

**RULE 7.1.2: Error Prevention Rules**
- CORRECT Check for existing migration files before creating new ones
- CORRECT Use UUID from start (not INTEGER)
- CORRECT Verify all model fields in migration
- CORRECT Disambiguate all relationships
- CORRECT Use correct config attribute name
- CORRECT Import all models in Alembic env.py

## RULE 8: Verification Checklist
### 8.1 Pre-Implementation Checklist
Before starting database setup, verify:

**Packages:**
- CORRECT `sqlalchemy[asyncio]`, `asyncpg`, `alembic` in `requirements/base.txt`
- CORRECT Package versions are pinned

**Configuration:**
- CORRECT Database settings added to `src/config.py` (user-provided values)
- CORRECT Database URL uses user-provided values (not placeholders)

**Database Module:**
- CORRECT `src/database.py` exists with async engine and session maker
- CORRECT `Base` class defined for models
- CORRECT `get_session()` dependency function exists
- CORRECT Connection pooling configured correctly

### 8.2 Alembic Configuration Checklist
**Alembic Files:**
- CORRECT Alembic configuration files exist (`alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`)
- CORRECT `alembic/env.py` removes `+asyncpg` for offline migrations
- CORRECT `alembic/env.py` keeps `+asyncpg` for online async migrations
- CORRECT `alembic/env.py` uses `config.config_file_name` (NOT `config.config_file_path`)
- CORRECT All models imported in `alembic/env.py` for autogenerate

### 8.3 Migration Checklist
**Migration Files:**
- CORRECT ONLY ONE initial migration file in `alembic/versions/`
- CORRECT Initial migration uses `postgresql.UUID(as_uuid=True)` for primary keys
- CORRECT Timestamp columns use `server_default=sa.text('now()')`
- CORRECT Migration file has descriptive name (not hash-based)
- CORRECT `down_revision: None` for initial migration

**Migration Content:**
- CORRECT CRITICAL: All model fields verified in migration (every `Mapped` column has `sa.Column`)
- CORRECT All business fields included
- CORRECT All status fields included
- CORRECT All audit fields included

### 8.4 Relationship Checklist
**Relationship Verification:**
- CORRECT CRITICAL: All relationships verified for ambiguity
- CORRECT CRITICAL: All ambiguous relationships specify `primaryjoin` or `foreign_keys`
- CORRECT CRITICAL: Application starts without `AmbiguousForeignKeysError`
- CORRECT All multiple FK relationships disambiguated
- CORRECT All bidirectional FK relationships disambiguated

### 8.5 Runtime Verification
**Application Startup:**
- CORRECT CRITICAL: Application starts without `AmbiguousForeignKeysError`
- CORRECT CRITICAL: Application queries database without `UndefinedColumnError`
- CORRECT Database connections work correctly
- CORRECT Migrations run successfully

## RULE 9: Integration with Existing Project
### 9.1 Integration Steps
**RULE 9.1.1: Check Existing Files**
1. CORRECT Check if `src/database.py` exists - review/enhance or create new
2. CORRECT Add database settings to `src/config.py` if not present
3. CORRECT Add database packages to `requirements/base.txt` if not present
4. CORRECT Check Alembic configuration - review or create
5. CORRECT Check migration files - review existing or create initial migration
6. CORRECT Ensure all models import `Base` from `src.database`

**RULE 9.1.2: Integration Rules**
- CORRECT Review existing files before creating new ones
- CORRECT Enhance existing files if they don't follow patterns
- CORRECT Create new files only if they don't exist
- CORRECT Verify all models use `Base` from `src.database`

## Summary
This guide provides rule-based instructions for setting up PostgreSQL database with SQLAlchemy 2.x async engine and Alembic migrations. Each rule is numbered and contains specific, actionable requirements.

**Key Principles:**
- Use UUID for primary keys from the start
- Verify all model fields are in migration
- Disambiguate all relationships
- Use correct Alembic configuration
- Handle async URL conversion properly

**Critical Reminders:**
- Ask user for database credentials before proceeding
- Only ONE initial migration file should exist
- Use `postgresql.UUID(as_uuid=True)` for primary keys
- Use `server_default=sa.text('now()')` for timestamps
- Use `config.config_file_name` (NOT `config_file_path`) in Alembic
- Verify all model fields in migration before declaring complete
- Disambiguate all relationships to prevent runtime errors
