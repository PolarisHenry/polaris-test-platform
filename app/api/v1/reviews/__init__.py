from fastapi import APIRouter

from .reviews import router

review_router = APIRouter()
review_router.include_router(router, tags=["用例评审"])

__all__ = ["review_router"]
