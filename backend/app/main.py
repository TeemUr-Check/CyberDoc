from pathlib import Path
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, tools
from app.config import get_settings

logger = logging.getLogger(__name__)

def _resolve_frontend_dir() -> Path:
    cfg = get_settings().frontend_dir
    if cfg:
        return Path(cfg)
    here = Path(__file__).resolve().parent
    for ancestor in (here.parent, here.parent.parent):
        candidate = ancestor / "frontend"
        if candidate.is_dir():
            return candidate
    return here.parent / "frontend"


FRONTEND_DIR = _resolve_frontend_dir()

app = FastAPI(
    title="CyberDoc Pro",
    version="3.0.0",
    description="AI-powered cybersecurity analysis platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(tools.router, prefix="/api")

# Create directories if they don't exist to prevent Starlette RuntimeError
# Wrapped in try-except for read-only filesystems (Docker :ro)
for d in ["assets", "css", "js"]:
    dir_path = FRONTEND_DIR / d
    try:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"Could not create directory {dir_path}: {e}")

app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


@app.get("/")
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/chat")
async def serve_chat():
    return FileResponse(FRONTEND_DIR / "chat.html")


@app.get("/tools")
async def serve_tools():
    return FileResponse(FRONTEND_DIR / "tools.html")
