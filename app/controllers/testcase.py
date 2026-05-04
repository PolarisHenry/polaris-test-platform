import csv
import io
import json
import zipfile
from datetime import datetime
from typing import List, Tuple
from xml.etree import ElementTree

from tortoise.expressions import Q

from app.core.crud import CRUDBase, Total
from app.models.enums import ReviewResult
from app.models.tp import TestCase, TestCaseStep
from app.schemas.tp import TestCaseCreate, TestCaseUpdate
from app.controllers.change_history import record_change


class TestCaseController(CRUDBase[TestCase, TestCaseCreate, TestCaseUpdate]):
    def __init__(self):
        super().__init__(model=TestCase)

    async def list(self, page: int, page_size: int, search: Q = Q(), order: list = []) -> Tuple[Total, List[TestCase]]:
        query = self.model.filter(search)
        total = await query.count()
        items = (
            await query.offset((page - 1) * page_size)
            .limit(page_size)
            .order_by(*order)
            .prefetch_related("steps", "module", "creator", "reviewer")
        )
        return total, items

    async def get(self, id: int) -> TestCase:
        return await self.model.get(id=id).prefetch_related("steps")

    async def create_case(self, obj_in: TestCaseCreate, creator_id: int) -> TestCase:
        obj_dict = obj_in.model_dump(exclude={"steps"})
        obj_dict["creator_id"] = creator_id
        case = self.model(**obj_dict)
        await case.save()

        for step_data in obj_in.steps:
            await TestCaseStep.create(
                test_case_id=case.id,
                step_number=step_data.step_number,
                action=step_data.action,
                expected_result=step_data.expected_result,
                sort_order=step_data.sort_order,
            )
        return case

    async def update_case(
        self, obj_in: TestCaseUpdate, check_re_review: bool = False, changed_by_id: int | None = None
    ) -> TestCase:
        obj_dict = obj_in.model_dump(exclude_unset=True, exclude={"id", "steps"})
        case = await self.get(id=obj_in.id)
        old_values = {field: getattr(case, field, None) for field in obj_dict.keys()}

        # 检查是否触发重新提审
        if check_re_review and case.review_result not in (None, ReviewResult.RESUBMIT):
            from app.models.tp import ReviewPlanCase

            in_review = await ReviewPlanCase.filter(case_id=case.id).exists()
            if in_review:
                obj_dict["review_result"] = ReviewResult.RESUBMIT

        case.update_from_dict(obj_dict)
        await case.save()
        if changed_by_id:
            for field, old_value in old_values.items():
                await record_change("testcase", case.id, field, old_value, obj_dict.get(field), changed_by_id)

        if obj_in.steps is not None:
            if changed_by_id:
                await record_change("testcase", case.id, "steps", "已保存步骤", "已更新步骤", changed_by_id)
            await TestCaseStep.filter(test_case_id=case.id).delete()
            for step_data in obj_in.steps:
                await TestCaseStep.create(
                    test_case_id=case.id,
                    step_number=step_data.step_number,
                    action=step_data.action,
                    expected_result=step_data.expected_result,
                    sort_order=step_data.sort_order,
                )
        return case

    async def soft_delete(self, ids: List[int]):
        """软删除用例 (移入回收站)"""
        await self.model.filter(id__in=ids).update(is_deleted=True, deleted_at=datetime.now())

    async def restore(self, ids: List[int]):
        """从回收站恢复用例"""
        await self.model.filter(id__in=ids).update(is_deleted=False, deleted_at=None)

    async def hard_delete(self, ids: List[int]):
        """彻底删除用例 (从回收站)"""
        await TestCaseStep.filter(test_case_id__in=ids).delete()
        await self.model.filter(id__in=ids).delete()

    async def get_recycle_bin(self, project_id: int) -> List[dict]:
        items = await self.model.filter(project_id=project_id, is_deleted=True).prefetch_related("module")
        result = []
        for item in items:
            module = await item.module
            result.append(
                {
                    "id": item.id,
                    "name": item.name,
                    "type": "testcase",
                    "deleted_at": getattr(item, "deleted_at", item.updated_at),
                    "module_name": module.name if module else None,
                    "level": item.level.value if hasattr(item.level, "value") else str(item.level),
                }
            )
        return result

    async def batch_delete(self, ids: List[int]):
        await self.model.filter(id__in=ids).delete()

    async def batch_review(self, ids: List[int], review_result: ReviewResult):
        await self.model.filter(id__in=ids).update(review_result=review_result)

    async def batch_update_module(self, ids: List[int], module_id: int):
        await self.model.filter(id__in=ids).update(module_id=module_id)

    async def update_exec_result(self, case_id: int, exec_result: str):
        case = await self.get(id=case_id)
        case.exec_result = exec_result
        await case.save()

    async def import_cases(
        self,
        filename: str,
        content: bytes,
        project_id: int,
        module_id: int | None,
        creator_id: int,
        overwrite: bool = False,
    ) -> dict:
        rows = self._parse_import_rows(filename=filename, content=content)
        created = 0
        updated = 0
        skipped = 0

        for row in rows:
            name = (row.get("name") or row.get("用例名称") or "").strip()
            if not name:
                skipped += 1
                continue
            case_module_id = self._safe_int(row.get("module_id") or row.get("模块ID")) or module_id
            level = (row.get("level") or row.get("用例等级") or "P2").strip() or "P2"
            precondition = row.get("precondition") or row.get("前置条件") or ""
            remark = row.get("remark") or row.get("备注") or ""
            tags_text = row.get("tags") or row.get("标签") or ""
            action = row.get("action") or row.get("步骤描述") or row.get("用例步骤") or ""
            expected = row.get("expected_result") or row.get("预期结果") or ""

            existing = await self.model.filter(project_id=project_id, name=name, is_deleted=False).first()
            if existing and not overwrite:
                skipped += 1
                continue

            payload = TestCaseCreate(
                name=name,
                module_id=case_module_id,
                project_id=project_id,
                level=level,
                precondition=precondition,
                remark=remark,
                tags=[tag.strip() for tag in str(tags_text).split(",") if tag.strip()],
                steps=(
                    [
                        {
                            "step_number": 1,
                            "action": action,
                            "expected_result": expected,
                            "sort_order": 0,
                        }
                    ]
                    if action or expected
                    else []
                ),
            )

            if existing:
                await self.update_case(TestCaseUpdate(id=existing.id, **payload.model_dump()))
                updated += 1
            else:
                await self.create_case(obj_in=payload, creator_id=creator_id)
                created += 1

        return {"created": created, "updated": updated, "skipped": skipped}

    def _parse_import_rows(self, filename: str, content: bytes) -> List[dict]:
        suffix = (filename or "").lower()
        if suffix.endswith(".csv"):
            return self._parse_csv(content)
        if suffix.endswith(".xlsx") or suffix.endswith(".xls"):
            return self._parse_xlsx(content)
        if suffix.endswith(".xmind"):
            return self._parse_xmind(content)
        return self._parse_csv(content)

    def _parse_csv(self, content: bytes) -> List[dict]:
        text = content.decode("utf-8-sig")
        return list(csv.DictReader(io.StringIO(text)))

    def _parse_xlsx(self, content: bytes) -> List[dict]:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            shared_strings = []
            if "xl/sharedStrings.xml" in zf.namelist():
                root = ElementTree.fromstring(zf.read("xl/sharedStrings.xml"))
                ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                for si in root.findall("x:si", ns):
                    shared_strings.append("".join(t.text or "" for t in si.findall(".//x:t", ns)))
            sheet_name = "xl/worksheets/sheet1.xml"
            if sheet_name not in zf.namelist():
                return []
            root = ElementTree.fromstring(zf.read(sheet_name))
            ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            matrix = []
            for row in root.findall(".//x:row", ns):
                values = []
                for cell in row.findall("x:c", ns):
                    value_node = cell.find("x:v", ns)
                    value = value_node.text if value_node is not None else ""
                    if cell.get("t") == "s" and value:
                        value = shared_strings[int(value)]
                    values.append(value)
                matrix.append(values)
            if not matrix:
                return []
            headers = matrix[0]
            return [dict(zip(headers, row)) for row in matrix[1:]]

    def _parse_xmind(self, content: bytes) -> List[dict]:
        rows = []
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            target = "content.json" if "content.json" in zf.namelist() else ""
            if not target:
                return rows
            data = json.loads(zf.read(target).decode("utf-8"))
        sheets = data if isinstance(data, list) else [data]
        for sheet in sheets:
            root = sheet.get("rootTopic") or sheet.get("root") or {}
            for module in self._topic_children(root):
                for case_topic in self._topic_children(module):
                    steps = self._topic_children(case_topic)
                    first_step = steps[0] if steps else {}
                    expected = self._topic_children(first_step)
                    rows.append(
                        {
                            "name": case_topic.get("title") or case_topic.get("text") or "",
                            "action": first_step.get("title") or first_step.get("text") or "",
                            "expected_result": (
                                (expected[0].get("title") or expected[0].get("text") or "") if expected else ""
                            ),
                        }
                    )
        return rows

    def _topic_children(self, topic: dict) -> List[dict]:
        children = topic.get("children") or {}
        if isinstance(children, dict):
            attached = children.get("attached")
            return attached if isinstance(attached, list) else []
        return children if isinstance(children, list) else []

    def _safe_int(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


test_case_controller = TestCaseController()
