from fastapi import APIRouter

from .changehistories import router

change_history_router = APIRouter()
change_history_router.include_router(router, tags=["变更历史"])
