from pathlib import Path
import sqlite3

from soc.agentzero.export_incident import export_incident
from soc.agentzero.ai_analyzer import analyze_incident

def main():
    root = Path(__file__).resolve().parents[3]
    db_path = root / "data" / "db" / "soc.db"
    outbox = root / "data" / "ai" / "outbox"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    incidents = cur.execute(
        """
        SELECT incident_key
        FROM incidents
        ORDER BY id
        """
    ).fetchall()

    conn.close()

    processed = 0
    skipped = 0

    for (key,) in incidents:
        report_path = outbox / f"{key}.report.json"
                # Re-generate if missing OR incident was updated after the report
        if report_path.exists():
            incident_path = (root / "data" / "ai" / "inbox" / f"{key}.json")
            if incident_path.exists():
                report_mtime = report_path.stat().st_mtime
                incident_mtime = incident_path.stat().st_mtime
                # If incident package is not newer, skip
                if incident_mtime <= report_mtime:
                    skipped += 1
                    continue
            else:
                skipped += 1
                continue

        # Export fresh package then analyze
        export_incident(key)
        analyze_incident(key)
        processed += 1

    print(f"✅ AI enrichment complete: processed={processed}, skipped={skipped}")

if __name__ == "__main__":
    main()