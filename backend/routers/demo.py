from fastapi import APIRouter
from database import clear_all_data

router = APIRouter(prefix="/api/demo", tags=["Data Management"])

@router.post("/reset")
def reset_demo_data():
    clear_all_data()
    return {"message": "All workspace data has been reset to a clean state."}

@router.post("/clear")
def clear_user_data():
    clear_all_data()
    return {"message": "All tasks, habits, and focus sessions have been cleared."}
