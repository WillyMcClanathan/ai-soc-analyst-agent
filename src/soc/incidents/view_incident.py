from pathlib import Path
import sqlite3
import json
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m soc.incidents.view_incident INC-YYYY-000001")
        raise SystemExit(2)

    incident_key = sys.argv[1]

    root = Path(__file__).resolve().parents[3]
    db_path = root / "data" / "db" / "soc.db"
    report_path = root / "data" / "ai" / "outbox" / f"{incident_key}.report.json"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    inc = cur.execute(
        """
        SELECT incident_key, created_at, status, severity, primary_ip, summary
        FROM incidents
        WHERE incident_key = ?
        """,
        (incident_key,)
    ).fetchone()

    conn.close()

    if not inc:
        print(f"Incident not found: {incident_key}")
        raise SystemExit(1)

    incident_key, created_at, status, severity, primary_ip, summary = inc

    print("=" * 80)
    print(f"{incident_key} | {status} | Sev {severity} | IP {primary_ip}")
    print(f"Created: {created_at}")
    print(f"Summary: {summary}")
    print("=" * 80)

    if not report_path.exists():
        print("No AI report found.")
        return

    report = json.loads(report_path.read_text(encoding="utf-8"))

    print("\n[Executive Summary]")
    print(report.get("executive_summary", ""))

    print("\n[Technical Summary]")
    print(report.get("technical_summary", ""))

    print("\n[Timeline]")
    for item in report.get("timeline", []):
        print(f"- {item.get('time')} | {item.get('event')}")

    print("\n[Triage Checklist]")
    for t in report.get("triage_checklist", []):
        print(f"- {t}")

    print("\n[Containment]")
    for t in report.get("containment_recommendations", []):
        print(f"- {t}")

    print("\n[Remediation]")
    for t in report.get("remediation_recommendations", []):
        print(f"- {t}")

    print("\n[Assumptions]")
    for t in report.get("assumptions", []):
        print(f"- {t}")

    print(f"\n[Confidence] {report.get('confidence')}")
    print("=" * 80)

if __name__ == "__main__":
    main()