from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.project import project_controller
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.tp import ProjectCreate, ProjectUpdate

router = APIRouter()


@router.get("/list", summary="查看项目列表")
async def list_project(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    name: str = Query("", description="项目名称"),
    organization: str = Query("", description="所属组织"),
):
    q = Q(is_deleted=False)
    if name:
        q &= Q(name__contains=name)
    if organization:
        q &= Q(organization__contains=organization)
    total, items = await project_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict() for obj in items]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看项目")
async def get_project(project_id: int = Query(..., description="项目ID")):
    obj = await project_controller.get(id=project_id)
    data = await obj.to_dict()
    data["members"] = await project_controller.get_members(project_id)
    return Success(data=data)


@router.post("/create", summary="创建项目")
async def create_project(project_in: ProjectCreate):
    existing = await project_controller.get_by_name(project_in.name)
    if existing:
        return Fail(code=400, msg="项目名称已存在")
    await project_controller.create(obj_in=project_in)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新项目")
async def update_project(project_in: ProjectUpdate):
    await project_controller.update(id=project_in.id, obj_in=project_in)
    if project_in.member_ids:
        await project_controller.update_members(project_in.id, project_in.member_ids)
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除项目")
async def delete_project(project_id: int = Query(..., description="项目ID")):
    obj = await project_controller.get(id=project_id)
    obj.is_deleted = True
    await obj.save()
    return Success(msg="Deleted Successfully")


@router.get("/members", summary="查看项目成员")
async def get_members(project_id: int = Query(..., description="项目ID")):
    members = await project_controller.get_members(project_id)
    return Success(data=members)


@router.post("/members", summary="更新项目成员")
async def update_members(
    project_id: int = Query(..., description="项目ID"),
    member_ids: list[int] = Query([], description="成员用户ID列表"),
):
    await project_controller.update_members(project_id, member_ids)
    return Success(msg="Updated Successfully")
