from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db.database import get_conn


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = Path("app/static/uploads")


def _save_upload(file: UploadFile | None) -> str | None:
    if file is None or not file.filename:
        return None

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename).suffix.lower()
    safe_name = f"{uuid4().hex}{suffix}"
    dest = UPLOAD_DIR / safe_name

    with dest.open("wb") as f:
        f.write(file.file.read())

    return f"/static/uploads/{safe_name}"


@router.get("/items")
def items_list(request: Request):
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM items ORDER BY id DESC").fetchall()
        items = [dict(r) for r in rows]
    finally:
        conn.close()

    return templates.TemplateResponse(
        "items_list.html",
        {"request": request, "items": items, "title": "Wardrobe"},
    )


@router.get("/items/new")
def item_new_form(request: Request):
    return templates.TemplateResponse(
        "item_new.html",
        {"request": request, "title": "Add Item"},
    )


@router.post("/items/new")
async def item_new_submit(request: Request, image: UploadFile | None = File(default=None)):
    form = await request.form()

    name = str(form.get("name", "")).strip()
    category = str(form.get("category", "")).strip()
    color_primary = str(form.get("color_primary", "")).strip()
    color_secondary = str(form.get("color_secondary", "")).strip() or None
    notes = str(form.get("notes", "")).strip() or None

    warmth = int(form.get("warmth", 3))
    formality = int(form.get("formality", 3))

    image_path = _save_upload(image)

    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO items (name, category, color_primary, color_secondary, warmth, formality, notes, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, category, color_primary, color_secondary, warmth, formality, notes, image_path),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url="/items", status_code=303)


@router.get("/items/{item_id}/edit")
def item_edit_form(request: Request, item_id: int):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            return RedirectResponse(url="/items", status_code=303)
        item = dict(row)
    finally:
        conn.close()

    return templates.TemplateResponse(
        "item_edit.html",
        {"request": request, "item": item, "title": "Edit Item"},
    )


@router.post("/items/{item_id}/edit")
async def item_edit_submit(item_id: int, request: Request, image: UploadFile | None = File(default=None)):
    form = await request.form()

    name = str(form.get("name", "")).strip()
    category = str(form.get("category", "")).strip()
    color_primary = str(form.get("color_primary", "")).strip()
    color_secondary = str(form.get("color_secondary", "")).strip() or None
    notes = str(form.get("notes", "")).strip() or None

    warmth = int(form.get("warmth", 3))
    formality = int(form.get("formality", 3))

    new_image_path = _save_upload(image) if image and image.filename else None

    conn = get_conn()
    try:
        old = conn.execute("SELECT image_path FROM items WHERE id = ?", (item_id,)).fetchone()
        old_image_path = old["image_path"] if old else None
        final_image_path = new_image_path or old_image_path

        conn.execute(
            """
            UPDATE items
            SET name = ?, category = ?, color_primary = ?, color_secondary = ?, warmth = ?, formality = ?, notes = ?, image_path = ?
            WHERE id = ?
            """,
            (name, category, color_primary, color_secondary, warmth, formality, notes, final_image_path, item_id),
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
