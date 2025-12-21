from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.db.database import get_conn
from app.services.outfit_engine import generate_outfit

router = APIRouter()

@router.post("/api/outfits/generate")
def generate(context: str = "office"):
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM items").fetchall()
        items = [dict(r) for r in rows]
    finally:
        conn.close()

    outfit = generate_outfit(items, context)
    return JSONResponse(outfit)
