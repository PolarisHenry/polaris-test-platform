from tortoise.expressions import Q
from tortoise.transactions import atomic

from app.core.crud import CRUDBase
from app.models.tp import Module, ModuleClosure, TestCase
from app.schemas.tp import ModuleCreate, ModuleUpdate
from app.settings.config import settings

_conn = settings.TORTOISE_ORM["apps"]["models"]["default_connection"]


class ModuleController(CRUDBase[Module, ModuleCreate, ModuleUpdate]):
    def __init__(self):
        super().__init__(model=Module)

    async def get_module_tree(self, project_id: int, name: str = ""):
        q = Q(is_deleted=False, project_id=project_id)
        if name:
            q &= Q(name__contains=name)
        all_modules = await self.model.filter(q).order_by("order")

        def build_tree(parent_id):
            return [
                {
                    "id": m.id,
                    "name": m.name,
                    "desc": m.desc,
                    "order": m.order,
                    "parent_id": m.parent_id,
                    "project_id": m.project_id,
                    "children": build_tree(m.id),
                }
                for m in all_modules
                if m.parent_id == parent_id
            ]

        return build_tree(0)

    async def update_module_closure(self, obj: Module):
        parent_modules = await ModuleClosure.filter(descendant=obj.parent_id)
        closure_objs: list[ModuleClosure] = []
        for item in parent_modules:
            closure_objs.append(
                ModuleClosure(ancestor=item.ancestor, descendant=obj.id, level=item.level + 1)
            )
        closure_objs.append(ModuleClosure(ancestor=obj.id, descendant=obj.id, level=0))
        await ModuleClosure.bulk_create(closure_objs)

    @atomic(_conn)
    async def create_module(self, obj_in: ModuleCreate):
        if obj_in.parent_id != 0:
            await self.get(id=obj_in.parent_id)
        new_obj = await self.create(obj_in=obj_in)
        await self.update_module_closure(new_obj)

    @atomic(_conn)
    async def update_module(self, obj_in: ModuleUpdate):
        module_obj = await self.get(id=obj_in.id)
        parent_changed = module_obj.parent_id != obj_in.parent_id
        module_obj.update_from_dict(obj_in.model_dump(exclude_unset=True, exclude={"id"}))
        await module_obj.save()
        if parent_changed:
            await ModuleClosure.filter(ancestor=module_obj.id).delete()
            await ModuleClosure.filter(descendant=module_obj.id).delete()
            await self.update_module_closure(module_obj)

    @atomic(_conn)
    async def move_module(self, id: int, parent_id: int, order: int = 0):
        module_obj = await self.get(id=id)
        parent_changed = module_obj.parent_id != parent_id
        module_obj.parent_id = parent_id
        module_obj.order = order
        await module_obj.save()
        if parent_changed:
            await ModuleClosure.filter(ancestor=module_obj.id).delete()
            await ModuleClosure.filter(descendant=module_obj.id).delete()
            await self.update_module_closure(module_obj)

    @atomic(_conn)
    async def delete_module(self, module_id: int):
        obj = await self.get(id=module_id)
        obj.is_deleted = True
        await obj.save()
        await ModuleClosure.filter(descendant=module_id).delete()

    async def get_module_stats(self, project_id: int):
        modules = await self.model.filter(is_deleted=False, project_id=project_id).order_by("order")
        result = []
        for m in modules:
            descendants = await ModuleClosure.filter(ancestor=m.id).values_list("descendant", flat=True)
            count = await TestCase.filter(module_id__in=descendants).count()
            result.append({"id": m.id, "name": m.name, "case_count": count})
        # 统计未规划用例
        unplanned_count = await TestCase.filter(
            Q(project_id=project_id), Q(module_id__isnull=True) | Q(module_id=0)
        ).count()
        return {"modules": result, "unplanned_count": unplanned_count}


module_controller = ModuleController()
