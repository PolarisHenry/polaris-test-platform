from fastapi import APIRouter

from .testplans import router

testplan_router = APIRouter()
testplan_router.include_router(router, tags=["测试计划"])

__all__ = ["testplan_router"]
