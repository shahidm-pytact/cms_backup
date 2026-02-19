# Celery Setup Guide

**Purpose:** Essential setup instructions for Celery in a FastAPI project for background task processing.

## RULE 1: Before Starting
### 1.1 User Information Requirements
**CRITICAL RULE:** MUST ASK USER FOR required information before proceeding.

**RULE 1.1.1: Required Information**
- Celery app name (e.g., "myapp", "product_service", "order_processor")

**RULE 1.1.2: Proceeding Rules**
- INCORRECT Proceed without user-provided app name
- CORRECT Ask user for Celery app name first
- CORRECT Use user-provided app name (not example names)
- INCORRECT Use example "fastapi_boilerplate" without user confirmation

## RULE 2: Prerequisites
### 2.1 Redis Requirement
**RULE 2.1.1: Prerequisites**
- CORRECT Redis must be set up first (see `redis_validate.md` in rules/validate folder)
- CORRECT Redis is used as both broker and result backend
- CORRECT Verify Redis is running before configuring Celery
- INCORRECT Configure Celery without Redis setup

**RULE 2.1.2: Redis Configuration Rules**
- CORRECT Redis must be accessible from Celery worker
- CORRECT Redis URL must be correctly configured
- CORRECT Redis service must be healthy before worker starts

## RULE 3: Celery File Structure
### 3.1 Required File Structure
**CRITICAL RULE:** When Celery is activated, MUST create the following file structure in `src/` directory.

**RULE 3.1.1: CORRECT File Structure Pattern**
```
src/
├── celery_app.py           # Celery configuration
├── celery_worker.py        # Celery tasks
└── email_templates/        # Email HTML templates directory
    ├── welcome.html
    └── reset_password.html
```

**RULE 3.1.2: File Structure Rules**
- CORRECT `src/celery_app.py` - Contains Celery app configuration and initialization
- CORRECT `src/celery_worker.py` - Contains all Celery task definitions
- CORRECT `src/email_templates/` - Directory for email HTML templates
- CORRECT `src/email_templates/welcome.html` - Welcome email template
- CORRECT `src/email_templates/reset_password.html` - Password reset email template
- CORRECT Create `email_templates` directory if it doesn't exist
- CORRECT Create template files even if initially empty (can be populated later)
- INCORRECT Place Celery files in `src/infra/` directory (use `src/` directly)
- INCORRECT Mix Celery configuration and tasks in same file
- INCORRECT Missing email_templates directory when email tasks are needed

**RULE 3.1.3: File Purpose**
- CORRECT `celery_app.py` - Celery app instance, broker/backend configuration
- CORRECT `celery_worker.py` - All `@celery_app.task` decorated functions
- CORRECT `email_templates/` - Reusable HTML email templates for email tasks
- CORRECT Templates can be loaded and rendered in Celery tasks

**RULE 3.1.4: Directory Creation Rules**
- CORRECT Create `src/email_templates/` directory when Celery is activated
- CORRECT Create template files with proper HTML structure
- CORRECT Templates should be ready for use in email-sending tasks
- CORRECT Use descriptive template file names matching their purpose

---

## RULE 4: Celery Configuration
### 4.1 Step 1: Add Celery Settings
**RULE 4.1.1: Configuration Location**
- CORRECT Add Celery settings to `src/config.py`
- CORRECT Add broker and backend URLs to Settings class
- CORRECT Use Pydantic BaseSettings for configuration

**RULE 4.1.2: Configuration Pattern**
```python
class Settings(BaseSettings):
    # Celery
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"
    
    # ... other settings ...
```

**RULE 4.1.3: Configuration Rules**
- CORRECT Broker URL: Where Celery sends tasks (Redis)
- CORRECT Result Backend: Where Celery stores task results (Redis)
- CORRECT Use service name `redis` for docker-compose internal communication
- CORRECT Use `localhost` or `127.0.0.1` for local development outside Docker
- CORRECT Use database number (e.g., `/0`) for Redis namespace

### 4.2 Step 2: Create Celery App Module
**RULE 4.2.1: Celery App Location**
- CORRECT Create `src/celery_app.py` for Celery app configuration (see RULE 3 for file structure)
- CORRECT Use user-provided app name (not example names)
- CORRECT Configure broker and backend URLs from settings

**RULE 4.2.2: Celery App Pattern**
```python
from celery import Celery
from src.config import settings

celery_app = Celery(
    "<user_provided_app_name>",  # MUST ASK USER for app name (e.g., "myapp", "product_service")
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)
```

**RULE 4.2.3: Celery App Configuration Rules**
- CORRECT App name should match your project name (user-provided)
- CORRECT JSON serialization for tasks and results
- CORRECT UTC timezone for consistency
- CORRECT Task time limits prevent hanging tasks
- CORRECT Set `task_track_started=True` for task tracking
- CORRECT Set `task_time_limit` and `task_soft_time_limit` for task safety

### 4.3 Step 3: Create Celery Worker Module
**RULE 4.3.1: Celery Worker Location**
- CORRECT Create `src/celery_worker.py` for Celery task definitions (see RULE 3 for file structure)
- CORRECT Import Celery app from `src.celery_app`
- CORRECT Define all tasks using `@celery_app.task` decorator
- CORRECT Use absolute imports for project modules

**RULE 4.3.2: Celery Worker Pattern**
```python
# src/celery_worker.py
from src.celery_app import celery_app

@celery_app.task(name="send_welcome_email")
def send_welcome_email(user_email: str, user_name: str):
    """Send welcome email to new user"""
    # Task implementation here
    pass

@celery_app.task(name="send_password_reset_email")
def send_password_reset_email(user_email: str, reset_token: str):
    """Send password reset email"""
    # Task implementation here
    pass
```

**RULE 4.3.3: Celery Worker Rules**
- CORRECT All tasks must be defined in `src/celery_worker.py`
- CORRECT Use descriptive task names
- CORRECT Import celery_app from `src.celery_app`
- CORRECT Use absolute imports for project modules
- CORRECT Tasks should be idempotent when possible
- INCORRECT Define tasks in `celery_app.py` (separate files)

### 4.4 Step 4: Create Email Templates Directory
**RULE 4.4.1: Email Templates Location**
- CORRECT Create `src/email_templates/` directory (see RULE 3 for file structure)
- CORRECT Create `welcome.html` template file
- CORRECT Create `reset_password.html` template file
- CORRECT Templates should contain valid HTML structure

**RULE 4.4.2: Email Templates Pattern**
```html
<!-- src/email_templates/welcome.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Welcome</title>
</head>
<body>
    <h1>Welcome!</h1>
    <p>Thank you for joining us.</p>
</body>
</html>
```

```html
<!-- src/email_templates/reset_password.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Reset Password</title>
</head>
<body>
    <h1>Password Reset</h1>
    <p>Click the link below to reset your password:</p>
    <a href="{{ reset_url }}">Reset Password</a>
</body>
</html>
```

**RULE 4.4.3: Email Templates Rules**
- CORRECT Create templates directory when Celery is activated
- CORRECT Use HTML structure for email templates
- CORRECT Templates can use template variables (e.g., `{{ variable }}`)
- CORRECT Templates should be ready for rendering in tasks
- CORRECT Add more templates as needed for other email types
- INCORRECT Missing email_templates directory when email tasks are used

### 4.5 Step 5: Add Celery to Requirements
**RULE 4.5.1: Package Requirements**
```txt
celery==5.3.4
```

**RULE 4.5.2: Package Rules**
- CORRECT Add `celery` package to `requirements/base.txt`
- CORRECT Pin Celery version for consistency
- CORRECT CRITICAL: If using Celery, you MUST have `celery` package installed
- INCORRECT Use unpinned Celery version

## RULE 5: Docker Compose Configuration
### 5.1 Worker Service Configuration
**RULE 5.1.1: Worker Service Pattern**
```yaml
services:
  worker:
    build: .
    command: celery -A src.celery_app worker --loglevel=info
    volumes:
      - .:/app
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:password@db:5432/dbname
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      ENVIRONMENT: development
      DEBUG: "true"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully
```

**RULE 5.1.2: Worker Command Rules**
- CORRECT Command: `celery -A src.celery_app worker --loglevel=info`
- CORRECT `-A` specifies the Celery app module path
- CORRECT `worker` starts a worker process
- CORRECT `--loglevel=info` sets logging level
- CORRECT Use absolute module path for Celery app

**RULE 5.1.3: Worker Dependencies Rules**
- CORRECT Worker needs database service (with health check)
- CORRECT Worker needs Redis service (with health check)
- CORRECT Worker needs migrations to complete successfully
- CORRECT Use `condition: service_healthy` for db and redis
- CORRECT Use `condition: service_completed_successfully` for migrate

**RULE 5.1.4: Worker Environment Rules**
- CORRECT All Celery-related env vars must match config
- CORRECT DATABASE_URL must be set for database access
- CORRECT REDIS_URL must be set for Redis access
- CORRECT CELERY_BROKER_URL must match config
- CORRECT CELERY_RESULT_BACKEND must match config

## RULE 6: Common Issues & Solutions
### 6.1 Worker Not Starting
**RULE 6.1.1: Error Description**
- Worker container exits immediately
- Worker fails to start

**RULE 6.1.2: Solutions**
- CORRECT Check Celery app module path is correct: `-A src.celery_app`
- CORRECT Verify Redis is running and accessible
- CORRECT Check worker logs: `docker compose logs worker`
- CORRECT Ensure all environment variables are set
- CORRECT Verify Redis connection string is correct
- CORRECT Check worker dependencies are satisfied

### 6.2 Tasks Not Executing
**RULE 6.2.1: Error Description**
- Tasks are queued but not processed
- Tasks remain in pending state

**RULE 6.2.2: Solutions**
- CORRECT Verify worker is running: `docker compose ps worker`
- CORRECT Check worker logs for errors: `docker compose logs worker`
- CORRECT Verify Redis connection
- CORRECT Ensure tasks are properly defined and registered
- CORRECT Check task imports are correct
- CORRECT Verify task decorators are properly applied

### 6.3 Import Errors
**RULE 6.3.1: Error Description**
- `ModuleNotFoundError` or `ImportError` in tasks
- Tasks fail with import errors

**RULE 6.3.2: Solutions**
- CORRECT Ensure all task dependencies are in `requirements/base.txt`
- CORRECT Use absolute imports in tasks (e.g., `from src.models import ...`)
- CORRECT Verify Python path includes project root
- CORRECT Check that all imported modules are available in worker container
- CORRECT Ensure all required packages are installed
- CORRECT Verify import paths match project structure

## RULE 7: Verification Checklist
### 7.1 Package Verification
**RULE 7.1.1: Package Checklist**
- CORRECT `celery` package added to `requirements/base.txt`
- CORRECT Celery version is pinned
- CORRECT All Celery dependencies are installed

### 7.2 File Structure Verification
**RULE 7.2.1: File Structure Checklist**
- CORRECT `src/celery_app.py` exists with Celery app configured
- CORRECT `src/celery_worker.py` exists with task definitions
- CORRECT `src/email_templates/` directory exists
- CORRECT `src/email_templates/welcome.html` exists
- CORRECT `src/email_templates/reset_password.html` exists

### 7.3 Configuration Verification
**RULE 7.3.1: Configuration Checklist**
- CORRECT Celery settings added to `src/config.py` (broker and backend URLs)
- CORRECT Celery app name uses user-provided value
- CORRECT Broker URL is correctly configured
- CORRECT Result backend URL is correctly configured

### 7.4 Docker Compose Verification
**RULE 7.4.1: Docker Compose Checklist**
- CORRECT Worker service configured in `docker-compose.yml`
- CORRECT Worker depends on Redis and database services
- CORRECT Worker command uses correct Celery app path
- CORRECT Worker environment variables are set
- CORRECT Worker dependencies are properly configured

### 7.5 Runtime Verification
**RULE 7.5.1: Runtime Checklist**
- CORRECT Worker container starts successfully
- CORRECT Worker connects to Redis
- CORRECT Worker connects to database
- CORRECT Tasks can be queued and executed
- CORRECT Task results are stored correctly

## RULE 8: Integration with Existing Project
### 8.1 Integration Steps
**RULE 8.1.1: Step-by-Step Integration**
1. CORRECT Check if `src/celery_app.py` already exists
2. CORRECT If exists, review and enhance; if not, create new
3. CORRECT Check if `src/celery_worker.py` already exists
4. CORRECT If exists, review and enhance; if not, create new
5. CORRECT Check if `src/email_templates/` directory exists, create if not
6. CORRECT Create template files (`welcome.html`, `reset_password.html`) if they don't exist
7. CORRECT Add Celery settings to `src/config.py` if not present
8. CORRECT Add `celery` to `requirements/base.txt` if not present
9. CORRECT Add worker service to `docker-compose.yml` if not present
10. CORRECT Update service dependencies to include worker requirements

**RULE 8.1.2: Integration Rules**
- CORRECT Review existing files before creating new ones
- CORRECT Enhance existing files if they don't follow patterns
- CORRECT Create new files only if they don't exist
- CORRECT Verify all dependencies are satisfied
- CORRECT Test worker startup after integration

## RULE 9: Best Practices
### 9.1 Celery Configuration Best Practices
**RULE 9.1.1: Configuration Best Practices**
- CORRECT Use JSON serialization for tasks and results
- CORRECT Set appropriate task time limits
- CORRECT Use UTC timezone for consistency
- CORRECT Enable task tracking for monitoring
- CORRECT Use separate Redis databases for broker and backend (if needed)

### 9.2 Task Definition Best Practices
**RULE 9.2.1: Task Definition Rules**
- CORRECT Use absolute imports in tasks
- CORRECT Define tasks in separate modules
- CORRECT Use descriptive task names
- CORRECT Handle task errors gracefully
- CORRECT Set appropriate task timeouts

### 9.3 Worker Management Best Practices
**RULE 9.3.1: Worker Management Rules**
- CORRECT Monitor worker logs for errors
- CORRECT Set appropriate worker concurrency
- CORRECT Use worker health checks
- CORRECT Restart workers on failure
- CORRECT Scale workers based on load

## Summary
This guide provides rule-based instructions for setting up Celery in a FastAPI project. Each rule is numbered and contains specific, actionable requirements.

**Key Principles:**
- Redis must be set up before Celery
- Use user-provided app name for Celery app
- Configure broker and backend URLs correctly
- Set appropriate task time limits
- Use absolute imports in tasks
- Create required file structure: `src/celery_app.py`, `src/celery_worker.py`, `src/email_templates/`

**Critical Reminders:**
- Ask user for Celery app name before proceeding
- Verify Redis is running before configuring Celery
- Create required file structure when Celery is activated (see RULE 3)
- Use correct Celery app module path in worker command: `-A src.celery_app`
- Ensure all environment variables are set correctly
- Create `src/email_templates/` directory with template files
- Test worker startup after configuration
