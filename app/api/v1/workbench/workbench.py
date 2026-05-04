from fastapi import APIRouter, Query

from app.controllers.workbench import workbench_controller
from app.core.ctx import CTX_USER_ID
from app.schemas.base import Success

router = APIRouter()


@router.get("/stats", summary="工作台统计")
async def get_stats(project_id: int = Query(..., description="项目ID")):
    data = await workbench_controller.get_stats(project_id=project_id)
    return Success(data=data)


@router.get("/charts", summary="工作台图表数据")
async def get_charts(
    project_id: int = Query(..., description="项目ID"),
    time_range: str = Query("7d", description="时间范围(3d/7d/custom)"),
):
    data = await workbench_controller.get_charts(project_id=project_id, time_range=time_range)
    return Success(data=data)


@router.get("/my-items", summary="我的资产列表")
async def get_my_items(
    project_id: int = Query(..., description="项目ID"),
    tab: str = Query("created", description="标签页(created/followed/todos)"),
):
    user_id = CTX_USER_ID.get()
    data = await workbench_controller.get_my_items(user_id=user_id, project_id=project_id, tab=tab)
    return Success(data=data)
