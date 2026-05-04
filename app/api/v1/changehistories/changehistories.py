from fastapi import APIRouter, Query

from app.controllers.change_history import change_history_controller
from app.schemas.base import Success

router = APIRouter()


@router.get("/list", summary="查看变更历史")
async def list_change_history(
    target_type: str = Query(..., description="目标类型(testcase/defect/plan)"),
    target_id: int = Query(..., description="目标ID"),
):
    data = await change_history_controller.list(target_type=target_type, target_id=target_id)
    return Success(data=data)
