from fastapi import APIRouter

from backend.api.endpoints import auth, uploads, search

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
