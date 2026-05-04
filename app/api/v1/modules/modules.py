from fastapi import APIRouter, Query

from app.controllers.module import module_controller
from app.schemas.base import Success
from app.schemas.tp import ModuleCreate, ModuleMove, ModuleUpdate

router = APIRouter()


@router.get("/tree", summary="查看模块树")
async def get_module_tree(
    project_id: int = Query(..., description="项目ID"),
    name: str = Query("", description="模块名称筛选"),
):
    data = await module_controller.get_module_tree(project_id=project_id, name=name)
    return Success(data=data)


@router.get("/get", summary="查看模块")
async def get_module(id: int = Query(..., description="模块ID")):
    obj = await module_controller.get(id=id)
    return Success(data=await obj.to_dict())


@router.post("/create", summary="创建模块")
async def create_module(module_in: ModuleCreate):
    await module_controller.create_module(obj_in=module_in)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新模块")
async def update_module(module_in: ModuleUpdate):
    await module_controller.update_module(obj_in=module_in)
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除模块")
async def delete_module(module_id: int = Query(..., description="模块ID")):
    await module_controller.delete_module(module_id=module_id)
    return Success(msg="Deleted Successfully")


@router.post("/move", summary="移动模块（拖拽）")
async def move_module(move_in: ModuleMove):
    await module_controller.move_module(id=move_in.id, parent_id=move_in.parent_id, order=move_in.order)
    return Success(msg="Moved Successfully")


@router.get("/stats", summary="模块用例统计")
async def get_module_stats(project_id: int = Query(..., description="项目ID")):
    data = await module_controller.get_module_stats(project_id=project_id)
    return Success(data=data)
