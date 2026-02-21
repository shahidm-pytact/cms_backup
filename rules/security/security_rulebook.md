# 🔐 FastAPI Security Rulebook
### FastAPI + PostgreSQL + Celery + Redis
**Backend Security Audit Checklist & Cursor Rules | v1.0 | 2025**

---

## How to Use This Rulebook

Use each section as a checklist during code review, PRs, or AI-assisted development. Every rule maps to a real-world attack vector.

**Severity Levels:**
- 🔴 `CRITICAL` — Fix immediately, do not deploy
- 🟠 `HIGH` — Fix this sprint
- 🟡 `MEDIUM` — Plan for next release
- 🟢 `LOW` — Best practice / nice to have

---

## 1. SQL Injection (SQLi)

**What is it?** Attacker manipulates SQL queries through API parameters, form fields, or headers. Can lead to full database dump, data deletion, or auth bypass.

| Severity | Rule |
|----------|------|
| 🔴 CRITICAL | NEVER use raw f-strings in SQL queries: `cursor.execute(f"SELECT * FROM users WHERE id={id}")` |
| 🔴 CRITICAL | ALWAYS use parameterized queries or SQLAlchemy ORM |
| 🔴 CRITICAL | If using `text()`, always use `.bindparams()` — never string-format user input into it |
| 🟠 HIGH | Validate and sanitize all inputs with Pydantic models before they reach the DB layer |
| 🟠 HIGH | App DB user must NOT have `DROP`, `CREATE`, `ALTER` privileges — least privilege only |
| 🟡 MEDIUM | Enable `pg_audit` in PostgreSQL to log all queries for forensic analysis |

```python
# ❌ BAD
result = db.execute(f"SELECT * FROM users WHERE email='{email}'")

# ✅ GOOD
result = db.execute(text("SELECT * FROM users WHERE email=:email"), {"email": email})

# ✅ ALSO GOOD (ORM)
user = db.query(User).filter(User.email == email).first()
```

---

## 2. Broken Authentication & JWT Attacks

**What is it?** Weak authentication lets attackers impersonate users, bypass login, forge tokens, or brute-force credentials.

| Severity | Rule |
|----------|------|
| 🔴 CRITICAL | NEVER use `algorithm='none'` in JWT decode. Always specify `algorithms=['HS256']` |
| 🔴 CRITICAL | Verify JWT signature on EVERY protected route using `Depends()` with `oauth2_scheme` |
| 🔴 CRITICAL | `SECRET_KEY` must be ≥32 random chars. NEVER hardcode it — load from environment only |
| 🔴 CRITICAL | NEVER store plain text passwords. Use `bcrypt` or `argon2` via `passlib` |
| 🟠 HIGH | Rate limit `/login`, `/token`, `/register` endpoints (use `slowapi`) |
| 🟠 HIGH | Never log JWT tokens or Bearer headers |
| 🟠 HIGH | Set short expiry on access tokens (15–60 min). Use refresh token rotation |
| 🟠 HIGH | Rotate session/token on privilege change (login, password reset, role change) |
| 🟡 MEDIUM | Implement token blacklisting on logout using Redis (store invalidated JTIs) |

```python
# ❌ BAD
jwt.decode(token, SECRET_KEY)  # No algorithm — vulnerable to alg:none attack

# ✅ GOOD
jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

# ❌ BAD
SECRET_KEY = "mysecret"

# ✅ GOOD
SECRET_KEY = os.environ.get("SECRET_KEY")  # Load from .env

# ✅ Password hashing
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash(plain_password)
```

---

## 3. Broken Access Control (IDOR)

**What is it?** Insecure Direct Object Reference — attacker accesses other users' data by changing IDs in requests. Example: `GET /api/orders/1234` returns data for any logged-in user, not just the owner.

| Severity | Rule |
|----------|------|
| 🔴 CRITICAL | ALWAYS verify resource ownership: `resource.user_id == current_user.id` |
| 🔴 CRITICAL | NEVER trust client-supplied `user_id` in body/params for ownership — get it from JWT payload |
| 🔴 CRITICAL | Implement role-based checks on every endpoint using `Depends()` |
| 🟠 HIGH | Use UUIDs instead of sequential integer IDs to prevent enumeration |
| 🟠 HIGH | Use separate Pydantic schemas for input vs output — never expose internal fields |
| 🟠 HIGH | All `/admin/*` routes must validate `is_admin` from token, never from request body |

```python
# ❌ BAD — IDOR vulnerability
@app.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    return db.query(Order).filter(Order.id == order_id).first()
    # Anyone can access any order by guessing the ID!

# ✅ GOOD
@app.get("/orders/{order_id}")
def get_order(order_id: int, current_user=Depends(get_current_user), db=Depends(get_db)):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id  # Ownership check
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Not found")
    return order
```

---

## 4. Injection Attacks (XSS, Command Injection, SSTI)

| Severity | Rule |
|----------|------|
| 🔴 CRITICAL | NEVER use `subprocess` with `shell=True` and user input — use `shell=False` with a list |
| 🔴 CRITICAL | NEVER render user input directly in Jinja2 templates without escaping |
| 🔴 CRITICAL | NEVER use `jinja2.Environment().from_string()` with user-supplied template strings |
| 🟠 HIGH | Never return raw user HTML. Use `bleach` or `markupsafe` to sanitize |
| 🟠 HIGH | Set `Content-Security-Policy` headers using Starlette middleware |
| 🟠 HIGH | Strip newlines from any value going into HTTP response headers |
| 🟡 MEDIUM | Sanitize user input before logging — attackers can inject fake log lines |

```python
# ❌ BAD — Command Injection
import subprocess
subprocess.run(f"convert {user_filename} output.pdf", shell=True)

# ✅ GOOD
subprocess.run(["convert", user_filename, "output.pdf"], shell=False)

# ❌ BAD — SSTI
from jinja2 import Environment
env = Environment()
template = env.from_string(user_input)  # NEVER do this

# ✅ GOOD — Use autoescaping
from jinja2 import Environment, select_autoescape
env = Environment(autoescape=select_autoescape())
```

---

## 5. Celery Task Security

**What is it?** Celery workers execute background tasks. Attackers can exploit serialization, task injection, or privilege escalation through improperly secured task queues.

| Severity | Rule |
|----------|------|
| 🔴 CRITICAL | NEVER use `pickle` serializer — always set `task_serializer='json'` |
| 🔴 CRITICAL | NEVER allow untrusted input to determine task name or routing — whitelist allowed task names |
| 🔴 CRITICAL | Redis/RabbitMQ broker must require authentication — never expose on `0.0.0.0` without auth |
| 🟠 HIGH | Celery worker should run as a non-root OS user with minimal permissions |
| 🟠 HIGH | Rate limit task creation per user to prevent task flooding |
| 🟠 HIGH | Do not store PII or secrets in task results in Redis |
| 🟡 MEDIUM | Set `task_soft_time_limit` and `task_time_limit` to prevent resource exhaustion |

```python
# ✅ Required Celery security config
app.conf.update(
    task_serializer="json",
    accept_content=["json"],          # Reject pickle
    result_serializer="json",
    task_always_eager=False,          # Never True in production
    worker_hijack_root_logger=False,
    task_soft_time_limit=300,         # 5 min soft limit
    task_time_limit=360,              # 6 min hard limit
    broker_url=os.environ.get("CELERY_BROKER_URL"),  # Auth in URL
)

# ❌ BAD — Pickle deserialization (default in older Celery)
# accept_content=["pickle"]  # NEVER

# ❌ BAD — Letting user control task routing
task_name = request.json.get("task")  # Attacker can call any task!
app.send_task(task_name)

# ✅ GOOD — Whitelist allowed tasks
ALLOWED_TASKS = {"send_email", "generate_report"}
if task_name not in ALLOWED_TASKS:
    raise HTTPException(400, "Invalid task")
```

---

## 6. Redis Security

**What is it?** Redis is often misconfigured and exposed to the internet. Attackers can flush all data, read cached secrets, or use Redis as a pivot to write files on the server.

| Severity | Rule |
|----------|------|
| 🔴 CRITICAL | Redis must NEVER listen on `0.0.0.0` without firewall rules — bind to `127.0.0.1` only |
| 🔴 CRITICAL | Always set `requirepass` in `redis.conf` with a strong random password |
| 🟠 HIGH | Never cache sensitive data (passwords, PII, full JWT tokens) without encryption |
| 🟠 HIGH | Always set TTL (`EXPIRE`) on every cached key — never store keys with no expiry |
| 🟠 HIGH | Disable dangerous Redis commands via `rename-command` in `redis.conf` |
| 🟠 HIGH | Use prefixed key namespaces: `user:{id}:session`, `task:{id}:result` |
| 🟡 MEDIUM | Use TLS for Redis connections in production (Redis 6+ native TLS or stunnel) |

```bash
# redis.conf — required security settings
bind 127.0.0.1
requirepass YourStrongRandomPasswordHere
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command CONFIG ""
rename-command DEBUG ""
rename-command SLAVEOF ""
```

```python
# ✅ Always set TTL
redis_client.setex(f"session:{user_id}", 3600, session_token)  # 1 hour TTL

# ❌ BAD — No TTL, data lives forever
redis_client.set(f"session:{user_id}", session_token)
```

---

## 7. API-Level Attacks

### 7.1 Rate Limiting & DoS

| Severity | Rule |
|----------|------|
| 🔴 CRITICAL | Implement rate limiting on ALL public endpoints using `slowapi` or nginx |
| 🔴 CRITICAL | Set max request body size to prevent memory exhaustion |
| 🟠 HIGH | Set timeouts in uvicorn: `--timeout-keep-alive 5` |
| 🟠 HIGH | Validate max string lengths in all Pydantic models |

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute per IP
async def login(request: Request, ...):
    ...
```

### 7.2 CORS Misconfiguration

| Severity | Rule |
|----------|------|
| 🔴 CRITICAL | NEVER set `allow_origins=["*"]` WITH `allow_credentials=True` — this is a browser exploit |
| 🟠 HIGH | Whitelist only specific trusted origins |
| 🟠 HIGH | Only allow required HTTP methods — don't expose DELETE/PUT on read-only APIs |

```python
# ❌ BAD — Critical security misconfiguration
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True)  # This bypasses same-origin policy!

# ✅ GOOD
app.add_middleware(CORSMiddleware,
    allow_origins=["https://yourapp.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"])
```

### 7.3 Security Headers

| Severity | Rule |
|----------|------|
| 🔴 CRITICAL | Add `Strict-Transport-Security` (HSTS) in production |
| 🟠 HIGH | Add `X-Frame-Options: DENY` to prevent clickjacking |
| 🟠 HIGH | Add `Content-Security-Policy` header |
| 🟠 HIGH | Remove or genericize the `Server` header — don't leak framework version |
| 🟡 MEDIUM | Add `X-Content-Type-Options: nosniff` |

```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        del response.headers["server"]  # Hide server info
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

---

## 8. Sensitive Data Exposure

| Severity | Rule |
|----------|------|
| 🔴 CRITICAL | NEVER hardcode secrets, API keys, DB passwords in source code |
| 🔴 CRITICAL | Add `.env` to `.gitignore`. Run `gitleaks` or `trufflehog` in CI pipeline |
| 🔴 CRITICAL | Disable debug mode in production: never return stack traces to clients |
| 🟠 HIGH | Return generic error messages to clients — log detailed errors server-side only |
| 🟠 HIGH | Never log passwords, SSNs, credit cards, or full email addresses |
| 🟠 HIGH | Never accept API keys in query parameters — use `Authorization: Bearer` header |
| 🟠 HIGH | Catch Pydantic `ValidationError` and return a generic message — schema can be exposed |
| 🟠 HIGH | Encrypt database backups — never store in public S3 buckets |

```python
# ❌ BAD — Leaks stack trace and internal info to client
@app.exception_handler(Exception)
async def generic_handler(request, exc):
    return JSONResponse({"error": str(exc), "traceback": traceback.format_exc()})

# ✅ GOOD
@app.exception_handler(Exception)
async def generic_handler(request, exc):
    logger.error(f"Unhandled error: {exc}", exc_info=True)  # Log server-side
    return JSONResponse({"error": "Internal server error"}, status_code=500)

# ✅ Catch Pydantic validation errors
from pydantic import ValidationError
@app.exception_handler(ValidationError)
async def validation_handler(request, exc):
    return JSONResponse({"error": "Invalid input"}, status_code=422)
```

---

## 9. File Upload Vulnerabilities

| Severity | Rule |
|----------|------|
| 🔴 CRITICAL | Validate file type by **magic bytes**, not just extension — use `python-magic` |
| 🔴 CRITICAL | NEVER use user-supplied filenames directly — use `uuid4()` for stored filenames |
| 🔴 CRITICAL | Never store uploaded files in a web-accessible directory where they can be executed |
| 🟠 HIGH | Set maximum file size limit — reject oversized files before loading into memory |
| 🟠 HIGH | Scan uploaded files with ClamAV or VirusTotal API before accepting |
| 🟡 MEDIUM | If accepting ZIP/tar, check decompressed size before extracting (zip bomb defense) |

```python
import magic
import uuid

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@app.post("/upload")
async def upload_file(file: UploadFile):
    # Check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")

    # ✅ Validate by magic bytes, not extension
    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, "Invalid file type")

    # ✅ Use UUID for filename — never user-supplied name
    safe_filename = f"{uuid.uuid4()}.{mime_type.split('/')[1]}"
    save_path = UPLOAD_DIR / safe_filename  # UPLOAD_DIR not web-accessible
    ...
```

---

## 10. Supply Chain & Dependency Attacks

| Severity | Rule |
|----------|------|
| 🟠 HIGH | Pin all dependency versions in `requirements.txt` with hashes |
| 🟠 HIGH | Run `pip audit` or `safety check` in CI/CD pipeline on every build |
| 🟠 HIGH | Verify package names carefully — typosquatting is common (`requets` vs `requests`) |
| 🟠 HIGH | Use official minimal Docker base images (`python:3.12-slim`) |
| 🟠 HIGH | Never run application as root in Docker — use `USER` directive |
| 🟡 MEDIUM | Use Dependabot or Renovate Bot for automated security update PRs |

```dockerfile
# ❌ BAD
FROM python:3.12
RUN pip install -r requirements.txt
# App runs as root

# ✅ GOOD
FROM python:3.12-slim
RUN useradd -m -u 1000 appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser . .
USER appuser  # Non-root user
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Add to CI/CD pipeline
pip audit                          # Check for known vulnerabilities
pip install pip-audit && pip-audit # Alternative
```

---

## 11. Infrastructure & PostgreSQL Security

| Severity | Rule |
|----------|------|
| 🔴 CRITICAL | PostgreSQL must NOT be accessible from the public internet |
| 🔴 CRITICAL | Change default `postgres` user password — create an app-specific DB user |
| 🔴 CRITICAL | App DB user: `GRANT SELECT, INSERT, UPDATE, DELETE` only on required tables — NO superuser |
| 🟠 HIGH | Enforce SSL connections: `sslmode=require` in connection string |
| 🟠 HIGH | Encrypt all database backups at rest and in transit |
| 🟡 MEDIUM | Enable `pg_audit` or PostgreSQL logging to track all queries |
| 🟡 MEDIUM | Use pgBouncer connection pooling — set `max_connections` appropriately |

```sql
-- ✅ Least privilege DB setup
CREATE USER app_user WITH PASSWORD 'StrongRandomPassword123!';
CREATE DATABASE appdb OWNER app_user;

-- Grant only required permissions on specific tables
GRANT SELECT, INSERT, UPDATE, DELETE ON users, orders, products TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- NEVER grant:
-- GRANT ALL PRIVILEGES ON DATABASE appdb TO app_user;
-- GRANT superuser TO app_user;
```

```python
# ✅ Connection string with SSL
DATABASE_URL = "postgresql://app_user:password@localhost:5432/appdb?sslmode=require"
```

---

## 12. Server-Side Request Forgery (SSRF)

**What is it?** Attacker tricks your server into making HTTP requests to internal services (AWS metadata, Redis, internal APIs) by supplying malicious URLs.

| Severity | Rule |
|----------|------|
| 🔴 CRITICAL | Never fetch URLs directly from user input without validation |
| 🔴 CRITICAL | Block requests to private IP ranges: `10.x`, `172.16.x`, `192.168.x`, `169.254.x` (AWS metadata) |
| 🟠 HIGH | Maintain an allowlist of permitted external domains |
| 🟠 HIGH | Never use user-supplied URLs in Celery tasks for HTTP fetching |

```python
import ipaddress
import httpx
from urllib.parse import urlparse

ALLOWED_DOMAINS = {"api.trustedservice.com", "hooks.slack.com"}

def validate_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    if parsed.hostname in ALLOWED_DOMAINS:
        return True
    # Block private IPs
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except ValueError:
        pass
    return False
```

---

## 13. Mass Assignment & Input Validation

| Severity | Rule |
|----------|------|
| 🔴 CRITICAL | Never pass `**request.dict()` directly to ORM model constructors |
| 🟠 HIGH | Use separate Pydantic schemas: `UserCreate` (input) vs `UserResponse` (output) |
| 🟠 HIGH | Never expose `is_admin`, `role`, `password_hash` in response schemas |
| 🟠 HIGH | Always define `model_config = ConfigDict(from_attributes=True)` on response schemas |

```python
# ❌ BAD — Mass assignment
@app.post("/users")
def create_user(data: dict, db=Depends(get_db)):
    user = User(**data)  # Attacker can set is_admin=True!

# ✅ GOOD — Strict schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(max_length=100)
    # No is_admin field — user cannot set this

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    # No password_hash, no is_admin in output
    model_config = ConfigDict(from_attributes=True)
```

---

## 14. OWASP Top 10 — Attack Reference Matrix

| OWASP Category | FastAPI Stack Risk | Primary Defense |
|---|---|---|
| A01: Broken Access Control | IDOR, Privilege Escalation | Ownership checks, role `Depends()` |
| A02: Cryptographic Failures | Weak JWT, plain passwords | bcrypt, strong keys, HTTPS/TLS |
| A03: Injection | SQL, Command, SSTI | ORM, parameterized queries, no `shell=True` |
| A04: Insecure Design | Missing rate limits, no auth | Architecture review, threat modeling |
| A05: Security Misconfiguration | CORS `*`, debug on, default creds | Env config, security headers |
| A06: Vulnerable Components | Outdated packages, CVEs | `pip audit` in CI, pinned versions |
| A07: Auth Failures | Weak passwords, no MFA, no lockout | Strong policy, token rotation, rate limit |
| A08: Software Integrity Failures | Pickle deserialization, supply chain | JSON serializer, hash-pinned deps |
| A09: Logging Failures | No audit trail, PII in logs | Structured logging, `pg_audit` |
| A10: SSRF | Celery/webhooks fetching attacker URLs | URL allowlisting, private IP blocking |

---

## 15. .cursorrules File — Paste This Directly

```
# ============================================================
# FASTAPI SECURITY RULES FOR AI CODE GENERATION
# ============================================================

# === DATABASE (SQL INJECTION PREVENTION) ===
# NEVER use f-strings or string concatenation in SQL queries
# ALWAYS use SQLAlchemy ORM or parameterized queries with bindparams
# NEVER give the app DB user DROP/CREATE/ALTER privileges
# Use GRANT SELECT, INSERT, UPDATE, DELETE only on required tables

# === AUTHENTICATION & JWT ===
# Always specify algorithm in jwt.decode(): algorithms=['HS256']
# Load SECRET_KEY from env ONLY: os.environ.get('SECRET_KEY')
# Use bcrypt/argon2 for passwords via passlib — NEVER plain text or MD5/SHA1
# Set short JWT expiry (15-60 min) — use refresh token rotation
# Rate limit /login and /register with slowapi: @limiter.limit("5/minute")
# Never log JWT tokens or Authorization headers

# === ACCESS CONTROL ===
# ALWAYS verify resource ownership: resource.user_id == current_user.id
# NEVER trust client-supplied user_id for ownership — get from JWT payload only
# Use separate Pydantic schemas for input vs output — never expose internal fields
# Never pass **request.dict() directly to ORM model constructors (mass assignment)
# Use UUIDs for resource IDs instead of sequential integers

# === CELERY ===
# Always set task_serializer='json' — NEVER use pickle
# Always set task_soft_time_limit and task_time_limit
# Never let user input determine task name or routing — use a whitelist
# Celery broker must require authentication (set in CELERY_BROKER_URL)

# === REDIS ===
# Redis must bind to 127.0.0.1 only — never 0.0.0.0 without firewall
# Always requirepass in redis.conf with a strong password
# Always set TTL on every Redis key — never store without expiry
# Disable: FLUSHALL, FLUSHDB, CONFIG, DEBUG via rename-command in redis.conf
# Never store raw sensitive data — encrypt or hash PII in Redis

# === API SECURITY ===
# Rate limit ALL public endpoints with slowapi
# NEVER set CORS allow_origins=["*"] with allow_credentials=True
# Whitelist specific CORS origins: allow_origins=["https://yourapp.com"]
# Add security headers: CSP, X-Frame-Options, HSTS, X-Content-Type-Options
# Disable debug mode in production — NEVER return stack traces to clients
# Set max request body size to prevent DoS via large payload

# === FILE UPLOADS ===
# Validate file type by magic bytes — NEVER trust file extension alone
# Use uuid4() for stored filenames — NEVER use user-supplied filenames
# Never store uploaded files in a web-accessible or executable directory
# Set max file size limit before reading file into memory

# === SECRETS & CONFIGURATION ===
# NEVER hardcode secrets, API keys, DB passwords in source code
# Use .env + python-dotenv. Add .env to .gitignore
# Run `pip audit` in CI pipeline on every build
# Remove or override the Server response header to hide framework version

# === SSRF PREVENTION ===
# Never fetch user-supplied URLs without validating against an allowlist
# Block requests to private IP ranges: 10.x, 172.16.x, 192.168.x, 169.254.x
# Never use user-supplied URLs in Celery tasks for HTTP requests

# === DOCKER / INFRASTRUCTURE ===
# Never run application as root in Docker — use USER directive
# Use official minimal base images: python:3.12-slim
# PostgreSQL must NOT be accessible from public internet
# Enforce SSL for all DB connections: sslmode=require
```

---

## 16. Pre-Deployment Security Checklist

Run this before every production deployment:

- [ ] `pip audit` passes with no critical vulnerabilities
- [ ] `DEBUG=False` in production config
- [ ] All secrets loaded from environment variables — none hardcoded
- [ ] `.env` is in `.gitignore` and not committed
- [ ] JWT `SECRET_KEY` is ≥32 random characters
- [ ] JWT `algorithms` explicitly specified in decode
- [ ] Rate limiting active on `/login`, `/register`, `/token`
- [ ] CORS origins are an explicit whitelist — not `*`
- [ ] Security headers middleware is active (CSP, HSTS, X-Frame-Options)
- [ ] Redis has `requirepass` and binds to `127.0.0.1`
- [ ] Celery uses `task_serializer='json'` — no pickle
- [ ] PostgreSQL app user has minimal privileges (no superuser)
- [ ] All file uploads validated by magic bytes + UUID filenames
- [ ] Generic error responses to clients — detailed logs server-side only
- [ ] All resource endpoints have ownership validation
- [ ] `gitleaks` or `trufflehog` run on repository — no secrets in git history
- [ ] Docker container runs as non-root user

---

*Run this checklist on every PR. Security is everyone's responsibility.*
