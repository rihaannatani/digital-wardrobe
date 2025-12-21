from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db.database import init_db
from app.routers.items import router as items_router

app = FastAPI(title="Digital Wardrobe")
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

app.include_router(items_router)

from app.routers.outfits import router as outfits_router
app.include_router(outfits_router)

from app.routers.outfits_ui import router as outfits_ui_router
app.include_router(outfits_ui_router)
