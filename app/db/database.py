import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "wardrobe.sqlite3"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def _ensure_columns(conn: sqlite3.Connection) -> None:
    # Add columns to existing DBs without breaking anything
    try:
        conn.execute("ALTER TABLE items ADD COLUMN image_path TEXT;")
    except sqlite3.OperationalError:
        # column already exists (or table doesn't yet), ignore
        pass

def init_db() -> None:
    conn = get_conn()
    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        _ensure_columns(conn)
        conn.commit()
    finally:
        conn.close()

def _ensure_columns(conn: sqlite3.Connection) -> None:
    # existing stuff...

    # Add image_path to items (you already have this)
    try:
        conn.execute("ALTER TABLE items ADD COLUMN image_path TEXT;")
    except sqlite3.OperationalError:
        pass

    # NEW: add locked_slots to outfits
    try:
        conn.execute("ALTER TABLE outfits ADD COLUMN locked_slots TEXT;")
    except sqlite3.OperationalError:
        pass
    
    try:
        conn.execute("ALTER TABLE items ADD COLUMN color_hex TEXT;")
    except Exception:
        pass

    try:
        conn.execute("ALTER TABLE items ADD COLUMN color_h INTEGER;")
    except Exception:
        pass

    try:
        conn.execute("ALTER TABLE items ADD COLUMN color_s INTEGER;")
    except Exception:
        pass

    try:
        conn.execute("ALTER TABLE items ADD COLUMN color_l INTEGER;")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE items ADD COLUMN color_hex TEXT;")
    except Exception:
        pass
