from fastapi import APIRouter, Form, Query, UploadFile

from app.controllers.testcase import test_case_controller
from app.core.ctx import CTX_USER_ID
from app.schemas.base import Success, SuccessExtra
from app.schemas.tp import (
    BatchDeleteRequest,
    BatchReviewRequest,
    BatchUpdateModuleRequest,
    ExecResultUpdate,
    TestCaseCreate,
    TestCaseUpdate,
)

router = APIRouter()


@router.get("/list", summary="查看用例列表")
async def list_test_case(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    name: str = Query("", description="用例名称"),
    module_id: int = Query(None, description="模块ID"),
    project_id: int = Query(..., description="项目ID"),
    level: str = Query("", description="用例等级"),
    status: str = Query("", description="用例状态"),
    review_result: str = Query("", description="评审结果"),
    exec_result: str = Query("", description="执行结果"),
):
    from tortoise.expressions import Q

    q = Q(project_id=project_id, is_deleted=False)
    if name:
        q &= Q(name__contains=name)
    if module_id is not None:
        q &= Q(module_id=module_id)
    if level:
        q &= Q(level=level)
    if status:
        q &= Q(status=status)
    if review_result:
        q &= Q(review_result=review_result)
    if exec_result:
        q &= Q(exec_result=exec_result)
    total, items = await test_case_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict(m2m=True) for obj in items]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看用例详情")
async def get_test_case(case_id: int = Query(..., description="用例ID")):
    obj = await test_case_controller.get(id=case_id)
    data = await obj.to_dict(m2m=True)
    return Success(data=data)


@router.post("/create", summary="创建用例")
async def create_test_case(case_in: TestCaseCreate):
    creator_id = CTX_USER_ID.get()
    await test_case_controller.create_case(obj_in=case_in, creator_id=creator_id)
    return Success(msg="Created Successfully")


@router.post("/import", summary="导入用例")
async def import_test_cases(
    file: UploadFile,
    project_id: int = Form(..., description="项目ID"),
    module_id: int | None = Form(None, description="默认模块ID"),
    overwrite: bool = Form(False, description="是否覆盖同名用例"),
):
    creator_id = CTX_USER_ID.get()
    content = await file.read()
    data = await test_case_controller.import_cases(
        filename=file.filename,
        content=content,
        project_id=project_id,
        module_id=module_id,
        creator_id=creator_id,
        overwrite=overwrite,
    )
    return Success(data=data, msg="Imported Successfully")


@router.post("/update", summary="更新用例")
async def update_test_case(case_in: TestCaseUpdate):
    await test_case_controller.update_case(obj_in=case_in, check_re_review=True, changed_by_id=CTX_USER_ID.get())
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除用例(移入回收站)")
async def delete_test_case(case_id: int = Query(..., description="用例ID")):
    await test_case_controller.soft_delete(ids=[case_id])
    return Success(msg="Deleted Successfully")


@router.post("/batch_delete", summary="批量删除用例(移入回收站)")
async def batch_delete(batch_in: BatchDeleteRequest):
    await test_case_controller.soft_delete(ids=batch_in.ids)
    return Success(msg="Deleted Successfully")


@router.get("/recycle_bin", summary="回收站列表")
async def list_recycle_bin(project_id: int = Query(..., description="项目ID")):
    items = await test_case_controller.get_recycle_bin(project_id=project_id)
    return Success(data=items)


@router.post("/restore", summary="从回收站恢复用例")
async def restore_cases(batch_in: BatchDeleteRequest):
    await test_case_controller.restore(ids=batch_in.ids)
    return Success(msg="Restored Successfully")


@router.post("/hard_delete", summary="彻底删除用例")
async def hard_delete_cases(batch_in: BatchDeleteRequest):
    await test_case_controller.hard_delete(ids=batch_in.ids)
    return Success(msg="Permanently Deleted")


@router.post("/batch_review", summary="批量评审用例")
async def batch_review(batch_in: BatchReviewRequest):
    await test_case_controller.batch_review(ids=batch_in.ids, review_result=batch_in.review_result)
    return Success(msg="Reviewed Successfully")


@router.post("/batch_update_module", summary="批量更新用例模块")
async def batch_update_module(batch_in: BatchUpdateModuleRequest):
    await test_case_controller.batch_update_module(ids=batch_in.ids, module_id=batch_in.module_id)
    return Success(msg="Updated Successfully")


@router.post("/update_exec_result", summary="更新执行结果")
async def update_exec_result(result_in: ExecResultUpdate):
    await test_case_controller.update_exec_result(case_id=result_in.case_id, exec_result=result_in.exec_result)
    return Success(msg="Updated Successfully")
