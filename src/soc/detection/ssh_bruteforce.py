from pathlib import Path
import sqlite3

THRESHOLD = 10

def severity_from_count(cnt: int) -> int:
    # Simple scaling: more fails => higher severity
    if cnt >= 50:
        return 9
    if cnt >= 30:
        return 8
    if cnt >= 20:
        return 7
    return 6  # >=10

def main():
    root = Path(__file__).resolve().parents[3]
    db_path = root / "data" / "db" / "soc.db"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT src_ip, COUNT(*) as cnt
        FROM events
        WHERE event_type='ssh_auth'
          AND outcome='fail'
          AND src_ip IS NOT NULL
        GROUP BY src_ip
        HAVING cnt >= ?
        """,
        (THRESHOLD,)
    ).fetchall()

    changed = 0

    for ip, cnt in rows:
        sev = severity_from_count(cnt)
        desc = f"SSH brute force suspected: {cnt} failed logins from {ip}"

        # Upsert: one alert per (rule_name, src_ip)
        cur.execute(
            """
            INSERT INTO alerts (rule_name, severity, src_ip, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(rule_name, src_ip) DO UPDATE SET
              severity = excluded.severity,
              description = excluded.description,
              created_at = datetime('now')
            """,
            ("SSH_BRUTE_FORCE", sev, ip, desc)
        )
        changed += 1

    conn.commit()
    conn.close()

    print(f"✅ SSH brute force rule upserted {changed} alert(s)")

if __name__ == "__main__":
    main()