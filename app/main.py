from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db.database import init_db
from app.routers.items import router as items_router
from app.routers.outfits import router as outfits_router
from app.routers.outfits_ui import router as outfits_ui_router
from app.routers.ingest_ui import router as ingest_ui_router  # <-- THIS is what you were missing

app = FastAPI(title="Digital Wardrobe")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "title": "Home"})

# routers
app.include_router(items_router)
app.include_router(outfits_router)
app.include_router(outfits_ui_router)
app.include_router(ingest_ui_router)
