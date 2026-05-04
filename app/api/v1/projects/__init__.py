from fastapi import APIRouter

from .projects import router

project_router = APIRouter()
project_router.include_router(router, tags=["项目管理"])

__all__ = ["project_router"]
