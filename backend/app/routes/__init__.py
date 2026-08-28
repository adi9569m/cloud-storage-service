"""API routes package assembling all endpoint sub-routers."""

from fastapi import APIRouter
from app.routes.auth import router as auth_router
from app.routes.folder import router as folder_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(folder_router)

__all__ = ["api_router", "auth_router", "folder_router"]
