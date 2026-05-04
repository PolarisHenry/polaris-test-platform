from fastapi import APIRouter, Query

from app.controllers.defect_comment import defect_comment_controller
from app.core.ctx import CTX_USER_ID
from app.schemas.base import Success
from app.schemas.tp import DefectCommentCreate

router = APIRouter()


@router.get("/list", summary="缺陷评论列表")
async def list_comments(defect_id: int = Query(..., description="缺陷ID")):
    comments = await defect_comment_controller.get_comments(defect_id=defect_id)
    return Success(data=comments)


@router.post("/create", summary="创建评论")
async def create_comment(comment_in: DefectCommentCreate):
    user_id = CTX_USER_ID.get()
    await defect_comment_controller.create_comment(user_id=user_id, comment_in=comment_in)
    return Success(msg="Commented Successfully")


@router.delete("/delete", summary="删除评论")
async def delete_comment(comment_id: int = Query(..., description="评论ID")):
    await defect_comment_controller.remove(id=comment_id)
    return Success(msg="Deleted Successfully")
