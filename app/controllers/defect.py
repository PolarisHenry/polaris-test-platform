from typing import List, Tuple

from tortoise.expressions import Q

from app.controllers.change_history import record_change
from app.core.crud import CRUDBase, Total
from app.models.tp import Defect, DefectCase, TestPlan, TestPlanCase
from app.schemas.tp import DefectCreate, DefectUpdate


class DefectController(CRUDBase[Defect, DefectCreate, DefectUpdate]):
    def __init__(self):
        super().__init__(model=Defect)

    async def list(self, page: int, page_size: int, search: Q = Q(), order: list = []) -> Tuple[Total, List[Defect]]:
        query = self.model.filter(search)
        total = await query.count()
        items = (
            await query.offset((page - 1) * page_size)
            .limit(page_size)
            .order_by(*order)
            .prefetch_related("creator", "handler")
        )
        return total, items

    async def get(self, id: int) -> Defect:
        return await self.model.get(id=id).prefetch_related("handler", "creator")

    async def create_defect(self, obj_in: DefectCreate, creator_id: int) -> Defect:
        obj_dict = obj_in.model_dump(exclude={"related_case_ids"})
        obj_dict["creator_id"] = creator_id
        defect = self.model(**obj_dict)
        await defect.save()

        for case_id in obj_in.related_case_ids:
            await DefectCase.create(defect_id=defect.id, case_id=case_id)
        return defect

    async def update_defect(self, obj_in: DefectUpdate, changed_by_id: int | None = None) -> Defect:
        obj_dict = obj_in.model_dump(exclude_unset=True, exclude={"id", "related_case_ids"})
        defect = await self.get(id=obj_in.id)
        old_values = {field: getattr(defect, field, None) for field in obj_dict.keys()}
        defect.update_from_dict(obj_dict)
        await defect.save()
        if changed_by_id:
            for field, old_value in old_values.items():
                await record_change("defect", defect.id, field, old_value, obj_dict.get(field), changed_by_id)

        if obj_in.related_case_ids is not None:
            if changed_by_id:
                old_case_ids = await self.get_related_case_ids(defect.id)
                await record_change(
                    "defect", defect.id, "related_case_ids", old_case_ids, obj_in.related_case_ids, changed_by_id
                )
            await DefectCase.filter(defect_id=defect.id).delete()
            for case_id in obj_in.related_case_ids:
                await DefectCase.create(defect_id=defect.id, case_id=case_id)
        return defect

    async def create_from_failure(self, plan_id: int, case_id: int, name: str, creator_id: int) -> Defect:
        """从计划执行失败的用例快速创建缺陷"""
        plan_case = await TestPlanCase.get_or_none(plan_id=plan_id, case_id=case_id)
        plan = await TestPlan.get_or_none(id=plan_id)
        project_id = plan.project_id if plan else None

        defect = self.model(
            name=name,
            status="new",
            severity="major",
            project_id=project_id,
            plan_id=plan_id,
            creator_id=creator_id,
        )
        await defect.save()
        await DefectCase.create(defect_id=defect.id, case_id=case_id)

        if plan_case:
            plan_case.exec_result = "fail"
            await plan_case.save()
        return defect

    async def get_related_case_ids(self, defect_id: int) -> List[int]:
        cases = await DefectCase.filter(defect_id=defect_id).values_list("case_id", flat=True)
        return list(cases)

    async def update_status(self, defect_id: int, status: str):
        defect = await self.get(id=defect_id)
        defect.status = status
        await defect.save()


defect_controller = DefectController()
