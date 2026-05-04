from fastapi import APIRouter, Query

from app.controllers.review_plan import review_plan_controller
from app.core.ctx import CTX_USER_ID
from app.schemas.base import Success, SuccessExtra
from app.schemas.tp import (
    BatchDeleteRequest,
    BatchReviewRequest,
    ReviewPlanCaseSubmit,
    ReviewPlanCreate,
    ReviewPlanUpdate,
)

router = APIRouter()


async def _serialize_review_plan(obj):
    from app.models.tp import ReviewPlanCase, ReviewPlanReviewer

    data = await obj.to_dict(m2m=True)
    data["case_ids"] = list(await ReviewPlanCase.filter(plan_id=obj.id).values_list("case_id", flat=True))
    data["reviewers"] = [
        {
            "id": reviewer.user_id,
            "user_id": reviewer.user_id,
            "username": reviewer.user.username if reviewer.user else None,
        }
        for reviewer in await ReviewPlanReviewer.filter(plan_id=obj.id).prefetch_related("user")
    ]
    return data


@router.get("/list", summary="评审计划列表")
async def list_review_plans(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    name: str = Query("", description="评审名称"),
    project_id: int = Query(..., description="项目ID"),
    status: str = Query("", description="评审状态"),
    my_review: bool = Query(False, description="我评审的"),
    my_create: bool = Query(False, description="我创建的"),
):
    from tortoise.expressions import Q

    q = Q(project_id=project_id)
    if name:
        q &= Q(name__contains=name)
    if status:
        q &= Q(status=status)
    if my_create:
        q &= Q(creator_id=CTX_USER_ID.get())
    total, items = await review_plan_controller.list(page=page, page_size=page_size, search=q)
    data = []
    for obj in items:
        d = await _serialize_review_plan(obj)
        if my_review:
            from app.models.tp import ReviewPlanReviewer

            is_reviewer = await ReviewPlanReviewer.filter(plan_id=obj.id, user_id=CTX_USER_ID.get()).exists()
            if not is_reviewer:
                continue
        data.append(d)
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="评审计划详情")
async def get_review_plan(plan_id: int = Query(..., description="评审计划ID")):
    obj = await review_plan_controller.get_plan(id=plan_id)
    data = await _serialize_review_plan(obj)
    return Success(data=data)


@router.post("/create", summary="创建评审计划")
async def create_review_plan(plan_in: ReviewPlanCreate):
    creator_id = CTX_USER_ID.get()
    await review_plan_controller.create_plan(obj_in=plan_in, creator_id=creator_id)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新评审计划")
async def update_review_plan(plan_in: ReviewPlanUpdate):
    await review_plan_controller.update_plan(obj_in=plan_in)
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除评审计划")
async def delete_review_plan(plan_id: int = Query(..., description="评审计划ID")):
    await review_plan_controller.remove(id=plan_id)
    return Success(msg="Deleted Successfully")


@router.post("/start", summary="开始评审")
async def start_review(plan_id: int = Query(..., description="评审计划ID")):
    await review_plan_controller.start(plan_id=plan_id)
    return Success(msg="Started Successfully")


@router.post("/complete", summary="完成评审")
async def complete_review(plan_id: int = Query(..., description="评审计划ID")):
    await review_plan_controller.complete(plan_id=plan_id)
    return Success(msg="Completed Successfully")


@router.post("/cancel", summary="取消评审")
async def cancel_review(plan_id: int = Query(..., description="评审计划ID")):
    await review_plan_controller.cancel(plan_id=plan_id)
    return Success(msg="Cancelled Successfully")


@router.post("/copy", summary="复制评审计划")
async def copy_review_plan(plan_id: int = Query(..., description="评审计划ID")):
    creator_id = CTX_USER_ID.get()
    await review_plan_controller.copy_plan(plan_id=plan_id, creator_id=creator_id)
    return Success(msg="Copied Successfully")


@router.post("/link_cases", summary="关联用例")
async def link_cases(plan_id: int = Query(..., description="评审计划ID"), case_ids: list[int] = Query(...)):
    await review_plan_controller.link_cases(plan_id=plan_id, case_ids=case_ids)
    return Success(msg="Linked Successfully")


@router.post("/unlink_cases", summary="取消关联用例")
async def unlink_cases(plan_id: int = Query(..., description="评审计划ID"), case_ids: list[int] = Query(...)):
    await review_plan_controller.unlink_cases(plan_id=plan_id, case_ids=case_ids)
    return Success(msg="Unlinked Successfully")


@router.get("/case_results", summary="评审用例结果列表")
async def get_case_results(plan_id: int = Query(..., description="评审计划ID")):
    data = await review_plan_controller.get_case_results(plan_id=plan_id)
    return Success(data=data)


@router.post("/submit_review", summary="提交评审结果")
async def submit_review(submit: ReviewPlanCaseSubmit):
    reviewer_id = CTX_USER_ID.get()
    await review_plan_controller.submit_review(
        plan_case_id=submit.plan_case_id, review_result=submit.review_result, reviewer_id=reviewer_id
    )
    return Success(msg="Submitted Successfully")


@router.post("/batch_review", summary="批量评审")
async def batch_review(batch_in: BatchReviewRequest):
    """批量设置用例评审结果 (复用已有的批量评审)"""
    from app.controllers.testcase import test_case_controller

    await test_case_controller.batch_review(ids=batch_in.ids, review_result=batch_in.review_result)
    return Success(msg="Batch Review Successfully")
