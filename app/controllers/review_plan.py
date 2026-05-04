from datetime import datetime
from typing import List, Tuple

from tortoise.expressions import Q

from app.core.crud import CRUDBase, Total
from app.models.enums import PlanStatus, ReviewResult
from app.models.tp import ReviewPlan, ReviewPlanCase, ReviewPlanReviewer, TestCase
from app.schemas.tp import ReviewPlanCreate, ReviewPlanUpdate


class ReviewPlanController(CRUDBase[ReviewPlan, ReviewPlanCreate, ReviewPlanUpdate]):
    def __init__(self):
        super().__init__(model=ReviewPlan)

    async def list(
        self, page: int, page_size: int, search: Q = Q(), order: list = []
    ) -> Tuple[Total, List[ReviewPlan]]:
        query = self.model.filter(search)
        total = await query.count()
        items = (
            await query.offset((page - 1) * page_size)
            .limit(page_size)
            .order_by(*order)
            .prefetch_related("creator", "reviewers", "reviewers__user")
        )
        return total, items

    async def get_plan(self, id: int) -> ReviewPlan:
        return await self.model.get(id=id).prefetch_related("creator", "reviewers", "reviewers__user")

    async def create_plan(self, obj_in: ReviewPlanCreate, creator_id: int) -> ReviewPlan:
        obj_dict = obj_in.model_dump(exclude={"case_ids", "reviewer_ids"})
        obj_dict["creator_id"] = creator_id
        obj_dict["status"] = PlanStatus.DRAFT
        plan = self.model(**obj_dict)
        await plan.save()

        for uid in obj_in.reviewer_ids:
            await ReviewPlanReviewer.create(plan_id=plan.id, user_id=uid)

        for case_id in obj_in.case_ids:
            await ReviewPlanCase.create(plan_id=plan.id, case_id=case_id)
        return plan

    async def update_plan(self, obj_in: ReviewPlanUpdate) -> ReviewPlan:
        obj_dict = obj_in.model_dump(exclude_unset=True, exclude={"id", "case_ids", "reviewer_ids"})
        plan = await self.get(id=obj_in.id)
        plan.update_from_dict(obj_dict)
        await plan.save()

        if obj_in.reviewer_ids is not None:
            await ReviewPlanReviewer.filter(plan_id=plan.id).delete()
            for uid in obj_in.reviewer_ids:
                await ReviewPlanReviewer.create(plan_id=plan.id, user_id=uid)

        if obj_in.case_ids is not None:
            await ReviewPlanCase.filter(plan_id=plan.id).delete()
            for case_id in obj_in.case_ids:
                await ReviewPlanCase.create(plan_id=plan.id, case_id=case_id)
        return plan

    async def start(self, plan_id: int) -> ReviewPlan:
        plan = await self.get(id=plan_id)
        plan.status = PlanStatus.IN_PROGRESS
        await plan.save()
        return plan

    async def complete(self, plan_id: int) -> ReviewPlan:
        plan = await self.get(id=plan_id)
        plan.status = PlanStatus.COMPLETED
        await plan.save()
        return plan

    async def cancel(self, plan_id: int) -> ReviewPlan:
        plan = await self.get(id=plan_id)
        plan.status = PlanStatus.CANCELLED
        await plan.save()
        return plan

    async def copy_plan(self, plan_id: int, creator_id: int) -> ReviewPlan:
        """复制评审计划及其关联用例，评审状态全部重置"""
        original = await ReviewPlan.get(id=plan_id).prefetch_related("plan_cases", "reviewers")
        new_plan = ReviewPlan(
            name=f"{original.name} - 副本",
            review_mode=original.review_mode,
            status=PlanStatus.DRAFT,
            project_id=original.project_id,
            creator_id=creator_id,
            start_time=original.start_time,
            end_time=original.end_time,
            desc=original.desc,
            tags=original.tags,
        )
        await new_plan.save()

        for rev in original.reviewers:
            await ReviewPlanReviewer.create(plan_id=new_plan.id, user_id=rev.user_id)

        for pc in original.plan_cases:
            await ReviewPlanCase.create(plan_id=new_plan.id, case_id=pc.case_id)

        return new_plan

    async def link_cases(self, plan_id: int, case_ids: List[int]):
        for case_id in case_ids:
            exists = await ReviewPlanCase.filter(plan_id=plan_id, case_id=case_id).exists()
            if not exists:
                await ReviewPlanCase.create(plan_id=plan_id, case_id=case_id)

    async def unlink_cases(self, plan_id: int, case_ids: List[int]):
        await ReviewPlanCase.filter(plan_id=plan_id, case_id__in=case_ids).delete()

    async def submit_review(self, plan_case_id: int, review_result: ReviewResult, reviewer_id: int) -> ReviewPlanCase:
        pc = await ReviewPlanCase.get(id=plan_case_id)
        pc.review_result = review_result
        pc.reviewed_at = datetime.now()
        pc.reviewer_id = reviewer_id
        await pc.save()

        # 更新用例的评审结果
        case = await pc.case
        plan = await pc.plan

        if plan.review_mode == "single":
            # 单人模式: 直接更新用例评审结果
            case.review_result = review_result
            await case.save()
        else:
            # 多人模式: 所有评审人通过才算通过
            all_results = await ReviewPlanCase.filter(plan_id=plan.id, case_id=case.id).values_list(
                "review_result", flat=True
            )
            if None in all_results:
                # 还有人未评审
                pass
            elif ReviewResult.FAIL in all_results:
                case.review_result = ReviewResult.FAIL
                await case.save()
            else:
                case.review_result = ReviewResult.PASS
                await case.save()

        return pc

    async def get_case_results(self, plan_id: int) -> dict:
        plan_cases = await ReviewPlanCase.filter(plan_id=plan_id).prefetch_related("case", "reviewer")
        cases = []
        counts = {"unreviewed": 0, "pass_count": 0, "unpass_count": 0, "suggest": 0, "resubmit": 0}
        for pc in plan_cases:
            case = await pc.case
            reviewer = await pc.reviewer
            cases.append(
                {
                    "id": pc.id,
                    "plan_id": pc.plan_id,
                    "case_id": pc.case_id,
                    "case_name": case.name if case else None,
                    "review_result": pc.review_result,
                    "reviewed_at": pc.reviewed_at,
                    "reviewer_id": pc.reviewer_id,
                    "reviewer_name": reviewer.username if reviewer else None,
                }
            )
            if pc.review_result is None:
                counts["unreviewed"] += 1
            elif pc.review_result == ReviewResult.PASS:
                counts["pass_count"] += 1
            elif pc.review_result == ReviewResult.FAIL:
                counts["unpass_count"] += 1
            elif pc.review_result == ReviewResult.SUGGEST:
                counts["suggest"] += 1
            elif pc.review_result == ReviewResult.RESUBMIT:
                counts["resubmit"] += 1

        total = len(cases)
        done = total - counts["unreviewed"]
        percent = round(done / total * 100, 1) if total > 0 else 0.0

        return {
            "cases": cases,
            "progress": {
                "total": total,
                "unreviewed": counts["unreviewed"],
                "pass_count": counts["pass_count"],
                "unpass_count": counts["unpass_count"],
                "suggest": counts["suggest"],
                "resubmit": counts["resubmit"],
                "percent": percent,
            },
        }


review_plan_controller = ReviewPlanController()
