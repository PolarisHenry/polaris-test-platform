from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.defect import defect_controller
from app.core.ctx import CTX_USER_ID
from app.schemas.base import Success, SuccessExtra
from app.schemas.tp import DefectCreate, DefectStatusUpdate, DefectUpdate, DefectCreateFromFailure

router = APIRouter()


@router.get("/list", summary="查看缺陷列表")
async def list_defect(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    name: str = Query("", description="缺陷名称"),
    status: str = Query("", description="缺陷状态"),
    severity: str = Query("", description="严重程度"),
    handler_id: int = Query(None, description="处理人ID"),
    project_id: int = Query(..., description="项目ID"),
):
    q = Q(project_id=project_id)
    if name:
        q &= Q(name__contains=name)
    if status:
        q &= Q(status=status)
    if severity:
        q &= Q(severity=severity)
    if handler_id is not None:
        q &= Q(handler_id=handler_id)
    total, items = await defect_controller.list(page=page, page_size=page_size, search=q)
    data = []
    for obj in items:
        d = await obj.to_dict()
        d["related_case_ids"] = await defect_controller.get_related_case_ids(obj.id)
        data.append(d)
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看缺陷详情")
async def get_defect(defect_id: int = Query(..., description="缺陷ID")):
    from app.models.tp import TestCase

    obj = await defect_controller.get(id=defect_id)
    data = await obj.to_dict()
    related_case_ids = await defect_controller.get_related_case_ids(obj.id)
    data["related_case_ids"] = related_case_ids
    cases = await TestCase.filter(id__in=related_case_ids)
    data["related_cases"] = [
        {"id": case.id, "name": case.name, "level": case.level.value if hasattr(case.level, "value") else case.level}
        for case in cases
    ]
    return Success(data=data)


@router.post("/create", summary="创建缺陷")
async def create_defect(defect_in: DefectCreate):
    creator_id = CTX_USER_ID.get()
    await defect_controller.create_defect(obj_in=defect_in, creator_id=creator_id)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新缺陷")
async def update_defect(defect_in: DefectUpdate):
    await defect_controller.update_defect(obj_in=defect_in, changed_by_id=CTX_USER_ID.get())
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除缺陷")
async def delete_defect(defect_id: int = Query(..., description="缺陷ID")):
    await defect_controller.remove(id=defect_id)
    return Success(msg="Deleted Successfully")


@router.post("/update_status", summary="更新缺陷状态")
async def update_defect_status(status_in: DefectStatusUpdate):
    await defect_controller.update_status(defect_id=status_in.defect_id, status=status_in.status)
    return Success(msg="Updated Successfully")


@router.post("/create_from_failure", summary="从执行失败用例创建缺陷")
async def create_defect_from_failure(defect_in: DefectCreateFromFailure):
    creator_id = CTX_USER_ID.get()
    await defect_controller.create_from_failure(
        plan_id=defect_in.plan_id,
        case_id=defect_in.case_id,
        name=defect_in.name,
        creator_id=creator_id,
    )
    return Success(msg="Created Successfully")
