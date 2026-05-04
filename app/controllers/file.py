import os
import uuid

from fastapi import UploadFile

from app.models.tp import File
from app.settings.config import settings


class FileController:
    def __init__(self):
        self.model = File

    async def upload(self, file: UploadFile, category: str, project_id: int, uploader_id: int) -> File:
        upload_dir = os.path.join(settings.BASE_DIR, "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        safe_name = os.path.basename(file.filename or "upload.bin")
        file_path = os.path.join(upload_dir, f"{uuid.uuid4().hex}_{safe_name}")
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        file_obj = await self.model.create(
            name=file.filename,
            path=file_path,
            size=len(contents),
            file_type=file.content_type,
            category=category,
            project_id=project_id,
            uploader_id=uploader_id,
        )
        return file_obj

    async def get(self, id: int) -> File:
        return await self.model.get(id=id)

    async def list(self, page: int, page_size: int, search=None):
        from tortoise.expressions import Q

        q = Q()
        if search:
            if "name" in search:
                q &= Q(name__contains=search["name"])
            if "category" in search:
                q &= Q(category=search["category"])
            if "project_id" in search:
                q &= Q(project_id=search["project_id"])
        query = self.model.filter(q)
        total = await query.count()
        items = (
            await query.offset((page - 1) * page_size)
            .limit(page_size)
            .order_by("-created_at")
            .prefetch_related("uploader")
        )
        return total, items

    async def remove(self, id: int):
        obj = await self.get(id=id)
        if os.path.exists(obj.path):
            os.remove(obj.path)
        await obj.delete()


file_controller = FileController()
