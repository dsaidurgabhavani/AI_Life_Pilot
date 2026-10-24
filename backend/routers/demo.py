from fastapi import APIRouter
from database import seed_demo_data, clear_all_data

router = APIRouter(prefix="/api/demo", tags=["Demo Management"])

@router.post("/reset")
def reset_demo_data():
    seed_demo_data()
    return {"message": "Demo data has been successfully re-seeded with realistic tasks, habits, and focus sessions."}

@router.post("/clear")
def clear_user_data():
    clear_all_data()
    return {"message": "All tasks, habits, and focus sessions have been cleared."}
