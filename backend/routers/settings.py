from fastapi import APIRouter, HTTPException
from database import get_connection
from models import UserSettingsResponse, UserSettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("", response_model=UserSettingsResponse)
def get_user_settings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Settings not found")

    data = dict(row)
    data["notifications_enabled"] = bool(data.get("notifications_enabled", 1))
    return UserSettingsResponse(**data)

@router.patch("", response_model=UserSettingsResponse)
def update_user_settings(updates: UserSettingsUpdate):
    conn = get_connection()
    cursor = conn.cursor()

    update_data = updates.model_dump(exclude_unset=True)
    if "notifications_enabled" in update_data:
        update_data["notifications_enabled"] = 1 if update_data["notifications_enabled"] else 0

    if update_data:
        fields = [f"{k} = ?" for k in update_data.keys()]
        values = list(update_data.values())
        values.append(1)
        cursor.execute(f"UPDATE user_settings SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()

    cursor.execute("SELECT * FROM user_settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    data = dict(row)
    data["notifications_enabled"] = bool(data.get("notifications_enabled", 1))
    return UserSettingsResponse(**data)
