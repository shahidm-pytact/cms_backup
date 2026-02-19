"""Main API router that includes all module routers."""
from fastapi import APIRouter

from src.auth.router import router as auth_router
from src.user.router import router as user_router
from src.roles.router import router as roles_router
from src.audit_logs.router import router as audit_logs_router
from src.cms.router import router as blogs_router

# Create main API router
api_router = APIRouter()

# Include module routers
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(roles_router)
api_router.include_router(audit_logs_router)
api_router.include_router(blogs_router)