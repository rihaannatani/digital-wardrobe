import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "wardrobe.sqlite3"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def ensure_ingest_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS closet_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'upload',
            decision TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS photo_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            photo_id INTEGER NOT NULL,
            category TEXT,
            slot TEXT,
            bbox_json TEXT,
            extracted_color_hex TEXT,
            item_id INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (photo_id) REFERENCES closet_photos(id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE SET NULL
        )
        """
    )

def _ensure_columns(conn: sqlite3.Connection) -> None:
    def add(sql: str):
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            pass

    add("ALTER TABLE items ADD COLUMN image_path TEXT;")
    add("ALTER TABLE outfits ADD COLUMN locked_slots TEXT;")

    add("ALTER TABLE items ADD COLUMN color_hex TEXT;")
    add("ALTER TABLE items ADD COLUMN color_h INTEGER;")
    add("ALTER TABLE items ADD COLUMN color_s INTEGER;")
    add("ALTER TABLE items ADD COLUMN color_l INTEGER;")

def init_db() -> None:
    conn = get_conn()
    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        _ensure_columns(conn)
        ensure_ingest_tables(conn)
        conn.commit()
    finally:
        conn.close()
