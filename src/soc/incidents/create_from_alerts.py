from pathlib import Path
import sqlite3
from datetime import datetime

def next_incident_key(conn: sqlite3.Connection) -> str:
    year = datetime.now().year
    cur = conn.cursor()
    row = cur.execute(
        "SELECT COUNT(*) FROM incidents WHERE incident_key LIKE ?",
        (f"INC-{year}-%",)
    ).fetchone()
    n = (row[0] or 0) + 1
    return f"INC-{year}-{n:06d}"

def main():
    root = Path(__file__).resolve().parents[3]
    db_path = root / "data" / "db" / "soc.db"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    alerts = cur.execute(
        """
        SELECT id, rule_name, severity, src_ip, description
        FROM alerts
        ORDER BY id
        """
    ).fetchall()

    created = 0
    updated = 0

    for alert_id, rule_name, severity, src_ip, desc in alerts:
        if not src_ip:
            continue

        fingerprint = f"{rule_name}|{src_ip}"
        title = f"{rule_name} detected from {src_ip}"
        summary = f"{title} — {desc}"

        existing = cur.execute(
            """
            SELECT id, severity, summary
            FROM incidents
            WHERE fingerprint = ?
            LIMIT 1
            """,
            (fingerprint,)
        ).fetchone()

        if existing:
            inc_id, old_sev, old_summary = existing

            # Update if severity/summary changed
            if old_sev != severity or old_summary != summary:
                cur.execute(
                    """
                    UPDATE incidents
                    SET severity = ?, summary = ?, rule_name = ?, primary_ip = ?
                    WHERE id = ?
                    """,
                    (severity, summary, rule_name, src_ip, inc_id)
                )
                updated += 1
            continue

        key = next_incident_key(conn)
        cur.execute(
            """
            INSERT INTO incidents (
              incident_key, status, severity, primary_ip, summary,
              rule_name, fingerprint, source_alert_id
            )
            VALUES (?, 'New', ?, ?, ?, ?, ?, ?)
            """,
            (key, severity, src_ip, summary, rule_name, fingerprint, alert_id)
        )
        created += 1

    conn.commit()
    conn.close()

    print(f"✅ Incidents synced from alerts: created={created}, updated={updated}")

if __name__ == "__main__":
    main()