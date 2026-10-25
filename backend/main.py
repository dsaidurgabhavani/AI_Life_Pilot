import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import init_db, get_connection
from scheduler import start_scheduler, stop_scheduler
from routers import tasks, planner, habits, focus, assistant, analytics, settings, demo, reminders, external

def load_env_file(filepath: str):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("'\"")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception as e:
            print(f"Warning: could not read {filepath}: {e}")

# Load environment variables from root or backend directory if present
load_env_file(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_env_file(os.path.join(os.path.dirname(__file__), ".env"))

app = FastAPI(
    title="AI LifePilot API",
    description="Intelligent Daily Life Assistant API - Real-Time AI Productivity Platform",
    version="2.0.0"
)

# CORS configuration for development and local production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
def startup_event():
    init_db()
    start_scheduler()

@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()

# Include all REST API routers
app.include_router(tasks.router)
app.include_router(planner.router)
app.include_router(habits.router)
app.include_router(focus.router)
app.include_router(assistant.router)
app.include_router(analytics.router)
app.include_router(settings.router)
app.include_router(demo.router)
app.include_router(reminders.router)
app.include_router(external.router)

@app.get("/api/health")
def health_check():
    ai_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not ai_key:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT gemini_api_key FROM user_settings WHERE id = 1")
            row = cursor.fetchone()
            conn.close()
            if row and row["gemini_api_key"]:
                ai_key = row["gemini_api_key"].strip()
        except Exception:
            pass
    ai_configured = bool(ai_key)
    return {
        "status": "ok",
        "service": "AI LifePilot Backend",
        "version": "2.0.0",
        "ai_configured": ai_configured,
        "scheduler_active": True,
        "supported_tools": [
            "create_task",
            "list_tasks",
            "complete_task",
            "delete_task",
            "get_weather",
            "web_search",
            "create_reminder",
            "get_schedule",
            "get_current_time"
        ]
    }

# Serve frontend build if dist directory exists
DIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(DIST_DIR):
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            return {"error": "Endpoint not found"}
        file_path = os.path.join(DIST_DIR, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "app": "AI LifePilot API",
            "status": "online",
            "documentation": "/docs"
        }

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port)
