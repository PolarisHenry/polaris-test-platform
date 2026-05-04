from fastapi import APIRouter

from .msgconfigs import router

msgconfig_router = APIRouter()
msgconfig_router.include_router(router, tags=["消息配置"])

__all__ = ["msgconfig_router"]
