import json
from pathlib import Path
import sqlite3

def export_incident(incident_key: str):
    root = Path(__file__).resolve().parents[3]
    db_path = root / "data" / "db" / "soc.db"
    out_dir = root / "data" / "ai" / "inbox"
    out_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    inc = cur.execute(
        """
        SELECT id, incident_key, created_at, status, severity, primary_ip, summary
        FROM incidents
        WHERE incident_key = ?
        """,
        (incident_key,)
    ).fetchone()

    if not inc:
        raise SystemExit(f"Incident not found: {incident_key}")

    inc_id, key, created_at, status, severity, primary_ip, summary = inc

    # For V1, find alerts that match same IP (since we didn't build mapping table yet)
    alerts = cur.execute(
        """
        SELECT id, rule_name, created_at, severity, src_ip, description
        FROM alerts
        WHERE src_ip = ?
        ORDER BY id
        """,
        (primary_ip,)
    ).fetchall()

    # Pull events related to that IP
    events = cur.execute(
        """
        SELECT event_time, event_type, product, host, src_ip, username, outcome, message
        FROM events
        WHERE src_ip = ?
        ORDER BY event_time
        """,
        (primary_ip,)
    ).fetchall()

    conn.close()

    payload = {
        "incident": {
            "incident_key": key,
            "created_at": created_at,
            "status": status,
            "severity": severity,
            "primary_ip": primary_ip,
            "summary": summary
        },
        "alerts": [
            {
                "id": a[0],
                "rule_name": a[1],
                "created_at": a[2],
                "severity": a[3],
                "src_ip": a[4],
                "description": a[5],
            }
            for a in alerts
        ],
        "timeline": [
            {
                "time": e[0],
                "event_type": e[1],
                "product": e[2],
                "host": e[3],
                "src_ip": e[4],
                "username": e[5],
                "outcome": e[6],
                "message": e[7],
            }
            for e in events
        ],
        "constraints": [
            "Local/lab logs only",
            "No offensive hacking or exploitation",
            "Focus on SOC analyst workflow realism",
            "If something is unknown, state assumptions"
        ],
        "requested_output": {
            "format": "json",
            "fields": [
                "executive_summary",
                "technical_summary",
                "timeline",
                "triage_checklist",
                "containment_recommendations",
                "remediation_recommendations",
                "assumptions",
                "confidence"
            ]
        }
    }

    out_path = out_dir / f"{incident_key}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"✅ Exported: {out_path}")

if __name__ == "__main__":
    # default: export your first incident
    export_incident("INC-2026-000001")