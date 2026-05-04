from fastapi import APIRouter

from .comments import router

comment_router = APIRouter()
comment_router.include_router(router, tags=["评论"])

__all__ = ["comment_router"]
