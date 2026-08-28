from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router

BASE = Path(__file__).resolve().parents[2]
FRONTEND = BASE / "frontend"

app = FastAPI(title="NetraX — Criminal Network Analysis", version="0.1.0")
app.include_router(router)


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
