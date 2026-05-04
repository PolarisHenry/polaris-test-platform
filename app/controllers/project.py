from typing import List, Optional

from app.core.crud import CRUDBase
from app.models.tp import Project, ProjectMember
from app.schemas.tp import ProjectCreate, ProjectUpdate


class ProjectController(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    def __init__(self):
        super().__init__(model=Project)

    async def get_by_name(self, name: str) -> Optional[Project]:
        return await self.model.filter(name=name).first()

    async def update_members(self, project_id: int, member_ids: List[int]):
        project = await self.get(id=project_id)
        await ProjectMember.filter(project_id=project_id).delete()
        for user_id in member_ids:
            await ProjectMember.create(project_id=project_id, user_id=user_id)

    async def get_members(self, project_id: int):
        members = await ProjectMember.filter(project_id=project_id).prefetch_related("user")
        result = []
        for m in members:
            user = await m.user
            result.append({
                "id": m.id,
                "project_id": m.project_id,
                "user_id": m.user_id,
                "role": m.role,
                "username": user.username if user else None,
                "email": user.email if user else None,
            })
        return result


project_controller = ProjectController()
