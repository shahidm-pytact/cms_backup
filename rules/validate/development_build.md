# Development Build Configuration

**Purpose:** Configure minimal development builds for FastAPI with Docker Compose.

## RULE 1: Keep It Simple
### 1.1 Default Approach
**CRITICAL RULE:**
- CORRECT **MUST use `docker-compose.yml` directly** - it's sufficient for development
- INCORRECT **DO NOT create optional files automatically** (`.cursorrules`, `docker-compose.dev.yml`)
- CORRECT **Only create optional files** if you have a specific need

**RULE 1.1.1: Default Behavior**
- Use `docker-compose.yml` directly for development
- No need for separate development configuration files
- Keep configuration simple and maintainable

## RULE 2: Minimal Development Stack
### 2.1 Required Services
**MANDATORY Services:**
- CORRECT `db` - PostgreSQL database
- CORRECT `migrate` - Runs database migrations (once)
- CORRECT `api` - FastAPI application with hot-reload

**RULE 2.1.1: Service Requirements**
- `db` must start first (required by all services)
- `migrate` must run before `api` starts
- `api` is the main development target

### 2.2 Optional Services
**OPTIONAL Services (only if needed):**
- `worker` - Celery worker (for background tasks)
- `redis` - Redis cache (for caching or Celery)

**RULE 2.2.1: When to Include Optional Services**
- CORRECT Include `redis` only if actively developing Redis features
- CORRECT Include `worker` only if actively developing Celery features
- INCORRECT DO NOT start optional services unless needed
- CORRECT Skip optional services to speed up development builds

## RULE 3: Basic Usage
### 3.1 Service Startup Commands
**RULE 3.1.1: Minimal Stack (Most Common)**
```bash
docker compose up db migrate api
```

**RULE 3.1.2: With Redis (If Needed)**
```bash
docker compose up db migrate redis api
```

**RULE 3.1.3: With Celery (If Needed)**
```bash
docker compose up db migrate redis api worker
```

**RULE 3.1.4: Service Startup Rules**
- CORRECT Start only required services for basic development
- CORRECT Add optional services only when actively developing those features
- CORRECT Use explicit service names to control what starts

## RULE 4: Service Dependencies
### 4.1 Dependency Graph
**Service Dependencies:**
```
api → depends on → db, migrate
worker → depends on → redis, db
migrate → depends on → db
```

**RULE 4.1.1: Build Order**
1. Start `db` first (required by all services)
2. Run `migrate` once (before API starts)
3. Start `api` (main development target)
4. Add `redis`/`worker` only if actively developing those features

**RULE 4.1.2: Dependency Rules**
- CORRECT `db` must be healthy before `migrate` starts
- CORRECT `migrate` must complete successfully before `api` starts
- CORRECT `redis` must be healthy before `worker` starts (if Celery is used)
- CORRECT All dependencies must be satisfied before dependent services start

## RULE 5: Optional Configuration Files
### 5.1 General Rule
**CRITICAL RULE:**
- INCORRECT **DO NOT create optional files automatically**
- CORRECT **Only create if you have a specific need**
- CORRECT **Default to using `docker-compose.yml` directly**

### 5.2 .cursorrules File
**RULE 5.2.1: When to Create**
- CORRECT Only if you need Cursor IDE-specific integration
- CORRECT Only if you have specific Cursor IDE requirements

**RULE 5.2.2: When NOT to Create**
- INCORRECT If `docker-compose.yml` already works (most cases)
- INCORRECT If you don't need Cursor IDE-specific features
- INCORRECT As a default file in every project

**RULE 5.2.3: Purpose**
- Cursor IDE-specific rules for development builds
- Optional integration with Cursor IDE features

### 5.3 docker-compose.dev.yml File
**RULE 5.3.1: When to Create**
- CORRECT Only if you have a separate production `docker-compose.yml`
- CORRECT Only if you need to override base configuration for development
- CORRECT Only if base config is shared/committed and you want local dev tweaks

**RULE 5.3.2: When NOT to Create**
- INCORRECT If `docker-compose.yml` is already development-focused (most common)
- INCORRECT If base config already has `--reload`, `DEBUG=true`, and volume mounts
- INCORRECT If you don't need to separate dev/prod configs
- INCORRECT As a default file in every project

**RULE 5.3.3: Usage (If Created)**
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**RULE 5.3.4: Default Behavior**
- Use `docker-compose.yml` directly - it's sufficient for development
- No need for separate development configuration file

## RULE 6: Profile-Based Startup
### 6.1 Docker Compose Profiles
**RULE 6.1.1: When to Use Profiles**
- CORRECT If using Docker Compose v2.4+
- CORRECT If you want to control which services start
- CORRECT If you want to group services by purpose

**RULE 6.1.2: Profile Configuration Pattern**
```yaml
services:
  api:
    profiles: ["dev"]
  worker:
    profiles: ["celery"]  # Only start if Celery is needed
  redis:
    profiles: ["redis"]   # Only start if Redis is needed
```

**RULE 6.1.3: Starting with Profiles**
```bash
docker compose --profile dev up
```

**RULE 6.1.4: Profile Rules**
- CORRECT Use profiles to group related services
- CORRECT Start only services in specified profiles
- CORRECT Keep profile names descriptive and clear

## RULE 7: Best Practices
### 7.1 Development Build Best Practices
**RULE 7.1.1: Start Minimal Services**
- CORRECT Only start what you need for development
- CORRECT Skip optional services (Redis/Celery) unless actively developing
- CORRECT Use explicit service names in startup commands

**RULE 7.1.2: Use Hot Reload**
- CORRECT Ensure volume mounts are configured in `docker-compose.yml`
- CORRECT Verify `--reload` flag is in API command
- CORRECT Check file permissions allow container to read files

**RULE 7.1.3: Keep It Simple**
- CORRECT Use `docker-compose.yml` directly
- CORRECT Don't create optional files unless actually needed
- CORRECT Avoid over-engineering development setup

**RULE 7.1.4: Don't Create Optional Files**
- INCORRECT Don't create `.cursorrules` automatically
- INCORRECT Don't create `docker-compose.dev.yml` automatically
- CORRECT Only create if you have a specific need

## RULE 8: Common Workflows
### 8.1 Basic API Development
**RULE 8.1.1: Command**
```bash
docker compose up db migrate api
```

**RULE 8.1.2: When to Use**
- CORRECT Basic API development
- CORRECT Most common development scenario
- CORRECT No Redis or Celery needed

### 8.2 Development with Redis
**RULE 8.2.1: Command**
```bash
docker compose up db migrate redis api
```

**RULE 8.2.2: When to Use**
- CORRECT When actively developing Redis features
- CORRECT When testing caching functionality
- CORRECT When Redis is required for API features

### 8.3 Development with Celery
**RULE 8.3.1: Command**
```bash
docker compose up db migrate redis api worker
```

**RULE 8.3.2: When to Use**
- CORRECT When actively developing Celery features
- CORRECT When testing background tasks
- CORRECT When Celery is required for application features

**RULE 8.3.3: Celery Requirements**
- CORRECT Redis must be included (Celery uses Redis as broker)
- CORRECT Both `redis` and `worker` services must be started
- CORRECT `worker` depends on `redis` being healthy

## RULE 9: Troubleshooting
### 9.1 Service Not Starting
**RULE 9.1.1: Check Dependencies**
- CORRECT Verify dependencies are running (e.g., `api` needs `db` and `migrate`)
- CORRECT Check service health: `docker compose ps`
- CORRECT Verify service dependencies in `docker-compose.yml`

**RULE 9.1.2: Check Configuration**
- CORRECT Verify `.env` file has correct credentials
- CORRECT Check environment variables match between services
- CORRECT Verify DATABASE_URL matches db service credentials

**RULE 9.1.3: Check Service Health**
- CORRECT Run `docker compose ps` to check service status
- CORRECT Check service logs: `docker compose logs <service_name>`
- CORRECT Verify health checks are passing

### 9.2 Slow Builds
**RULE 9.2.1: Skip Unnecessary Services**
- CORRECT Use only required services for development
- CORRECT Don't start Redis/Celery unless actively developing
- CORRECT Use explicit service names in startup commands

**RULE 9.2.2: Use Volume Mounts**
- CORRECT Use volume mounts instead of rebuilding images
- CORRECT Verify volumes are mounted correctly in `docker-compose.yml`
- CORRECT Check that code changes are reflected without rebuild

### 9.3 Hot Reload Not Working
**RULE 9.3.1: Check Volume Mounts**
- CORRECT Verify volumes are mounted correctly in `docker-compose.yml`
- CORRECT Check that `--reload` flag is in API command
- CORRECT Ensure file permissions allow container to read files

**RULE 9.3.2: Check Configuration**
- CORRECT Verify API command includes `--reload` flag
- CORRECT Check that volume mounts point to correct directories
- CORRECT If using `docker-compose.dev.yml`, verify it's not overriding volume mounts incorrectly

**RULE 9.3.3: Check File Permissions**
- CORRECT Ensure container can read files from mounted volumes
- CORRECT Check file ownership and permissions
- CORRECT Verify volume mount paths are correct

### 9.4 Troubleshooting Reference Table
| Issue | Solution |
|-------|----------|
| Service not starting | Check dependencies are running (e.g., `api` needs `db` and `migrate`) |
| Service not starting | Verify `.env` file has correct credentials |
| Service not starting | Check service health: `docker compose ps` |
| Slow builds | Skip unnecessary services, use only required services |
| Slow builds | Use volume mounts instead of rebuilding images |
| Hot reload not working | Verify volumes are mounted correctly in `docker-compose.yml` |
| Hot reload not working | Check that `--reload` flag is in API command |
| Hot reload not working | Ensure file permissions allow container to read files |
| Hot reload not working | If using `docker-compose.dev.yml`, verify it's not overriding volume mounts incorrectly |

## RULE 10: Verification Checklist
### 10.1 Development Setup Verification
Before starting development, verify:

**Configuration:**
- CORRECT `docker-compose.yml` exists and is properly configured
- CORRECT `.env` file has correct credentials
- CORRECT Volume mounts are configured for hot reload
- CORRECT API command includes `--reload` flag

**Services:**
- CORRECT `db` service is configured with health checks
- CORRECT `migrate` service runs before `api` starts
- CORRECT `api` service has volume mounts for code changes
- CORRECT Optional services (Redis/Celery) only included if needed

**Dependencies:**
- CORRECT Service dependencies are correctly configured
- CORRECT Health checks are properly set up
- CORRECT `depends_on` conditions are correct

**Hot Reload:**
- CORRECT Volume mounts are configured correctly
- CORRECT `--reload` flag is in API command
- CORRECT File permissions allow container to read files

## Summary
This guide provides rule-based instructions for configuring minimal development builds. Each rule is numbered and contains specific, actionable requirements.

**Key Principles:**
- Keep it simple - use `docker-compose.yml` directly
- Start minimal services - only what you need
- Don't create optional files automatically
- Use hot reload for faster development
- Skip optional services unless actively developing

**Critical Reminders:**
- Default to using `docker-compose.yml` directly
- Only create optional files if you have a specific need
- Start only required services for basic development
- Verify hot reload is working before starting development
- Check service dependencies and health checks

**Common Workflows:**
- Basic: `docker compose up db migrate api`
- With Redis: `docker compose up db migrate redis api`
- With Celery: `docker compose up db migrate redis api worker`
