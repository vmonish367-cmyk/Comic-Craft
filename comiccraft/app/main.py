import os
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("comiccraft")

# Initialize FastAPI app instance
app = FastAPI(
    title="ComicCraft",
    description="Personalized 5-Panel AI Comic Book Generator & PDF Exporter",
    version="1.0.0"
)

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Ensure required static subdirectories exist
for sub in ["panels", "exports", "fonts"]:
    os.makedirs(os.path.join(STATIC_DIR, sub), exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include router from routes.py
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    logger.info("Starting ComicCraft on http://%s:%s", host, port)
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
