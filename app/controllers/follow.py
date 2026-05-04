from typing import List

from app.core.crud import CRUDBase
from app.models.tp import Follow
from app.schemas.tp import FollowCreate


class FollowController(CRUDBase[Follow, FollowCreate, FollowCreate]):
    def __init__(self):
        super().__init__(model=Follow)

    async def toggle(self, user_id: int, target_type: str, target_id: int) -> dict:
        existing = await Follow.filter(
            user_id=user_id, target_type=target_type, target_id=target_id
        ).first()
        if existing:
            await existing.delete()
            return {"followed": False}
        else:
            await Follow.create(
                user_id=user_id, target_type=target_type, target_id=target_id
            )
            return {"followed": True}

    async def is_following(self, user_id: int, target_type: str, target_id: int) -> bool:
        return await Follow.filter(
            user_id=user_id, target_type=target_type, target_id=target_id
        ).exists()

    async def get_followed_items(self, user_id: int) -> List[dict]:
        follows = await Follow.filter(user_id=user_id).order_by("-created_at")
        items = []
        for f in follows:
            item = {
                "id": f.id,
                "target_type": f.target_type,
                "target_id": f.target_id,
                "name": "",
                "status": "",
                "created_at": f.created_at,
            }
            if f.target_type == "testcase":
                from app.models.tp import TestCase
                obj = await TestCase.get_or_none(id=f.target_id)
                if obj:
                    item["name"] = obj.name
                    item["status"] = obj.status.value if hasattr(obj.status, 'value') else str(obj.status)
            elif f.target_type == "defect":
                from app.models.tp import Defect
                obj = await Defect.get_or_none(id=f.target_id)
                if obj:
                    item["name"] = obj.name
                    item["status"] = obj.status.value if hasattr(obj.status, 'value') else str(obj.status)
            elif f.target_type in ("plan", "review_plan"):
                from app.models.tp import TestPlan, ReviewPlan
                if f.target_type == "plan":
                    obj = await TestPlan.get_or_none(id=f.target_id)
                else:
                    obj = await ReviewPlan.get_or_none(id=f.target_id)
                if obj:
                    item["name"] = obj.name
                    item["status"] = obj.status.value if hasattr(obj.status, 'value') else str(obj.status)
            items.append(item)
        return items


follow_controller = FollowController()
