from fastapi import APIRouter

from .testcases import router

testcase_router = APIRouter()
testcase_router.include_router(router, tags=["测试用例"])

__all__ = ["testcase_router"]
