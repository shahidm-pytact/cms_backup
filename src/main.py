"""FastAPI application entry point."""
import uuid
from typing import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    database_exception_handler,
    catch_all_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from sqlalchemy.exc import DatabaseError
from src.api.router import api_router
from src.database import engine

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager.
    
    Handles startup and shutdown tasks:
    - Startup: Any initialization needed
    - Shutdown: Dispose database engine to close all connections
    """
    # Startup
    yield
    # Shutdown: Dispose engine to ensure all connections are properly closed
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    debug=settings.debug,
    swagger_ui_parameters={
        "persistAuthorization": True,  # Persist authorization token on page refresh
    },
    lifespan=lifespan,
)


# Middleware: X-Request-ID
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next) -> Response:
    """Add X-Request-ID to request state and response headers."""
    # Generate or get X-Request-ID from header
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = f"req_{uuid.uuid4().hex[:12]}"
    
    # Store in request state
    request.state.request_id = request_id
    
    # Process request
    response = await call_next(request)
    
    # Set X-Request-ID header in response
    response.headers["X-Request-ID"] = request_id
    
    return response


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["ETag", "Last-Modified", "X-Request-ID"],  # Expose headers for frontend access
)


# Exception Handlers (order matters - most specific first)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(DatabaseError, database_exception_handler)
app.add_exception_handler(Exception, catch_all_exception_handler)

app.include_router(api_router, prefix=settings.api_prefix)

# Mount static files directory for serving images
static_dir = Path(settings.storage_base_path)
static_dir.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
