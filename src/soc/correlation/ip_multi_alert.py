from pathlib import Path
import sqlite3

def main():
    root = Path(__file__).resolve().parents[3]
    db_path = root / "data" / "db" / "soc.db"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Find IPs with 2+ open incidents
    rows = cur.execute(
        """
        SELECT primary_ip, COUNT(*) as cnt, MAX(severity) as max_sev
        FROM incidents
        WHERE status != 'Closed'
          AND primary_ip IS NOT NULL
        GROUP BY primary_ip
        HAVING cnt >= 2
        """
    ).fetchall()

    updated = 0

    for ip, cnt, max_sev in rows:
        # bump severity by 1 (cap at 9)
        new_sev = min(9, int(max_sev) + 1)

        cur.execute(
            """
            UPDATE incidents
            SET severity = ?
            WHERE status != 'Closed'
              AND primary_ip = ?
              AND severity < ?
            """,
            (new_sev, ip, new_sev)
        )
        updated += cur.rowcount

    conn.commit()
    conn.close()

    print(f"✅ Correlation applied: updated {updated} incident(s)")

if __name__ == "__main__":
    main()