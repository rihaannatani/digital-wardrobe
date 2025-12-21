PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  category TEXT NOT NULL,          -- top, bottom, shoes, outerwear, accessory
  color_primary TEXT NOT NULL,     -- "black", "navy", "white", etc
  color_secondary TEXT,            -- optional
  warmth INTEGER NOT NULL DEFAULT 3,   -- 1..5
  formality INTEGER NOT NULL DEFAULT 3, -- 1..5
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS item_tags (
  item_id INTEGER NOT NULL,
  tag_id INTEGER NOT NULL,
  PRIMARY KEY (item_id, tag_id),
  FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS outfits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  context TEXT NOT NULL,        -- office, brunch, date, gym
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS outfit_items (
  outfit_id INTEGER NOT NULL,
  item_id INTEGER NOT NULL,
  slot TEXT NOT NULL,           -- top, bottom, shoes, outerwear
  PRIMARY KEY (outfit_id, item_id),
  FOREIGN KEY (outfit_id) REFERENCES outfits(id) ON DELETE CASCADE,
  FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);
