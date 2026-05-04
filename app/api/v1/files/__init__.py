from fastapi import APIRouter

from .files import router

file_router = APIRouter()
file_router.include_router(router, tags=["文件管理"])

__all__ = ["file_router"]
