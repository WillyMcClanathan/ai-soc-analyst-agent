from pathlib import Path
import sqlite3

def import_log_file(file_path: Path, source_name: str):
    root = Path(__file__).resolve().parents[3]
    db_path = root / "data" / "db" / "soc.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    inserted = 0

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            cursor.execute(
                """
                INSERT INTO raw_logs (source, line)
                VALUES (?, ?)
                """,
                (source_name, line)
            )
            inserted += 1

    conn.commit()
    conn.close()

    print(f"✅ Imported {inserted} lines from {file_path.name}")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    log_dir = root / "data" / "logs"

    # Example files (we'll replace with real ones next)
    for log_file in log_dir.glob("*.log"):
        import_log_file(log_file, log_file.name)