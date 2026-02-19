# Redis Setup Guide

**Purpose:** Essential setup instructions for Redis in a FastAPI project.

---

## RULE 1: Overview

### 1.1 Redis Usage

**RULE 1.1.1: Redis Use Cases**
- CORRECT Caching
- CORRECT Celery broker (message queue)
- CORRECT Celery result backend

**RULE 1.1.2: Redis Rules**
- CORRECT Redis is optional - only add if user explicitly requests
- CORRECT Redis is required if Celery is used
- CORRECT Redis can be used standalone for caching

---

## RULE 2: Redis Configuration

### 2.1 Step 1: Add Redis Settings

**RULE 2.1.1: Configuration Location**
- CORRECT Add Redis URL to `src/config.py`
- CORRECT Use Pydantic BaseSettings for configuration
- CORRECT Use service name `redis` for docker-compose internal communication

**RULE 2.1.2: Configuration Pattern**
```python
class Settings(BaseSettings):
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # ... other settings ...
```

**RULE 2.1.3: Configuration Rules**
- CORRECT Use service name `redis` for docker-compose internal communication
- CORRECT Use `localhost` or `127.0.0.1` for local development outside Docker
- CORRECT Format: `redis://[host]:[port]/[db_number]`
- CORRECT Use database number (e.g., `/0`) for Redis namespace

### 2.2 Step 2: Create Redis Client Module

**RULE 2.2.1: Redis Client Location**
- CORRECT Create `src/infra/cache_redis.py` for Redis client
- CORRECT Use async Redis client (`redis.asyncio`)
- CORRECT Implement singleton pattern with connection pooling

**RULE 2.2.2: Redis Client Pattern**
```python
import redis.asyncio as redis
from src.config import settings

# Redis connection pool
_redis_pool: redis.ConnectionPool | None = None
_redis_client: redis.Redis | None = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client singleton"""
    global _redis_pool, _redis_client
    
    if _redis_client is None:
        _redis_pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=50,
        )
        _redis_client = redis.Redis(connection_pool=_redis_pool)
    
    return _redis_client


async def close_redis():
    """Close Redis connection pool"""
    global _redis_client, _redis_pool
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
```

**RULE 2.2.3: Redis Client Rules**
- CORRECT Uses async Redis client (`redis.asyncio`)
- CORRECT Singleton pattern with connection pooling
- CORRECT `decode_responses=True` for automatic string decoding
- CORRECT Proper cleanup function for graceful shutdown
- CORRECT Connection pool with max_connections limit

### 2.3 Step 3: Redis Cleanup in main.py

**CRITICAL RULE:** You MUST register shutdown event in `src/main.py` to close Redis connections.

**RULE 2.3.1: Cleanup Pattern**
```python
from fastapi import FastAPI
from src.infra.cache_redis import close_redis

app = FastAPI(...)

@app.on_event("shutdown")
async def shutdown_event():
    await close_redis()
```

**RULE 2.3.2: Cleanup Rules**
- CORRECT MUST register shutdown event in `src/main.py`
- CORRECT Call `close_redis()` in shutdown event
- INCORRECT Without this, Redis connections will not be properly closed on application shutdown
- CORRECT Proper cleanup prevents connection leaks

### 2.4 Step 4: Add Redis to Requirements

**RULE 2.4.1: Package Requirements**
```txt
redis==5.0.1
```

**RULE 2.4.2: Package Rules**
- CORRECT Add `redis` package to `requirements/base.txt`
- CORRECT Pin Redis version for consistency
- CORRECT CRITICAL: If using `redis.asyncio`, you MUST have `redis` package installed
- INCORRECT Use unpinned Redis version

---

## RULE 3: Docker Compose Configuration

### 3.1 Redis Service Configuration

**RULE 3.1.1: Redis Service Pattern**
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"  # Non-standard host port to avoid conflicts
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru --save ""
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
```

**RULE 3.1.2: Redis Service Rules**
- CORRECT Port Mapping: Use `6380:6379` (not `6379:6379`) to avoid conflicts with local Redis
- CORRECT Memory Limits: `--maxmemory 256mb` limits memory usage
- CORRECT Persistence: `--appendonly yes` enables AOF persistence
- CORRECT Memory Policy: `--maxmemory-policy allkeys-lru` evicts least recently used keys
- CORRECT Background Saves: `--save ""` disables background saves to reduce overcommit warnings
- CORRECT Health Check: Ensures Redis is ready before dependent services start

### 3.2 Service Dependencies

**RULE 3.2.1: Dependency Pattern**
```yaml
api:
  depends_on:
    redis:
      condition: service_healthy
```

**RULE 3.2.2: Dependency Rules**
- CORRECT Services that use Redis should depend on it
- CORRECT Use `condition: service_healthy` for Redis dependency
- CORRECT Ensure Redis is ready before dependent services start
- INCORRECT Skip Redis health check in dependencies

---

## RULE 4: Common Issues & Solutions

### 4.1 Redis Memory Overcommit Warning

**RULE 4.1.1: Warning Description**
- Warning: "WARNING Memory overcommit must be enabled!"
- This is a warning, not an error

**RULE 4.1.2: Solution**
- CORRECT This is a warning, not an error - Redis will function normally
- CORRECT The docker-compose configuration with `--save ""` minimizes this warning
- CORRECT Can be safely ignored in development environments

### 4.2 Port Already in Use

**RULE 4.2.1: Error Description**
- Error: "address already in use" on port 6379

**RULE 4.2.2: Solution**
- CORRECT Use non-standard host port `6380:6379` in docker-compose
- CORRECT Container-to-container communication still uses port 6379 via service name
- CORRECT Check for existing containers using the port
- CORRECT Stop conflicting containers before starting new ones

### 4.3 Missing redis Package

**RULE 4.3.1: Error Description**
- Error: `ImportError: cannot import name 'asyncio' from 'redis'`

**RULE 4.3.2: Solution**
- CORRECT Ensure `redis==5.0.1` (or compatible version) is in `requirements/base.txt`
- CORRECT Verify package is installed: `pip list | grep redis`
- CORRECT Reinstall package if needed: `pip install redis==5.0.1`
- INCORRECT Missing redis package causes import errors

---

## RULE 5: Verification Checklist

### 5.1 Package Verification

**RULE 5.1.1: Package Checklist**
- CORRECT `redis` package added to `requirements/base.txt`
- CORRECT Package is installed and importable
- CORRECT No version conflicts with other packages

### 5.2 Configuration Verification

**RULE 5.2.1: Configuration Checklist**
- CORRECT `src/infra/cache_redis.py` exists with async client
- CORRECT Redis settings added to `src/config.py`
- CORRECT Redis URL is correctly configured
- CORRECT Cleanup function is implemented

### 5.3 Docker Compose Verification

**RULE 5.3.1: Docker Compose Checklist**
- CORRECT Redis service configured in `docker-compose.yml`
- CORRECT Health check configured for Redis service
- CORRECT Port mapping uses non-standard host port (6380)
- CORRECT Services that use Redis depend on it with health check condition

### 5.4 Application Integration Verification

**RULE 5.4.1: Application Checklist**
- CORRECT Redis cleanup registered in `src/main.py` shutdown event (calls `close_redis()`)
- CORRECT Redis client can be imported and used
- CORRECT Redis connections are properly closed on shutdown

---

## RULE 6: Integration with Existing Project

### 6.1 Integration Steps

**RULE 6.1.1: Step-by-Step Integration**
1. CORRECT Check if `src/infra/` directory exists, create if not
2. CORRECT Check if `src/infra/cache_redis.py` already exists
3. CORRECT If exists, review and enhance; if not, create new
4. CORRECT Add Redis settings to `src/config.py` if not present
5. CORRECT Add `redis` to `requirements/base.txt` if not present
6. CORRECT Add Redis service to `docker-compose.yml` if not present
7. CORRECT Update service dependencies to include Redis health check
8. CORRECT Register Redis cleanup in `src/main.py` shutdown event

**RULE 6.1.2: Integration Rules**
- CORRECT Review existing files before creating new ones
- CORRECT Enhance existing files if they don't follow patterns
- CORRECT Create new files only if they don't exist
- CORRECT Verify all dependencies are satisfied
- CORRECT Test Redis connection after integration

---

## Summary

This guide provides rule-based instructions for setting up Redis in a FastAPI project. Each rule is numbered and contains specific, actionable requirements.

**Key Principles:**
- Redis is optional - only add if user explicitly requests
- Use async Redis client with connection pooling
- Register cleanup in shutdown event
- Use non-standard host ports to avoid conflicts
- Configure health checks for service dependencies

**Critical Reminders:**
- MUST register Redis cleanup in `src/main.py` shutdown event
- MUST use non-standard host port (6380) to avoid conflicts
- MUST configure health checks for Redis service
- MUST add `redis` package to requirements
- MUST use async Redis client (`redis.asyncio`)
