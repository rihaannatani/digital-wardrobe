from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db.database import get_conn
from app.services.outfit_engine import generate_outfits, SLOTS

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/outfits")
def outfits_page(request: Request, context: str = "office"):
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM items").fetchall()
        items = [dict(r) for r in rows]
    finally:
        conn.close()

    outfits = generate_outfits(items, context=context, k=3)

    return templates.TemplateResponse(
        "outfits.html",
        {"request": request, "context": context, "outfits": outfits, "slots": SLOTS, "title": "Outfits"},
    )

@router.post("/outfits/save")
async def outfits_save(request: Request):
    form = await request.form()
    context = str(form.get("context", "office"))

    # slot ids come in like top_id, bottom_id, shoes_id, outerwear_id
    slot_ids = {}
    for slot in SLOTS:
        raw = form.get(f"{slot}_id")
        if raw:
            try:
                slot_ids[slot] = int(raw)
            except ValueError:
                pass

    conn = get_conn()
    try:
        cur = conn.execute("INSERT INTO outfits (context) VALUES (?)", (context,))
        outfit_id = cur.lastrowid

        for slot, item_id in slot_ids.items():
            conn.execute(
                "INSERT INTO outfit_items (outfit_id, item_id, slot) VALUES (?, ?, ?)",
                (outfit_id, item_id, slot),
            )

        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/outfits?context={context}", status_code=303)

@router.get("/history")
def history_page(request: Request):
    conn = get_conn()
    try:
        outfit_rows = conn.execute(
            "SELECT id, context, created_at FROM outfits ORDER BY id DESC LIMIT 50"
        ).fetchall()

        outfits = []
        for o in outfit_rows:
            items = conn.execute(
                """
                SELECT oi.slot, i.*
                FROM outfit_items oi
                JOIN items i ON i.id = oi.item_id
                WHERE oi.outfit_id = ?
                """,
                (o["id"],),
            ).fetchall()
            outfits.append({"meta": dict(o), "items": [dict(r) for r in items]})
    finally:
        conn.close()

    return templates.TemplateResponse("history.html", {"request": request, "outfits": outfits, "title": "History"})
