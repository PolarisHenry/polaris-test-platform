from typing import Any

from app.models.tp import ChangeHistory


def stringify_change_value(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


async def record_change(
    target_type: str,
    target_id: int,
    field_name: str,
    old_value: Any,
    new_value: Any,
    changed_by_id: int,
):
    old_text = stringify_change_value(old_value)
    new_text = stringify_change_value(new_value)
    if old_text == new_text:
        return
    await ChangeHistory.create(
        target_type=target_type,
        target_id=target_id,
        field_name=field_name,
        old_value=old_text,
        new_value=new_text,
        changed_by_id=changed_by_id,
    )


class ChangeHistoryController:
    async def list(self, target_type: str, target_id: int) -> list[dict]:
        rows = (
            await ChangeHistory.filter(target_type=target_type, target_id=target_id)
            .order_by("-changed_at")
            .prefetch_related("changed_by")
        )
        result = []
        for row in rows:
            user = await row.changed_by
            result.append(
                {
                    "id": row.id,
                    "target_type": row.target_type,
                    "target_id": row.target_id,
                    "field_name": row.field_name,
                    "old_value": row.old_value,
                    "new_value": row.new_value,
                    "changed_by_id": row.changed_by_id,
                    "changed_by_name": user.username if user else None,
                    "changed_at": row.changed_at,
                }
            )
        return result


change_history_controller = ChangeHistoryController()
