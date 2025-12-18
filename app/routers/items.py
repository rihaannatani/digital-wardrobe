from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db.database import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/items")
def items_list(request: Request):
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM items ORDER BY id DESC").fetchall()
        items = [dict(r) for r in rows]
    finally:
        conn.close()
    return templates.TemplateResponse("items_list.html", {"request": request, "items": items, "title": "Wardrobe"})

@router.get("/items/new")
def item_new_form(request: Request):
    return templates.TemplateResponse("item_new.html", {"request": request, "title": "Add Item"})

@router.post("/items/new")
async def item_new_submit(request: Request):
    form = await request.form()
    name = str(form.get("name", "")).strip()
    category = str(form.get("category", "")).strip()
    color_primary = str(form.get("color_primary", "")).strip()
    color_secondary = str(form.get("color_secondary", "")).strip() or None
    notes = str(form.get("notes", "")).strip() or None

    warmth = int(form.get("warmth", 3))
    formality = int(form.get("formality", 3))

    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO items (name, category, color_primary, color_secondary, warmth, formality, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, category, color_primary, color_secondary, warmth, formality, notes),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url="/items", status_code=303)

@router.post("/items/{item_id}/delete")
def item_delete(item_id: int):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/items", status_code=303)
