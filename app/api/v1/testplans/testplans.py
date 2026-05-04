from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.testplan import test_plan_controller
from app.core.ctx import CTX_USER_ID
from app.schemas.base import Success, SuccessExtra
from app.schemas.tp import (
    BatchDeleteRequest,
    ExecResultUpdate,
    ManualExecSubmit,
    PlanCaseResultUpdate,
    PlanStatusUpdate,
    TestPlanCreate,
    TestPlanUpdate,
)

router = APIRouter()


async def _serialize_plan(obj):
    from app.models.tp import TestPlanCase

    data = await obj.to_dict()
    data["case_ids"] = list(await TestPlanCase.filter(plan_id=obj.id).values_list("case_id", flat=True))
    creator = await obj.creator
    data["creator_name"] = creator.username if creator else None
    plan_cases = await TestPlanCase.filter(plan_id=obj.id)
    total = len(plan_cases)
    passed = 0
    failed = 0
    blocked = 0
    skipped = 0
    pending = 0
    for plan_case in plan_cases:
        result = plan_case.exec_result.value if hasattr(plan_case.exec_result, "value") else str(plan_case.exec_result)
        if result == "success":
            passed += 1
        elif result == "fail":
            failed += 1
        elif result == "blocked":
            blocked += 1
        elif result == "skipped":
            skipped += 1
        else:
            pending += 1
    done = passed + failed + blocked + skipped
    data["progress"] = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "blocked": blocked,
        "skipped": skipped,
        "pending": pending,
        "completion_rate": round(done / total * 100, 1) if total else 0,
        "pass_rate": round(passed / max(done, 1) * 100, 1),
    }
    return data


@router.get("/list", summary="查看计划列表")
async def list_test_plan(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    name: str = Query("", description="计划名称"),
    status: str = Query("", description="计划状态"),
    project_id: int = Query(..., description="项目ID"),
):
    q = Q(project_id=project_id)
    if name:
        q &= Q(name__contains=name)
    if status:
        q &= Q(status=status)
    total, items = await test_plan_controller.list(page=page, page_size=page_size, search=q)
    data = [await _serialize_plan(obj) for obj in items]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看计划详情")
async def get_test_plan(plan_id: int = Query(..., description="计划ID")):
    obj = await test_plan_controller.get(id=plan_id)
    return Success(data=await _serialize_plan(obj))


@router.post("/create", summary="创建计划")
async def create_test_plan(plan_in: TestPlanCreate):
    creator_id = CTX_USER_ID.get()
    await test_plan_controller.create_plan(obj_in=plan_in, creator_id=creator_id)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新计划")
async def update_test_plan(plan_in: TestPlanUpdate):
    await test_plan_controller.update_plan(obj_in=plan_in)
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除计划")
async def delete_test_plan(plan_id: int = Query(..., description="计划ID")):
    await test_plan_controller.remove(id=plan_id)
    return Success(msg="Deleted Successfully")


@router.post("/execute", summary="执行测试计划")
async def execute_test_plan(plan_id: int = Query(..., description="计划ID")):
    await test_plan_controller.execute(plan_id=plan_id)
    return Success(msg="Execution Started")


@router.post("/complete", summary="完成测试计划")
async def complete_test_plan(plan_in: PlanStatusUpdate):
    await test_plan_controller.complete(plan_id=plan_in.plan_id)
    return Success(msg="Plan Completed")


@router.post("/cancel", summary="取消测试计划")
async def cancel_test_plan(plan_in: PlanStatusUpdate):
    await test_plan_controller.cancel(plan_id=plan_in.plan_id)
    return Success(msg="Plan Cancelled")


@router.get("/case_results", summary="计划用例执行结果")
async def get_case_results(plan_id: int = Query(..., description="计划ID")):
    data = await test_plan_controller.get_case_results(plan_id=plan_id)
    return Success(data=data)


@router.post("/update_case_result", summary="更新计划用例执行结果")
async def update_case_result(result_in: PlanCaseResultUpdate):
    executor_id = CTX_USER_ID.get()
    await test_plan_controller.update_case_result(
        plan_case_id=result_in.plan_case_id,
        exec_result=result_in.exec_result,
        executor_id=executor_id,
    )
    return Success(msg="Updated Successfully")


# ============== 手动执行相关 ==============
@router.post("/submit_manual_exec", summary="提交手动执行结果(含步骤)")
async def submit_manual_execution(submit: ManualExecSubmit):
    executor_id = CTX_USER_ID.get()
    step_results = [sr.model_dump() for sr in submit.step_results]
    await test_plan_controller.submit_manual_execution(
        plan_case_id=submit.plan_case_id,
        exec_result=submit.exec_result,
        executor_id=executor_id,
        step_results=step_results,
        comment=submit.comment,
    )
    return Success(msg="Submitted Successfully")


@router.get("/execution_detail", summary="查看用例执行详情(含步骤)")
async def get_execution_detail(plan_case_id: int = Query(..., description="计划-用例关联ID")):
    data = await test_plan_controller.get_case_execution_detail(plan_case_id=plan_case_id)
    return Success(data=data)


# ============== 批量操作 ==============
@router.post("/batch_execute", summary="批量执行")
async def batch_execute(batch_in: BatchDeleteRequest):
    await test_plan_controller.batch_execute(plan_case_ids=batch_in.ids)
    return Success(msg="Batch Execute Started")


@router.post("/batch_change_executor", summary="批量更换执行人")
async def batch_change_executor(ids: list[int] = Query(...), executor_id: int = Query(...)):
    await test_plan_controller.batch_change_executor(plan_case_ids=ids, executor_id=executor_id)
    return Success(msg="Batch Changed Executor")


@router.post("/batch_unlink", summary="批量取消关联")
async def batch_unlink(plan_id: int = Query(...), ids: list[int] = Query(...)):
    await test_plan_controller.batch_unlink(plan_id=plan_id, plan_case_ids=ids)
    return Success(msg="Batch Unlinked")


# ============== 报告生成 ==============
@router.get("/report", summary="生成测试报告")
async def generate_report(plan_id: int = Query(..., description="计划ID")):
    data = await test_plan_controller.generate_report(plan_id=plan_id)
    return Success(data=data)
