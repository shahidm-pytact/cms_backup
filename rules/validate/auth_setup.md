# FastAPI Authentication Module

**Purpose:** Standards for implementing authentication module with proper layer separation and security.

## RULE 1: Module Structure

### 1.1 Standard Module Layout
**Required Files:**
```
auth/
├── router.py          # API endpoints only
├── schemas.py         # Pydantic models
├── models.py          # SQLAlchemy models
├── dependencies.py    # FastAPI dependencies
├── config.py          # Configuration & settings
├── constants.py       # Constants & messages
├── exceptions.py      # Custom exceptions
├── service.py         # Business logic layer
└── utils.py          # Helper functions
```

### 1.2 Layer Responsibilities
| Layer | Purpose | Contains | DO NOT |
|-------|---------|----------|--------|
| `router.py` | API endpoints | Route definitions | Business logic, DB queries, password hashing, token creation |
| `service.py` | Business logic | All business logic, DB operations | Request/response handling, HTTP status codes |
| `schemas.py` | Data validation | Pydantic models | Business logic |
| `models.py` | Database | SQLAlchemy models | Business logic, methods (except `__repr__`) |
| `dependencies.py` | Auth checks | FastAPI dependencies | - |
| `utils.py` | Helpers | Pure functions | Database access, global state |
| `exceptions.py` | Errors | Custom exceptions | Raising exceptions (only define) |
| `config.py` | Settings | Configuration | Hardcoded secrets |
| `constants.py` | Values | Constants | Functions or logic |

**Layer Separation Rules:**
- Keep each layer focused on its responsibility
- Use service layer for all business logic
- Use router layer only for route definitions
- DO NOT mix business logic with route definitions
- DO NOT put database queries in router layer

## RULE 2: Implementation Patterns

### 2.1 Router Pattern
**CORRECT Pattern:**
```python
from src.schemas import StandardResponse

@router.post("/register", response_model=StandardResponse[UserResponse])
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    service = AuthService(session)
    user = await service.create_user(user_data)
    return StandardResponse(data=user, message="User created successfully")
```

**Router Rules:**
- Define routes only, call service methods for business logic
- Return StandardResponse format, specify response_model in decorator
- DO NOT include business logic, database queries, password hashing, or token creation in router

**WRONG Pattern:**
```python
# INCORRECT - Business logic in router
@router.post("/register")
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    existing = await session.query(User).filter(User.email == user_data.email).first()  # INCORRECT
    if existing:
        raise HTTPException(...)  # INCORRECT
    hashed_password = get_password_hash(user_data.password)  # INCORRECT
```

### 2.2 Service Pattern
**CORRECT Pattern:**
```python
class AuthService:
    async def create_user(self, user_data: UserCreate) -> User:
        existing = await self.get_user_by_email(user_data.email)
        if existing:
            raise UserAlreadyExistsException()
        
        hashed_password = get_password_hash(user_data.password)
        db_user = User(email=user_data.email, hashed_password=hashed_password)
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user
```

**Service Rules:**
- All business logic, database operations, and validation logic in service layer
- Raise custom exceptions from service
- Return domain models (not schemas)
- DO NOT handle HTTP status codes or request/response formatting in service

### 2.3 Schema Pattern
**CORRECT Pattern:**
```python
from pydantic import BaseModel, EmailStr, Field, validator

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        return v
```

**Schema Rules:**
- Use Pydantic BaseModel for all schemas
- Use EmailStr for email fields, Field for validation constraints
- Use validators for custom validation
- Define separate schemas for create, update, and response

### 2.4 Model Pattern
**CORRECT Pattern:**
```python
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from uuid import UUID, uuid4

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True, default=uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Model Rules:**
- Use UUID for primary keys, server_default for timestamps
- Add indexes for frequently queried fields
- Use nullable=False for required fields
- DO NOT include business logic or methods (except `__repr__`) in models

### 2.5 Dependency Pattern
**CORRECT Pattern:**
```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/users/token", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not token:  # CRITICAL: Check if token is None before decoding
        raise UnauthenticatedError("Could not validate credentials")
    
    payload = decode_token(token)
    if payload is None:
        raise UnauthenticatedError("Could not validate credentials")
    
    user = await session.get(User, payload["sub"])
    if not user:
        raise UnauthenticatedError("Could not validate credentials")
    
    return user
```

**Dependency Rules:**
- Use OAuth2PasswordBearer for token extraction
- CRITICAL: Check if token is None before decoding
- Validate token payload, fetch user from database
- Raise custom exceptions for errors

### 2.6 Exception Pattern
**CORRECT Pattern:**
```python
from src.exceptions import NotFoundError, ConflictError, UnauthenticatedError

class UserNotFound(NotFoundError):
    def __init__(self, user_id: str):
        super().__init__(resource="User", resource_id=user_id)

class UserEmailExists(ConflictError):
    def __init__(self, email: str):
        super().__init__(
            message=f"User with email {email} already exists",
            error_code="DUPLICATE_EMAIL",
            details=[{"field": "email", "issue": email}]
        )
```

**Exception Rules:**
- Extend base exceptions from src.exceptions
- Provide meaningful error messages, error codes, and details
- DO NOT use HTTPException directly

### 2.7 Utility Pattern
**CORRECT Pattern:**
```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

**Utility Rules:**
- Use pure functions (no side effects)
- No database access or global state in utils
- Type hints for all functions
- DO NOT include database queries or business logic in utils

### 2.8 Config Pattern
**CORRECT Pattern:**
```python
from pydantic_settings import BaseSettings

class AuthSettings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }

auth_settings = AuthSettings()
```

**Config Rules:**
- Use Pydantic BaseSettings (with `model_config` dict for Pydantic v2)
- Type all fields, provide defaults where appropriate
- Load from .env file
- DO NOT hardcode secrets or use plain dictionaries for config

### 2.9 Constants Pattern
**CORRECT Pattern:**
```python
# Token Types
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

# Error Messages
ERROR_USER_NOT_FOUND = "User not found"
ERROR_INVALID_CREDENTIALS = "Invalid email or password"

# Success Messages
SUCCESS_USER_CREATED = "User created successfully"
```

**Constants Rules:**
- UPPER_CASE naming, group by category
- Use comments for sections, string literals only
- DO NOT include functions, logic, or computed values

## RULE 3: OAuth2PasswordBearer

### 3.1 OAuth2PasswordBearer Configuration
**CRITICAL RULE:** MUST use `OAuth2PasswordBearer` (NOT `HTTPBearer` or custom) for Swagger UI integration.

**CORRECT Pattern:**
```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/v1/users/token",  # MUST point to OAuth2 token endpoint
    auto_error=False              # Don't auto-raise if token missing
)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not token:  # CRITICAL: Check if token is None before decoding
        raise UnauthenticatedError("Could not validate credentials")
    # ... rest of validation
```

**OAuth2PasswordBearer Rules:**
- MUST use OAuth2PasswordBearer (enables Swagger UI "Authorize" button)
- MUST set tokenUrl to OAuth2-compatible token endpoint
- MUST set auto_error=False to handle None tokens gracefully
- MUST check if token is None before decoding
- DO NOT use HTTPBearer (no Swagger UI OAuth2 modal)
- DO NOT use manual header extraction (not standard)

## RULE 4: OAuth2 Token Endpoint

### 4.1 Token Endpoint Requirements
**CRITICAL RULE:** MUST create OAuth2-compatible token endpoint for Swagger UI.

**CORRECT Pattern:**
```python
@router.post("/token", status_code=status.HTTP_200_OK)
async def token(
    username: str = Form(...),  # OAuth2 uses 'username' but treat as email
    password: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    """OAuth2-compatible token endpoint for Swagger UI authorization"""
    try:
        service = UserService(session)
        user = await service.authenticate_user(username, password)
        tokens = await service.create_tokens(user)
        return {
            "access_token": tokens["access_token"],
            "token_type": "bearer"
        }
    except (InvalidCredentialsException, InactiveUserException):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

**Token Endpoint Rules:**
- Token endpoint MUST accept `Form(...)` parameters (not JSON)
- Token endpoint MUST return OAuth2-compatible response
- Token endpoint MUST handle errors in OAuth2 format
- Use `username` parameter (treat as email internally)
- Return `access_token` and `token_type` in response
- DO NOT use JSON body instead of Form parameters
- DO NOT return non-OAuth2-compatible response format

## RULE 5: bcrypt Version

### 5.1 bcrypt Version Requirement
**CRITICAL RULE:** MUST pin bcrypt to 4.0.1 (bcrypt 5.0.0 is incompatible with passlib 1.7.4).

**CORRECT Package Versions:**
```txt
# requirements/base.txt
passlib[bcrypt]==1.7.4
bcrypt==4.0.1  # CRITICAL: Pin to 4.0.1
```

**bcrypt Version Rules:**
- MUST pin bcrypt to 4.0.1
- Verify: `pip list | grep bcrypt` should show `bcrypt==4.0.1`
- DO NOT use bcrypt 5.0.0 with passlib 1.7.4
- DO NOT use unpinned bcrypt version

## RULE 6: Security Standards

### 6.1 Password Security
**Password Security Rules:**
- Use bcrypt for hashing, minimum 8 characters
- Require uppercase, lowercase, digit
- Never log passwords, use Field validation
- DO NOT use MD5 or SHA hashing
- DO NOT store plain passwords

### 6.2 JWT Standards
**JWT Token Rules:**
- Separate access & refresh tokens
- Short expiry for access (15-30 min)
- Longer expiry for refresh (7 days)
- Include token type in payload
- Verify token type on decode
- DO NOT use single token type
- DO NOT use long-lived access tokens

### 6.3 API Security
**API Security Rules:**
- Use OAuth2PasswordBearer, validate all inputs
- Use custom exceptions, rate limiting (production)
- CORS configuration
- DO NOT use basic auth
- DO NOT use generic error messages

## RULE 7: FastAPI App Initialization with Swagger UI Token Persistence

### 7.1 Swagger UI Authorization Token Persistence
**CRITICAL RULE:** MUST configure FastAPI app with `swagger_ui_parameters` to persist authorization tokens on page refresh.

**CORRECT Pattern:**
```python
# src/main.py
from fastapi import FastAPI
from src.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    swagger_ui_parameters={
        "persistAuthorization": True,  # Persist authorization token on page refresh
    },
)
```

**Swagger UI Parameters Rules:**
- MUST include `swagger_ui_parameters` in FastAPI app initialization
- MUST set `persistAuthorization: True` to persist tokens on page refresh
- Ensures users don't need to re-authenticate after refreshing Swagger UI page
- Works with OAuth2PasswordBearer and OAuth2 token endpoint
- DO NOT miss `swagger_ui_parameters` (tokens lost on page refresh)
- DO NOT set `persistAuthorization: False` (defeats the purpose)

## RULE 8: Common Mistakes

### 8.1 Common Mistakes Reference Table
| Mistake | Correct Approach |
|---------|------------------|
| Business logic in router | Move all logic to service layer |
| Database queries in router | Use service methods instead |
| Missing type hints | Add type hints everywhere |
| Hardcoded secrets | Use config.py with .env |
| Using HTTPException directly | Extend base exceptions |
| Using HTTPBearer | Use OAuth2PasswordBearer |
| Missing token endpoint | Create `/token` endpoint with Form params |
| bcrypt 5.0.0 | Pin bcrypt to 4.0.1 |
| No token None check | Always check `if not token:` before decoding |

## RULE 9: Naming Conventions

### 9.1 Naming Rules
- **File Naming:** `router.py`, `schemas.py`, `models.py`, `service.py` (NOT `auth_router.py`, `user_schemas.py`)
- **Function Naming:** `get_user_by_email(email: str) -> Optional[User]` (NOT `getUserByEmail(email)`)
- **Class Naming:** `AuthService`, `UserCreate`, `InvalidCredentialsException` (NOT `auth_service`, `createUser`)
- **Variable Naming:** `user_data: UserCreate`, `access_token: str` (NOT `userData`, `token`)

## RULE 10: HTTP Status Codes

### 10.1 Status Code Reference
| Status | When to use |
|--------|-------------|
| 200 | OK (GET, PUT) |
| 201 | Created (POST) |
| 204 | No Content (DELETE) |
| 400 | Bad Request |
| 401 | Unauthorized (authentication) |
| 403 | Forbidden (authorization) |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

**Status Code Rules:**
- Use appropriate status codes for each operation
- Use 401 for authentication errors, 403 for authorization errors
- Use 422 for validation errors, 404 for not found errors

## RULE 11: Verification Checklist

### 11.1 Module Structure
- [ ] Module structure follows standard layout
- [ ] All required files exist
- [ ] Files are properly organized

### 11.2 Layer Separation
- [ ] No business logic in routers
- [ ] No database queries in routers
- [ ] All business logic in service layer
- [ ] All database operations in service layer

### 11.3 OAuth2
- [ ] OAuth2PasswordBearer used (NOT HTTPBearer)
- [ ] Token endpoint created with Form params
- [ ] Token endpoint returns OAuth2-compatible response
- [ ] `auto_error=False` set on OAuth2PasswordBearer
- [ ] Token None check before decoding

### 11.4 Security
- [ ] bcrypt pinned to 4.0.1
- [ ] All exceptions extend base exceptions
- [ ] Type hints everywhere
- [ ] No hardcoded secrets
- [ ] Password validation in schemas
- [ ] JWT tokens with proper expiry

### 11.5 Swagger UI
- [ ] FastAPI app initialization includes `swagger_ui_parameters`
- [ ] `persistAuthorization` is set to `True`
- [ ] Token persists after refreshing Swagger UI page

## RULE 12: Golden Rules

### 12.1 Core Principles
1. Separation of Concerns - Each layer has ONE job
2. No Business Logic in Routers - Always use service layer
3. Type Everything - Use type hints everywhere
4. Custom Exceptions - Don't use generic HTTPException
5. Security First - Never compromise on security
6. OAuth2PasswordBearer - Required for Swagger UI
7. Token Endpoint - Required for OAuth2 flow
8. bcrypt 4.0.1 - Required for compatibility

**Golden Rules Application:**
- Apply all golden rules in every implementation
- Review code against golden rules before completion
- Use golden rules as checklist for verification

## Summary

This guide provides rule-based instructions for implementing authentication module with proper layer separation and security.

**Key Principles:**
- Separation of concerns - Each layer has one job
- Security first - Never compromise on security
- Type everything - Use type hints everywhere
- Custom exceptions - Don't use generic HTTPException

**Critical Reminders:**
- Use OAuth2PasswordBearer (not HTTPBearer) for Swagger UI
- Create OAuth2-compatible token endpoint with Form params
- Pin bcrypt to 4.0.1 (not 5.0.0)
- Always check token for None before decoding
- Keep all business logic in service layer
- Never put database queries in router layer
- Configure FastAPI app with `swagger_ui_parameters={"persistAuthorization": True}` to persist tokens on page refresh
