from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import UPLOADS_DIR, OUTPUTS_DIR
from app.api import health, logs, analysis

app = FastAPI(
    title="SonarAI API",
    description="Intelligent Side-Scan Sonar (SSS) Survey Analysis Platform Backend",
    version="1.0.0"
)

# Enable CORS for React frontend (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static file directories for uploaded SSS sonar images and generated output artifacts (masks, overlays, thumbnails)
app.mount("/api/storage/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/api/storage/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

# Include Routers
app.include_router(health.router)
app.include_router(logs.router)
app.include_router(analysis.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
