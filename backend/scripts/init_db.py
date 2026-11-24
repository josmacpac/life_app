from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "game.sqlite"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

with sqlite3.connect(DB_PATH) as conn:
    conn.executescript(schema_sql)
    conn.commit()

print(f"Tabla sessions creada en: {DB_PATH}")