"""FastAPI application entrypoint for Cloud Storage Service."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.middleware import RequestTracingMiddleware, SecurityHeadersMiddleware
from app.routes import api_router

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Scalable Cloud-Based Media and File Storage Service REST API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure Middlewares (Security, Tracing, CORS)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestTracingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_router)


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint to verify backend operational readiness."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "0.1.0",
    }

