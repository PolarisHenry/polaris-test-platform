from fastapi import APIRouter, Query

from app.controllers.follow import follow_controller
from app.core.ctx import CTX_USER_ID
from app.schemas.base import Success
from app.schemas.tp import FollowCreate

router = APIRouter()


@router.post("/toggle", summary="关注/取消关注")
async def toggle_follow(follow_in: FollowCreate):
    user_id = CTX_USER_ID.get()
    result = await follow_controller.toggle(
        user_id=user_id, target_type=follow_in.target_type, target_id=follow_in.target_id
    )
    return Success(data=result, msg="Followed" if result["followed"] else "Unfollowed")


@router.get("/status", summary="检查关注状态")
async def check_follow_status(
    target_type: str = Query(..., description="目标类型"),
    target_id: int = Query(..., description="目标ID"),
):
    user_id = CTX_USER_ID.get()
    is_following = await follow_controller.is_following(
        user_id=user_id, target_type=target_type, target_id=target_id
    )
    return Success(data={"followed": is_following})


@router.get("/my_followed", summary="我关注的列表")
async def get_my_followed():
    user_id = CTX_USER_ID.get()
    items = await follow_controller.get_followed_items(user_id=user_id)
    return Success(data=items)
