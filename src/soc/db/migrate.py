from pathlib import Path
import sqlite3

def main():
    # Project root = ai-soc-analyst-agent/
    root = Path(__file__).resolve().parents[3]

    db_path = root / "data" / "db" / "soc.db"
    schema_path = root / "src" / "soc" / "db" / "schema.sql"

    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")

    schema_sql = schema_path.read_text(encoding="utf-8")
    conn.executescript(schema_sql)

    conn.commit()
    conn.close()

    print(f"✅ Database created/migrated: {db_path}")

if __name__ == "__main__":
    main()