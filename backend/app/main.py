from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database import Base, engine
from app.routers import recipes, meal_planner

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Recipe Extractor & Meal Planner",
    description="Extract structured recipe data from blog URLs using LLM and manage meal plans.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recipes.router)
app.include_router(meal_planner.router)

# Serve frontend static files if the frontend directory exists
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
