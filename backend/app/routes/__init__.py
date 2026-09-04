from fastapi import APIRouter
from app.routes.auth import router as auth_router
from app.routes.folder import router as folder_router
from app.routes.file import router as file_router
from app.routes.share import router as share_router
from app.routes.link_share import router as link_share_router, public_router as public_link_router
from app.routes.star import router as star_router
from app.routes.activity import router as activity_router
from app.routes.trash import router as trash_router
from app.routes.search import router as search_router
from app.routes.storage import router as storage_router
from app.routes.batch import router as batch_router
from app.routes.tag import router as tag_router
from app.routes.comment import router as comment_router
from app.routes.maintenance import router as maintenance_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(folder_router)
api_router.include_router(file_router)
api_router.include_router(share_router)
api_router.include_router(link_share_router)
api_router.include_router(public_link_router)
api_router.include_router(star_router)
api_router.include_router(activity_router)
api_router.include_router(trash_router)
api_router.include_router(search_router)
api_router.include_router(storage_router)
api_router.include_router(batch_router)
api_router.include_router(tag_router)
api_router.include_router(comment_router)
api_router.include_router(maintenance_router)

__all__ = [
    "api_router",
    "auth_router",
    "folder_router",
    "file_router",
    "share_router",
    "link_share_router",
    "public_link_router",
    "star_router",
    "activity_router",
    "trash_router",
    "search_router",
    "storage_router",
    "batch_router",
    "tag_router",
    "comment_router",
    "maintenance_router",
]
