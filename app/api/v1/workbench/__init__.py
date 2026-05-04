from fastapi import APIRouter

from .workbench import router

workbench_router = APIRouter()
workbench_router.include_router(router, tags=["工作台"])

__all__ = ["workbench_router"]
