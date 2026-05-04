from fastapi import APIRouter

from .follows import router

follow_router = APIRouter()
follow_router.include_router(router, tags=["关注"])

__all__ = ["follow_router"]
