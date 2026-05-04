from fastapi import APIRouter

from .defects import router

defect_router = APIRouter()
defect_router.include_router(router, tags=["缺陷管理"])

__all__ = ["defect_router"]
