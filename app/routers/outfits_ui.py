import random
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db.database import get_conn
from app.services.outfit_engine import generate_outfits, SLOTS

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/outfits")
def outfits_page(
    request: Request,
    context: str = "office",
    locked: str = "",
    toggle_lock: str | None = None,
    reroll: str | None = None,
    shuffle: int = 0,
    top_id: int | None = None,
    bottom_id: int | None = None,
    shoes_id: int | None = None,
    outerwear_id: int | None = None,
):
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM items").fetchall()
        items = [dict(r) for r in rows]
    finally:
        conn.close()

    # Parse locked slots
    locked_set = set()
    for s in locked.split(","):
        s2 = s.strip()
        if s2 in SLOTS:
            locked_set.add(s2)

    # Toggle lock if requested
    if toggle_lock in SLOTS:
        if toggle_lock in locked_set:
            locked_set.remove(toggle_lock)
        else:
            locked_set.add(toggle_lock)

    # Current selected ids (these keep your current outfit stable across clicks)
    selected_ids = {
        "top": top_id,
        "bottom": bottom_id,
        "shoes": shoes_id,
        "outerwear": outerwear_id,
    }

    by_id = {it["id"]: it for it in items}

    # Start with selected ids if present, else pick something reasonable
    # We generate a baseline outfit, then overlay selections, then apply shuffle/reroll rules
    base_list = generate_outfits(items, context=context, k=1)
    outfit = base_list[0] if base_list else {}

    # Overlay selected ids into outfit, these act as "current state"
    for slot, sid in selected_ids.items():
        if sid and sid in by_id:
            outfit[slot] = by_id[sid]

    # Helper to choose a random item for a slot
    def pick_for_slot(slot: str) -> dict | None:
        options = [it for it in items if it["category"] == slot]
        if not options:
            return None
        # avoid picking the exact same id when possible
        current = outfit.get(slot)
        if current and len(options) > 1:
            options = [x for x in options if x["id"] != current.get("id")]
        return random.choice(options)

    # Apply shuffle or reroll, but only on unlocked slots
    if shuffle == 1:
        for slot in SLOTS:
            if slot in locked_set:
                continue
            picked = pick_for_slot(slot)
            if picked:
                outfit[slot] = picked
    elif reroll in SLOTS:
        if reroll not in locked_set:
            picked = pick_for_slot(reroll)
            if picked:
                outfit[reroll] = picked

    # Rebuild locked string for template and links
    locked_str = ",".join(sorted(list(locked_set)))

    return templates.TemplateResponse(
        "outfits.html",
        {
            "request": request,
            "context": context,
            "outfit": outfit,
            "slots": SLOTS,
            "locked": locked_str,
            "locked_set": locked_set,
            "title": "Outfits",
        },
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
        locked_slots = str(form.get("locked", "")).strip()
        cur = conn.execute(
            "INSERT INTO outfits (context, locked_slots) VALUES (?, ?)",
            (context, locked_slots),
        )
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
            "SELECT id, context, created_at, locked_slots FROM outfits ORDER BY id DESC LIMIT 50"
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
