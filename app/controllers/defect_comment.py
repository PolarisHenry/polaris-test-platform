from typing import List

from app.core.crud import CRUDBase
from app.models.tp import DefectComment
from app.schemas.tp import DefectCommentCreate


class DefectCommentController(CRUDBase[DefectComment, DefectCommentCreate, DefectCommentCreate]):
    def __init__(self):
        super().__init__(model=DefectComment)

    async def get_comments(self, defect_id: int) -> List[dict]:
        comments = await DefectComment.filter(defect_id=defect_id).order_by("created_at").prefetch_related("user")
        result = []
        children_map = {}
        for c in comments:
            user = await c.user
            item = {
                "id": c.id,
                "defect_id": c.defect_id,
                "user_id": c.user_id,
                "username": user.username if user else None,
                "content": c.content,
                "parent_id": c.parent_id,
                "created_at": c.created_at,
                "replies": [],
            }
            if c.parent_id == 0:
                result.append(item)
            else:
                if c.parent_id not in children_map:
                    children_map[c.parent_id] = []
                children_map[c.parent_id].append(item)

        for item in result:
            if item["id"] in children_map:
                item["replies"] = children_map[item["id"]]
        return result

    async def create_comment(self, user_id: int, comment_in: DefectCommentCreate) -> DefectComment:
        comment = await DefectComment.create(
            defect_id=comment_in.defect_id,
            user_id=user_id,
            content=comment_in.content,
            parent_id=comment_in.parent_id,
        )
        return comment


defect_comment_controller = DefectCommentController()
