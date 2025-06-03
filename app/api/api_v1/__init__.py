from fastapi import APIRouter
from .endpoints import auth as auth_endpoints

api_router = APIRouter()
api_router.include_router(auth_endpoints.router, prefix="/auth", tags=["auth"])

# Import and include other routers here
from .api import router as main_router
api_router.include_router(main_router)

__all__ = ["api_router"]
