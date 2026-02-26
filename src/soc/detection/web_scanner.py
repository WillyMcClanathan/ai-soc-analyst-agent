from pathlib import Path
import sqlite3

THRESHOLD = 5  # number of 404s to trigger

def severity_from_count(cnt: int) -> int:
    if cnt >= 20:
        return 8
    if cnt >= 10:
        return 7
    return 6

def main():
    root = Path(__file__).resolve().parents[3]
    db_path = root / "data" / "db" / "soc.db"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT src_ip, COUNT(*) as cnt
        FROM events
        WHERE event_type='http_access'
          AND message LIKE '%-> 404%'
          AND src_ip IS NOT NULL
        GROUP BY src_ip
        HAVING cnt >= ?
        """,
        (THRESHOLD,)
    ).fetchall()

    changed = 0

    for ip, cnt in rows:
        sev = severity_from_count(cnt)
        desc = f"Web scanning suspected: {cnt} HTTP 404 responses from {ip}"

        cur.execute(
            """
            INSERT INTO alerts (rule_name, severity, src_ip, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(rule_name, src_ip) DO UPDATE SET
              severity = excluded.severity,
              description = excluded.description,
              created_at = datetime('now')
            """,
            ("WEB_404_SCANNING", sev, ip, desc)
        )
        changed += 1

    conn.commit()
    conn.close()

    print(f"✅ Web scanning rule upserted {changed} alert(s)")

if __name__ == "__main__":
    main()