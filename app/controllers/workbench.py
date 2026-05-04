from datetime import datetime, timedelta

from tortoise.expressions import Q

from app.models.enums import DefectStatus, ReviewResult
from app.models.tp import Defect, TestCase, TestPlan


class WorkbenchController:
    def __init__(self):
        pass

    async def get_stats(self, project_id: int) -> dict:
        case_count = await TestCase.filter(project_id=project_id).count()
        review_count = await TestCase.filter(project_id=project_id, review_result__not_isnull=True).count()
        plan_count = await TestPlan.filter(project_id=project_id).count()
        defect_count = await Defect.filter(project_id=project_id).count()

        return {
            "case_count": case_count,
            "review_count": review_count,
            "plan_count": plan_count,
            "defect_count": defect_count,
        }

    async def get_charts(self, project_id: int, time_range: str = "7d") -> dict:
        # Case distribution by level
        levels = ["P0", "P1", "P2", "P3"]
        case_by_level = []
        for level in levels:
            count = await TestCase.filter(project_id=project_id, level=level).count()
            case_by_level.append({"label": level, "value": count})

        # Defect distribution by status
        defect_by_status = []
        for status in DefectStatus:
            count = await Defect.filter(project_id=project_id, status=status).count()
            defect_by_status.append({"label": status, "value": count})

        # Case growth trend
        case_by_week = []
        today = datetime.now().date()
        days = 3 if time_range == "3d" else 7
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            day_start = datetime.combine(day, datetime.min.time())
            day_end = datetime.combine(day + timedelta(days=1), datetime.min.time())
            count = await TestCase.filter(
                project_id=project_id,
                created_at__gte=day_start,
                created_at__lt=day_end,
            ).count()
            case_by_week.append({"label": day.strftime("%m-%d"), "value": count})

        # Defect by severity
        defect_by_severity = []
        for severity in ["trivial", "minor", "major", "critical"]:
            count = await Defect.filter(project_id=project_id, severity=severity).count()
            defect_by_severity.append({"label": severity, "value": count})

        return {
            "case_by_level": case_by_level,
            "defect_by_status": defect_by_status,
            "case_by_week": case_by_week,
            "defect_by_severity": defect_by_severity,
        }

    async def get_my_items(self, user_id: int, project_id: int, tab: str) -> list:
        result = []
        if tab == "created":
            plans = await TestPlan.filter(project_id=project_id, creator_id=user_id).limit(20)
            for p in plans:
                result.append(
                    {
                        "id": p.id,
                        "name": p.name,
                        "type": "plan",
                        "status": p.status,
                        "created_at": p.created_at,
                        "target_path": "/testplatform/testplan",
                    }
                )
            defects = await Defect.filter(project_id=project_id, creator_id=user_id).limit(20)
            for d in defects:
                result.append(
                    {
                        "id": d.id,
                        "name": d.name,
                        "type": "defect",
                        "status": d.status,
                        "created_at": d.created_at,
                        "target_path": "/testplatform/defect",
                    }
                )
            cases = await TestCase.filter(project_id=project_id, creator_id=user_id).limit(20)
            for c in cases:
                result.append(
                    {
                        "id": c.id,
                        "name": c.name,
                        "type": "case",
                        "status": c.status,
                        "created_at": c.created_at,
                        "target_path": f"/testplatform/testcase?case_id={c.id}",
                    }
                )
        elif tab == "todos":
            defects = (
                await Defect.filter(project_id=project_id, handler_id=user_id)
                .exclude(status__in=[DefectStatus.CLOSED, DefectStatus.RESOLVED])
                .limit(15)
            )
            for d in defects:
                result.append(
                    {
                        "id": d.id,
                        "name": d.name,
                        "type": "defect",
                        "status": d.status,
                        "created_at": d.created_at,
                        "target_path": "/testplatform/defect",
                    }
                )
            # 待评审用例：评审人为当前用户，且结果为「未评 / 不通过 / 重新提交 / 建议」
            pending_cases = (
                await TestCase.filter(
                    project_id=project_id,
                    reviewer_id=user_id,
                )
                .filter(
                    Q(review_result__isnull=True)
                    | Q(
                        review_result__in=[
                            ReviewResult.FAIL,
                            ReviewResult.RESUBMIT,
                            ReviewResult.SUGGEST,
                        ]
                    )
                )
                .limit(15)
            )
            for c in pending_cases:
                result.append(
                    {
                        "id": c.id,
                        "name": c.name,
                        "type": "case_review",
                        "status": c.review_result or "pending",
                        "created_at": c.updated_at or c.created_at,
                        "target_path": f"/testplatform/testcase?tab=review&case_id={c.id}",
                    }
                )
        return result


workbench_controller = WorkbenchController()
