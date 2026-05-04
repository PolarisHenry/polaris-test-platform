from fastapi import APIRouter

from .modules import router

module_router = APIRouter()
module_router.include_router(router, tags=["模块管理"])

__all__ = ["module_router"]
