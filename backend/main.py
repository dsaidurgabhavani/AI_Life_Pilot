import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import init_db
from routers import tasks, planner, habits, focus, assistant, analytics, settings, demo

app = FastAPI(
    title="AI LifePilot API",
    description="Intelligent Daily Life Assistant API for AI Website Build Sprint",
    version="1.0.0"
)

# CORS configuration for development and local production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to ensure database is created and seeded
@app.on_event("startup")
def startup_event():
    init_db()

# Include all REST API routers
app.include_router(tasks.router)
app.include_router(planner.router)
app.include_router(habits.router)
app.include_router(focus.router)
app.include_router(assistant.router)
app.include_router(analytics.router)
app.include_router(settings.router)
app.include_router(demo.router)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "AI LifePilot Backend"}

# Serve frontend build if dist directory exists
DIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(DIST_DIR):
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        # Don't intercept API routes or docs
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
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
