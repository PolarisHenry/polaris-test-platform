from datetime import datetime
from typing import List, Tuple

from tortoise.expressions import Q

from app.core.crud import CRUDBase, Total
from app.models.enums import PlanStatus
from app.models.tp import TestPlan, TestPlanCase, TestPlanCaseStepResult
from app.schemas.tp import TestPlanCreate, TestPlanUpdate


class TestPlanController(CRUDBase[TestPlan, TestPlanCreate, TestPlanUpdate]):
    def __init__(self):
        super().__init__(model=TestPlan)

    async def list(self, page: int, page_size: int, search: Q = Q(), order: list = []) -> Tuple[Total, List[TestPlan]]:
        query = self.model.filter(search)
        total = await query.count()
        items = await query.offset((page - 1) * page_size).limit(page_size).order_by(*order).prefetch_related("creator")
        return total, items

    async def create_plan(self, obj_in: TestPlanCreate, creator_id: int) -> TestPlan:
        obj_dict = obj_in.model_dump(exclude={"case_ids"})
        obj_dict["creator_id"] = creator_id
        plan = self.model(**obj_dict)
        await plan.save()

        for case_id in obj_in.case_ids:
            await TestPlanCase.create(plan_id=plan.id, case_id=case_id)
        return plan

    async def update_plan(self, obj_in: TestPlanUpdate) -> TestPlan:
        obj_dict = obj_in.model_dump(exclude_unset=True, exclude={"id", "case_ids"})
        plan = await self.get(id=obj_in.id)
        plan.update_from_dict(obj_dict)
        await plan.save()

        if obj_in.case_ids is not None:
            await TestPlanCase.filter(plan_id=plan.id).delete()
            for case_id in obj_in.case_ids:
                await TestPlanCase.create(plan_id=plan.id, case_id=case_id)
        return plan

    async def execute(self, plan_id: int) -> TestPlan:
        plan = await self.get(id=plan_id)
        plan.status = PlanStatus.IN_PROGRESS
        plan.start_time = datetime.now()
        await plan.save()
        return plan

    async def complete(self, plan_id: int) -> TestPlan:
        plan = await self.get(id=plan_id)
        plan.status = PlanStatus.COMPLETED
        plan.end_time = datetime.now()
        await plan.save()
        return plan

    async def cancel(self, plan_id: int) -> TestPlan:
        plan = await self.get(id=plan_id)
        plan.status = PlanStatus.CANCELLED
        await plan.save()
        return plan

    async def update_case_result(self, plan_case_id: int, exec_result: str, executor_id: int = None) -> TestPlanCase:
        pc = await TestPlanCase.get(id=plan_case_id)
        pc.exec_result = exec_result
        pc.executed_at = datetime.now()
        if executor_id:
            pc.executor_id = executor_id
        await pc.save()
        return pc

    async def submit_manual_execution(
        self, plan_case_id: int, exec_result: str, executor_id: int, step_results: list, comment: str = ""
    ) -> TestPlanCase:
        pc = await TestPlanCase.get(id=plan_case_id)
        pc.exec_result = exec_result
        pc.executed_at = datetime.now()
        pc.executor_id = executor_id
        await pc.save()

        # 保存步骤执行结果
        await TestPlanCaseStepResult.filter(plan_case_id=plan_case_id).delete()
        for sr in step_results:
            await TestPlanCaseStepResult.create(
                plan_case_id=plan_case_id,
                step_number=sr.get("step_number", 0),
                actual_result=sr.get("actual_result", ""),
                step_exec_result=sr.get("step_exec_result", "pending"),
            )
        return pc

    async def get_case_execution_detail(self, plan_case_id: int) -> dict:
        pc = await TestPlanCase.get(id=plan_case_id).prefetch_related("case", "step_results")
        case = await pc.case
        step_results = await TestPlanCaseStepResult.filter(plan_case_id=plan_case_id).order_by("step_number")

        return {
            "plan_case_id": pc.id,
            "case_id": pc.case_id,
            "case_name": case.name if case else None,
            "exec_result": pc.exec_result,
            "executed_at": pc.executed_at,
            "executor_id": pc.executor_id,
            "step_results": [
                {
                    "id": sr.id,
                    "step_number": sr.step_number,
                    "actual_result": sr.actual_result,
                    "step_exec_result": sr.step_exec_result,
                }
                for sr in step_results
            ],
        }

    async def batch_execute(self, plan_case_ids: List[int]):
        for pc_id in plan_case_ids:
            pc = await TestPlanCase.get_or_none(id=pc_id)
            if pc:
                pc.exec_result = "pending"
                await pc.save()

    async def batch_change_executor(self, plan_case_ids: List[int], executor_id: int):
        await TestPlanCase.filter(id__in=plan_case_ids).update(executor_id=executor_id)

    async def batch_unlink(self, plan_id: int, plan_case_ids: List[int]):
        await TestPlanCaseStepResult.filter(plan_case_id__in=plan_case_ids).delete()
        await TestPlanCase.filter(id__in=plan_case_ids).delete()

    async def get_case_results(self, plan_id: int) -> dict:
        plan_cases = await TestPlanCase.filter(plan_id=plan_id).prefetch_related("case")
        cases = []
        counts = {"pending": 0, "success": 0, "fail": 0, "blocked": 0, "skipped": 0}
        for pc in plan_cases:
            case = await pc.case
            result = {
                "id": pc.id,
                "plan_id": pc.plan_id,
                "case_id": pc.case_id,
                "case_name": case.name if case else None,
                "exec_result": pc.exec_result,
                "executed_at": pc.executed_at,
                "executor_id": pc.executor_id,
            }
            cases.append(result)
            key = pc.exec_result.value if hasattr(pc.exec_result, "value") else str(pc.exec_result)
            if key in counts:
                counts[key] += 1

        total = len(cases)
        done = counts["success"] + counts["fail"] + counts["blocked"] + counts["skipped"]
        percent = round(done / total * 100, 1) if total > 0 else 0.0

        return {
            "cases": cases,
            "progress": {
                "total": total,
                "pending": counts["pending"],
                "success": counts["success"],
                "fail": counts["fail"],
                "blocked": counts["blocked"],
                "skipped": counts["skipped"],
                "percent": percent,
            },
        }

    async def generate_report(self, plan_id: int) -> dict:
        plan = await TestPlan.get(id=plan_id).prefetch_related("defects")
        results = await self.get_case_results(plan_id=plan_id)
        defects = await plan.defects.all()
        defect_count = len(defects)
        progress = results["progress"]

        pass_rate = round(progress["success"] / max(progress["total"] - progress["pending"], 1) * 100, 1)
        completion_rate = round(
            (progress["success"] + progress["fail"] + progress["blocked"]) / max(progress["total"], 1) * 100, 1
        )

        return {
            "plan_id": plan.id,
            "plan_name": plan.name,
            "total_cases": progress["total"],
            "passed": progress["success"],
            "failed": progress["fail"],
            "blocked": progress["blocked"],
            "skipped": progress.get("skipped", 0),
            "pending": progress["pending"],
            "pass_rate": pass_rate,
            "completion_rate": completion_rate,
            "defect_count": defect_count,
            "start_time": plan.start_time,
            "end_time": plan.end_time,
            "case_details": results["cases"],
        }


test_plan_controller = TestPlanController()
