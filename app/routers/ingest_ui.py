from __future__ import annotations

import random
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db.database import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = Path("app/static/uploads")

SLOTS = ["top", "bottom", "shoes", "outerwear"]

def _save_upload(file: UploadFile) -> str | None:
    if not file or not file.filename:
        return None

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename).suffix.lower()
    safe_name = f"{uuid4().hex}{suffix}"
    dest = UPLOAD_DIR / safe_name

    with dest.open("wb") as f:
        f.write(file.file.read())

    return f"/static/uploads/{safe_name}"

def _stub_extract_photo_items(photo_id: int) -> None:
    # Fake “AI”. Creates 2-4 detected items.
    possible = SLOTS[:]
    random.shuffle(possible)
    k = random.randint(2, 4)
    chosen = possible[:k]

    sample_hex = ["#111111", "#FFFFFF", "#2D2A32", "#1E3A8A", "#0F766E", "#B91C1C", "#A16207"]

    conn = get_conn()
    try:
        # clear any previous detections for this photo
        conn.execute("DELETE FROM photo_items WHERE photo_id = ?", (photo_id,))

        for cat in chosen:
            hexv = random.choice(sample_hex)
            conn.execute(
                """
                INSERT INTO photo_items (photo_id, category, slot, bbox_json, extracted_color_hex)
                VALUES (?, ?, ?, ?, ?)
                """,
                (photo_id, cat, cat, None, hexv),
            )

        conn.commit()
    finally:
        conn.close()

def _next_pending_photo_id(conn) -> int | None:
    row = conn.execute(
        "SELECT id FROM closet_photos WHERE decision = 'pending' ORDER BY id ASC LIMIT 1"
    ).fetchone()
    return int(row["id"]) if row else None

@router.get("/ingest")
def ingest_home(request: Request):
    conn = get_conn()
    try:
        pid = _next_pending_photo_id(conn)
        photo = None
        detected = []
        if pid is not None:
            photo = conn.execute("SELECT * FROM closet_photos WHERE id = ?", (pid,)).fetchone()
            detected_rows = conn.execute(
                "SELECT * FROM photo_items WHERE photo_id = ? ORDER BY id ASC", (pid,)
            ).fetchall()
            detected = [dict(r) for r in detected_rows]
    finally:
        conn.close()

    return templates.TemplateResponse(
        "ingest.html",
        {
            "request": request,
            "title": "Ingest",
            "photo": dict(photo) if photo else None,
            "detected": detected,
        },
    )

@router.post("/ingest/upload")
async def ingest_upload(request: Request, photos: list[UploadFile] = File(...)):
    paths: list[str] = []
    for f in photos:
        p = _save_upload(f)
        if p:
            paths.append(p)

    conn = get_conn()
    try:
        for p in paths:
            conn.execute(
                "INSERT INTO closet_photos (image_path, source, decision) VALUES (?, 'upload', 'pending')",
                (p,),
            )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url="/ingest", status_code=303)

@router.post("/ingest/{photo_id}/reject")
def ingest_reject(photo_id: int):
    conn = get_conn()
    try:
        conn.execute("UPDATE closet_photos SET decision = 'rejected' WHERE id = ?", (photo_id,))
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/ingest", status_code=303)

@router.post("/ingest/{photo_id}/accept")
def ingest_accept(photo_id: int):
    conn = get_conn()
    try:
        conn.execute("UPDATE closet_photos SET decision = 'accepted' WHERE id = ?", (photo_id,))
        conn.commit()
    finally:
        conn.close()

    _stub_extract_photo_items(photo_id)
    return RedirectResponse(url=f"/ingest/{photo_id}/review", status_code=303)

@router.get("/ingest/{photo_id}/review")
def ingest_review(request: Request, photo_id: int):
    conn = get_conn()
    try:
        photo = conn.execute("SELECT * FROM closet_photos WHERE id = ?", (photo_id,)).fetchone()
        if not photo:
            return RedirectResponse(url="/ingest", status_code=303)

        detected_rows = conn.execute(
            "SELECT * FROM photo_items WHERE photo_id = ? ORDER BY id ASC", (photo_id,)
        ).fetchall()
        detected = [dict(r) for r in detected_rows]
    finally:
        conn.close()

    return templates.TemplateResponse(
        "ingest_review.html",
        {
            "request": request,
            "title": "Review",
            "photo": dict(photo),
            "detected": detected,
        },
    )

@router.post("/ingest/{photo_id}/finalize")
async def ingest_finalize(photo_id: int, request: Request):
    form = await request.form()

    # which detections did user pick?
    # checkboxes named detect_{id} = "on"
    conn = get_conn()
    try:
        photo = conn.execute("SELECT * FROM closet_photos WHERE id = ?", (photo_id,)).fetchone()
        if not photo:
            return RedirectResponse(url="/ingest", status_code=303)

        detections = conn.execute(
            "SELECT * FROM photo_items WHERE photo_id = ? ORDER BY id ASC", (photo_id,)
        ).fetchall()

        created = 0
        for d in detections:
            did = d["id"]
            if not form.get(f"detect_{did}"):
                continue

            name = str(form.get(f"name_{did}", "")).strip() or f"Detected {d['category']}"
            category = str(form.get(f"category_{did}", d["category"] or "")).strip() or "top"
            color_primary = str(form.get(f"color_primary_{did}", "")).strip() or "unknown"
            color_hex = str(form.get(f"color_hex_{did}", "")).strip() or None

            # For now, we reuse the same photo as item image. Later you’ll crop to the detected bbox.
            image_path = photo["image_path"]

            warmth = int(form.get(f"warmth_{did}", 3))
            formality = int(form.get(f"formality_{did}", 3))
            notes = str(form.get(f"notes_{did}", "")).strip() or None

            cur = conn.execute(
                """
                INSERT INTO items (name, category, color_primary, color_secondary, warmth, formality, notes, image_path, color_hex)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, category, color_primary, None, warmth, formality, notes, image_path, color_hex),
            )
            item_id = cur.lastrowid

            conn.execute("UPDATE photo_items SET item_id = ? WHERE id = ?", (item_id, did))
            created += 1

        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url="/items", status_code=303)
