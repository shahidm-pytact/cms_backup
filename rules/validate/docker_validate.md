# Docker Setup Guide

**Purpose:** Essential setup instructions for Docker and docker-compose configuration.

## RULE 1: Before Starting
### 1.1 User Information Requirements
**CRITICAL RULE:** MUST ASK USER FOR required information before proceeding.

**RULE 1.1.1: Required Information**
- Database name (POSTGRES_DB) - e.g., "myapp_db", "project_db"
- Database user (POSTGRES_USER) - default: "postgres" (confirm with user)
- Database password (POSTGRES_PASSWORD) - CRITICAL, must ask, do not use defaults

**RULE 1.1.2: Proceeding Rules**
- INCORRECT Proceed with docker-compose.yml creation without user-provided values
- CORRECT Ask user for all required database credentials first
- CORRECT Use user-provided values (not placeholders or defaults)
- INCORRECT Use example values like `<password>`, `<db_name>`, `<user>` without replacement

## RULE 2: Overview
### 2.1 Docker Compose Overview
**RULE 2.1.1: Overview Points**
- CORRECT Docker Compose for local development
- CORRECT Required services: db, migrate, api
- CORRECT Optional services: redis (only if user requests Redis), worker (only if user requests Celery)
- CORRECT Health checks for proper startup order
- CORRECT Non-standard host ports to avoid conflicts

**RULE 2.1.2: Service Rules**
- CORRECT Redis and worker services are OPTIONAL - only add when user explicitly requests them
- CORRECT Required services must always be included
- INCORRECT Add optional services without user request

## RULE 3: Dockerfile Creation
### 3.1 Dockerfile Pattern
**RULE 3.1.1: Dockerfile Location**
- CORRECT Create `Dockerfile` in project root
- CORRECT Use Python 3.11 slim base image
- CORRECT Install system dependencies
- CORRECT Copy requirements and install packages

**RULE 3.1.2: Dockerfile Pattern**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/base.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**RULE 3.1.3: Dockerfile Rules**
- CORRECT Use Python 3.11 slim base image
- CORRECT Install system dependencies (gcc, postgresql-client)
- CORRECT Copy requirements before application code
- CORRECT Install packages from requirements/base.txt
- CORRECT Expose port 8000
- CORRECT Set default command for uvicorn

## RULE 4: Docker Compose Configuration
### 4.1 Version Field
**CRITICAL RULE:** DO NOT include `version` field in docker-compose.yml.

**RULE 4.1.1: Version Field Rules**
- INCORRECT Include `version` field in docker-compose.yml
- CORRECT Omit the `version` field entirely
- CORRECT Modern docker-compose (v2+) does not require or use the `version` field
- INCORRECT Including it will generate warnings: "the attribute `version` is obsolete"

### 4.2 Port Mapping Strategy
**CRITICAL RULE:** ALWAYS use non-standard host ports to avoid conflicts with local services.

**RULE 4.2.1: Port Mapping Rules**
- CORRECT PostgreSQL: Use `"5433:5432"` (host:container) instead of `"5432:5432"`
- CORRECT Redis: Use `"6380:6379"` (host:container) instead of `"6379:6379"`
- CORRECT This prevents "address already in use" errors when local services are running
- CORRECT Container-to-container communication still uses standard ports (5432, 6379) via service names
- INCORRECT Use standard host ports that conflict with local services

### 4.3 Complete docker-compose.yml Structure
**RULE 4.3.1: Docker Compose Pattern**
```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: <user_provided_user>  # Ask user (default: "postgres")
      POSTGRES_PASSWORD: <user_provided_password>  # MUST ASK USER - CRITICAL
      POSTGRES_DB: <user_provided_dbname>  # MUST ASK USER
    ports:
      - "5433:5432"  # Non-standard host port
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"  # Non-standard host port
    command: redis-server --appendonly yes --appendfsync everysec --maxmemory 256mb --maxmemory-policy allkeys-lru --save 60 1000
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  migrate:
    build: .
    command: alembic upgrade head
    volumes:
      - .:/app
    environment:
      DATABASE_URL: postgresql+asyncpg://<user>:<password>@db:5432/<dbname>
      # Replace <user>, <password>, <dbname> with SAME values provided by user
    depends_on:
      db:
        condition: service_healthy
    restart: "no"

  api:
    build: .
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://<user>:<password>@db:5432/<dbname>
      # Replace <user>, <password>, <dbname> with SAME values provided by user
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully

  worker:
    build: .
    command: celery -A src.infra.celery_app worker --loglevel=info
    volumes:
      - .:/app
    environment:
      DATABASE_URL: postgresql+asyncpg://<user>:<password>@db:5432/<dbname>
      # Replace <user>, <password>, <dbname> with SAME values provided by user
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully

volumes:
  postgres_data:
  redis_data:
```

**RULE 4.3.2: Docker Compose Rules**
- CORRECT Replace all placeholders with user-provided values
- CORRECT Use non-standard host ports (5433, 6380)
- CORRECT Include health checks for db and redis
- CORRECT Include migrate service with restart: "no"
- CORRECT Use service names for internal communication

## RULE 5: Critical Configuration Rules
### 5.1 Health Checks
**RULE 5.1.1: Health Check Requirements**
- CORRECT Always include health checks for `db` service
- CORRECT If Redis is added (user requested): Include health check for `redis` service
- CORRECT Use `depends_on` with `condition: service_healthy` for services that depend on them
- INCORRECT Skip health checks for required services

**RULE 5.1.2: Health Check Pattern**
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]
  interval: 5s
  timeout: 5s
  retries: 5
```

### 5.2 Service Dependencies
**RULE 5.2.1: Dependency Rules**
- CORRECT `migrate` depends on `db` with `condition: service_healthy`
- CORRECT `api` depends on:
  - `db` with `condition: service_healthy`
  - `migrate` with `condition: service_completed_successfully`
  - `redis` with `condition: service_healthy` (ONLY if Redis service exists - user requested Redis)
- CORRECT `worker` depends on (ONLY if user requested Celery):
  - `db` with `condition: service_healthy`
  - `redis` with `condition: service_healthy` (required - Celery needs Redis)
  - `migrate` with `condition: service_completed_successfully`

**RULE 5.2.2: Dependency Configuration Rules**
- CORRECT Use `condition: service_healthy` for health-checked services
- CORRECT Use `condition: service_completed_successfully` for migrate service
- CORRECT Only include optional service dependencies if service exists
- INCORRECT Skip dependency conditions

### 5.3 Environment Variables
**CRITICAL RULE:** Password Consistency - MUST ASK the user for database credentials BEFORE creating docker-compose.yml.

**RULE 5.3.1: Environment Variable Consistency Rules**
- CORRECT The password in `DATABASE_URL` MUST match `POSTGRES_PASSWORD` in the `db` service environment
- CORRECT The username in `DATABASE_URL` MUST match `POSTGRES_USER` in the `db` service environment
- CORRECT The database name in `DATABASE_URL` MUST match `POSTGRES_DB` in the `db` service environment
- CORRECT Use the SAME values provided by the user in all places
- INCORRECT Use different values in different places

**RULE 5.3.2: Environment Variable Example**
If user provides:
- POSTGRES_PASSWORD: "mypassword123"
- POSTGRES_USER: "postgres"
- POSTGRES_DB: "myapp_db"

Then `DATABASE_URL` must be:
`postgresql+asyncpg://postgres:mypassword123@db:5432/myapp_db`

**RULE 5.3.3: Service Names for Internal Communication**
- CORRECT Use service names (e.g., `db`, `redis`) for internal container communication
- CORRECT Database URL: `postgresql+asyncpg://postgres:password@db:5432/dbname`
- CORRECT Redis URL: `redis://redis:6379/0`
- INCORRECT Use `localhost` or `127.0.0.1` for container-to-container communication

### 5.4 Redis Persistence
**CRITICAL RULE:** Redis data MUST be persisted to a volume to survive container restarts.

**RULE 5.4.1: Redis Persistence Requirements**
- CORRECT Always mount a volume for Redis data: `redis_data:/data`
- CORRECT Enable AOF (Append Only File) persistence: `--appendonly yes`
- CORRECT Set AOF sync policy: `--appendfsync everysec` (balances performance and durability)
- CORRECT Optionally enable RDB snapshots: `--save 60 1000` (save if 1000+ keys changed in 60 seconds)
- CORRECT Declare `redis_data` volume in the `volumes` section
- INCORRECT Run Redis without a volume (data will be lost on container restart)
- INCORRECT Use `--save ""` to disable RDB (only if you want AOF-only persistence)

**RULE 5.4.2: Redis Persistence Configuration Pattern**
```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6380:6379"
  command: redis-server --appendonly yes --appendfsync everysec --maxmemory 256mb --maxmemory-policy allkeys-lru --save 60 1000
  volumes:
    - redis_data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    timeout: 3s
    retries: 5

volumes:
  postgres_data:
  redis_data:  # REQUIRED for Redis persistence
```

**RULE 5.4.3: Redis Persistence Command Options**
- `--appendonly yes`: Enables AOF persistence (writes every command to disk)
- `--appendfsync everysec`: Syncs AOF file every second (good balance of performance and durability)
- `--save 60 1000`: Creates RDB snapshot if 1000+ keys changed in 60 seconds (backup method)
- `--maxmemory 256mb`: Limits memory usage to 256MB
- `--maxmemory-policy allkeys-lru`: Evicts least recently used keys when memory limit is reached

**RULE 5.4.4: Redis Persistence Rules**
- CORRECT Mount volume to `/data` directory (Redis default persistence location)
- CORRECT Use named volume `redis_data` (not bind mount) for better portability
- CORRECT Enable both AOF and RDB for maximum data safety
- CORRECT Verify volume is declared in `volumes` section at the bottom of docker-compose.yml
- INCORRECT Forget to mount volume (data will be lost on restart)
- INCORRECT Forget to declare volume in volumes section (will cause startup error)

**RULE 5.4.5: Redis Data Loss Prevention**
- CORRECT With volume mounted: Data persists across container restarts, stops, and rebuilds
- CORRECT Without volume: Data is lost when container is removed or restarted
- CORRECT Volume persists even if container is recreated: `docker compose down` and `docker compose up`
- INCORRECT Assume Redis data persists without volume configuration

### 5.5 Migrate Service
**CRITICAL RULE:** MUST include a `migrate` service that runs `alembic upgrade head`.

**RULE 5.5.1: Migrate Service Requirements**
- CORRECT Depends on `db` with `condition: service_healthy`
- CORRECT Has `restart: "no"` (runs once and exits)
- CORRECT Uses the same DATABASE_URL environment variable as api/worker
- CORRECT Both `api` and `worker` MUST depend on `migrate` with `condition: service_completed_successfully`
- INCORRECT Without this, the application will fail with "relation does not exist" errors

## RULE 6: Common Issues & Solutions
### 6.1 Port Already in Use
**RULE 6.1.1: Error Description**
- "address already in use" on port 5432 or 6379
- `Bind for 0.0.0.0:5433 failed: port is already allocated`
- `Bind for 0.0.0.0:8000 failed: port is already allocated`

**RULE 6.1.2: Solutions**
- CORRECT Use non-standard host ports (5433, 6380) in docker-compose
- CORRECT Check for existing containers using the port:
  ```bash
  docker ps -a --format "table {{.Names}}\t{{.Ports}}" | grep -E "5433|8000"
  ```
- CORRECT Stop conflicting containers:
  ```bash
  docker stop <container_name>
  ```
- CORRECT Or use different host ports in docker-compose.yml (e.g., `"5434:5432"` instead of `"5433:5432"`)
- CORRECT Clean up stopped containers:
  ```bash
  docker compose down
  docker ps -a --filter "name=<project_name>" --format "{{.ID}}" | xargs -r docker rm -f
  ```

**RULE 6.1.3: Port Conflict Prevention Rules**
- CORRECT Always check for port conflicts before starting services
- CORRECT Use non-standard host ports (5433, 6380) to avoid conflicts
- CORRECT Stop conflicting containers before starting new ones
- INCORRECT Use standard ports that conflict with local services

### 6.2 Database Connection Failed
**RULE 6.2.1: Error Description**
- Cannot connect to database
- Connection refused errors

**RULE 6.2.2: Solutions**
- CORRECT Verify DATABASE_URL password/username/dbname matches POSTGRES_PASSWORD/POSTGRES_USER/POSTGRES_DB
- CORRECT Check service name is `db` (not `postgres` or `database`)
- CORRECT Verify database service is healthy: `docker compose ps db`
- CORRECT Check database service is running: `docker compose ps`
- CORRECT Verify health check is passing

### 6.3 Tables Don't Exist
**RULE 6.3.1: Error Description**
- "relation does not exist"
- Table not found errors

**RULE 6.3.2: Solutions**
- CORRECT Ensure `migrate` service exists and `api`/`worker` depend on it with `condition: service_completed_successfully`
- CORRECT Verify migrate service completed successfully: `docker compose logs migrate`
- CORRECT Check that migrations ran: `docker compose logs migrate`
- CORRECT Verify migrate service has `restart: "no"`

### 6.4 Redis Data Lost on Container Restart
**RULE 6.4.1: Error Description**
- Redis keys disappear after `docker compose down` and `docker compose up`
- Redis cache is empty after container restart
- Permission cache or session data is lost

**RULE 6.4.2: Root Cause**
- Redis is running in-memory without persistence
- No volume mounted for Redis data
- AOF (Append Only File) or RDB snapshots not configured
- Volume not declared in `volumes` section

**RULE 6.4.3: Solutions**
- CORRECT Mount Redis volume: Add `volumes: - redis_data:/data` to Redis service
- CORRECT Declare volume: Add `redis_data:` to `volumes` section at bottom of docker-compose.yml
- CORRECT Enable AOF persistence: Include `--appendonly yes` in Redis command
- CORRECT Set AOF sync: Include `--appendfsync everysec` for balanced performance
- CORRECT Optionally enable RDB: Include `--save 60 1000` for snapshot backups
- CORRECT Verify volume exists: `docker volume ls | grep redis_data`
- CORRECT Check volume is mounted: `docker compose exec redis ls -la /data`
- INCORRECT Run Redis without volume (data will be lost)
- INCORRECT Forget to declare volume in volumes section (will cause error)

**RULE 6.4.4: Verification Steps**
```bash
# 1. Check if Redis volume exists
docker volume ls | grep redis_data

# 2. Check if volume is mounted in container
docker compose exec redis ls -la /data

# 3. Check if AOF file exists (should see appendonly.aof)
docker compose exec redis ls -la /data/appendonly.aof

# 4. Test persistence: Add key, restart container, check if key exists
docker compose exec redis redis-cli SET test_key "test_value"
docker compose restart redis
docker compose exec redis redis-cli GET test_key
# Should return "test_value" if persistence is working
```

**RULE 6.4.5: Prevention Rules**
- CORRECT Always mount Redis volume when using Redis for caching
- CORRECT Always enable AOF persistence for production use
- CORRECT Test persistence after configuration changes
- CORRECT Document Redis persistence requirements in project setup
- INCORRECT Assume Redis data persists without explicit configuration

---

## RULE 7: Verification Checklist
### 7.1 File Verification
**RULE 7.1.1: File Checklist**
- CORRECT Dockerfile exists
- CORRECT docker-compose.yml exists
- CORRECT NO `version` field in docker-compose.yml

### 7.2 Port Verification
**RULE 7.2.1: Port Checklist**
- CORRECT Port 5433 used for PostgreSQL host mapping (not 5432)
- CORRECT Port 6380 used for Redis host mapping (not 6379)
- CORRECT Port 8000 used for API (if not conflicting)

### 7.3 Service Verification
**RULE 7.3.1: Service Checklist**
- CORRECT Health checks configured for `db` and `redis`
- CORRECT `migrate` service exists and runs `alembic upgrade head`
- CORRECT `migrate` service has `restart: "no"`
- CORRECT `api` and `worker` depend on `migrate` with `condition: service_completed_successfully`
- CORRECT Redis service has volume mounted: `redis_data:/data`
- CORRECT Redis persistence enabled: `--appendonly yes` in command
- CORRECT `redis_data` volume declared in `volumes` section

### 7.4 Environment Variable Verification
**RULE 7.4.1: Environment Variable Checklist**
- CORRECT DATABASE_URL password/username/dbname matches POSTGRES_PASSWORD/POSTGRES_USER/POSTGRES_DB
- CORRECT All services use correct service names for internal communication
- CORRECT All environment variables use user-provided values (not placeholders)

## RULE 8: Integration with Existing Project
### 8.1 Integration Steps
**RULE 8.1.1: Step-by-Step Integration**
1. CORRECT Check if Dockerfile exists, create if not
2. CORRECT Check if docker-compose.yml exists
3. CORRECT If exists, verify it follows all rules above; if not, create new
4. CORRECT Ensure migrate service exists and is properly configured
5. CORRECT Verify all environment variables match between services
6. CORRECT Verify port mappings use non-standard host ports
7. CORRECT Verify health checks are configured
8. CORRECT Verify service dependencies are correct
9. CORRECT Verify Redis has volume mounted for persistence
10. CORRECT Verify Redis volume is declared in volumes section

**RULE 8.1.2: Integration Rules**
- CORRECT Review existing files before creating new ones
- CORRECT Enhance existing files if they don't follow patterns
- CORRECT Create new files only if they don't exist
- CORRECT Verify all configurations are correct after integration

## Summary
This guide provides rule-based instructions for setting up Docker and docker-compose configuration. Each rule is numbered and contains specific, actionable requirements.

**Key Principles:**
- Ask user for database credentials before proceeding
- Use non-standard host ports to avoid conflicts
- Include health checks for all services
- Ensure migrate service runs before api/worker
- Use consistent environment variables across services

**Critical Reminders:**
- DO NOT include `version` field in docker-compose.yml
- Use non-standard host ports (5433, 6380) to avoid conflicts
- MUST include migrate service with restart: "no"
- All services must depend on migrate with condition: service_completed_successfully
- DATABASE_URL must match POSTGRES_* environment variables exactly
- Use service names (db, redis) for internal container communication
- **CRITICAL: Redis MUST have volume mounted (`redis_data:/data`) for data persistence**
- **CRITICAL: Redis volume MUST be declared in volumes section**
- **CRITICAL: Without Redis volume, all cached data will be lost on container restart**
