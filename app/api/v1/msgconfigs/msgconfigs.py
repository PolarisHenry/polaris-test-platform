from fastapi import APIRouter, Query

from app.core.crud import CRUDBase
from app.models.tp import MessageConfig
from app.schemas.base import Success, SuccessExtra
from app.schemas.tp import MessageConfigCreate, MessageConfigUpdate

msg_config_controller = CRUDBase[MessageConfig, MessageConfigCreate, MessageConfigUpdate](
    model=MessageConfig
)

router = APIRouter()


@router.get("/list", summary="查看消息配置列表")
async def list_msg_config(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    project_id: int = Query(..., description="项目ID"),
):
    from tortoise.expressions import Q

    q = Q(project_id=project_id)
    total, items = await msg_config_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict() for obj in items]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/create", summary="创建消息配置")
async def create_msg_config(config_in: MessageConfigCreate):
    await msg_config_controller.create(obj_in=config_in)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新消息配置")
async def update_msg_config(config_in: MessageConfigUpdate):
    await msg_config_controller.update(id=config_in.id, obj_in=config_in)
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除消息配置")
async def delete_msg_config(config_id: int = Query(..., description="配置ID")):
    await msg_config_controller.remove(id=config_id)
    return Success(msg="Deleted Successfully")
