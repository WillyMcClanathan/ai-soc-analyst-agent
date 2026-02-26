import re
from datetime import datetime
from pathlib import Path
import sqlite3

# Common combined-ish format example:
# 203.0.113.50 - - [19/Feb/2026:23:40:01 -0800] "GET /wp-login.php HTTP/1.1" 404 153 "-" "Mozilla/5.0 ..."
NGINX_RE = re.compile(
    r'^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<ts>[^\]]+)\]\s+'
    r'"(?P<method>\S+)\s+(?P<path>\S+)\s+(?P<proto>[^"]+)"\s+'
    r'(?P<status>\d{3})\s+(?P<size>\S+)\s+'
    r'"(?P<ref>[^"]*)"\s+"(?P<ua>[^"]*)"'
)

def parse_nginx_ts(ts: str) -> str:
    # ts: 19/Feb/2026:23:40:01 -0800
    dt = datetime.strptime(ts, "%d/%b/%Y:%H:%M:%S %z")
    return dt.astimezone().replace(tzinfo=None).isoformat(sep=" ")

def main():
    root = Path(__file__).resolve().parents[3]
    db_path = root / "data" / "db" / "soc.db"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT id, line
        FROM raw_logs
        WHERE source = 'nginx_access.log'
          AND id NOT IN (SELECT raw_log_id FROM events WHERE raw_log_id IS NOT NULL)
        ORDER BY id
        """
    ).fetchall()

    inserted = 0

    for raw_id, line in rows:
        m = NGINX_RE.match(line)
        if not m:
            continue

        ip = m["ip"]
        event_time = parse_nginx_ts(m["ts"])
        method = m["method"]
        path = m["path"]
        status = int(m["status"])
        ua = m["ua"]

        # Store key info in message for now (we'll add structured http fields later)
        msg = f"Nginx {method} {path} -> {status} UA={ua}"

        cur.execute(
            """
            INSERT INTO events (
              raw_log_id, event_time, event_type, product, host,
              src_ip, outcome, message
            )
            VALUES (?, ?, 'http_access', 'nginx', 'web', ?, ?, ?)
            """,
            (raw_id, event_time, ip, "success", msg)
        )
        inserted += 1

    conn.commit()
    conn.close()

    print(f"✅ Parsed nginx_access.log -> inserted {inserted} events")

if __name__ == "__main__":
    main()