import os

from fastapi import APIRouter, Form, Query, UploadFile
from fastapi.responses import FileResponse

from app.controllers.file import file_controller
from app.core.ctx import CTX_USER_ID
from app.schemas.base import Success, SuccessExtra
from app.schemas.tp import FileCategory

router = APIRouter()


@router.get("/list", summary="查看文件列表")
async def list_file(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    name: str = Query("", description="文件名"),
    category: str = Query("", description="文件分类"),
    project_id: int = Query(None, description="项目ID"),
):
    search = {}
    if name:
        search["name"] = name
    if category:
        search["category"] = category
    if project_id is not None:
        search["project_id"] = project_id
    total, items = await file_controller.list(page=page, page_size=page_size, search=search)
    data = [await obj.to_dict() for obj in items]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/upload", summary="上传文件")
async def upload_file(
    file: UploadFile,
    category: str = Form(FileCategory.COMMON, description="文件分类"),
    project_id: int | None = Form(None, description="项目ID"),
):
    uploader_id = CTX_USER_ID.get()
    file_obj = await file_controller.upload(
        file=file, category=category, project_id=project_id, uploader_id=uploader_id
    )
    return Success(data=await file_obj.to_dict(), msg="Uploaded Successfully")


@router.get("/download", summary="下载文件")
async def download_file(file_id: int = Query(..., description="文件ID")):
    file_obj = await file_controller.get(id=file_id)
    if not os.path.exists(file_obj.path):
        return Success(msg="File not found")
    return FileResponse(
        path=file_obj.path,
        filename=file_obj.name,
        media_type=file_obj.file_type or "application/octet-stream",
    )


@router.delete("/delete", summary="删除文件")
async def delete_file(file_id: int = Query(..., description="文件ID")):
    await file_controller.remove(id=file_id)
    return Success(msg="Deleted Successfully")
