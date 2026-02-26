import re
from datetime import datetime
from pathlib import Path
import sqlite3

# Examples:
# Feb 19 23:50:01 ubuntu sshd[1201]: Failed password for invalid user admin from 203.0.113.10 port 53321 ssh2
# Feb 19 23:52:00 ubuntu sshd[1210]: Accepted publickey for willy from 10.0.0.5 port 52111 ssh2

FAILED_RE = re.compile(
    r'^(?P<mon>\w+)\s+(?P<day>\d+)\s+(?P<time>\d+:\d+:\d+)\s+(?P<host>\S+)\s+sshd\[\d+\]:\s+'
    r'Failed password for (invalid user )?(?P<user>\S+)\s+from\s+(?P<ip>\S+)\s+port\s+(?P<port>\d+)'
)

ACCEPTED_RE = re.compile(
    r'^(?P<mon>\w+)\s+(?P<day>\d+)\s+(?P<time>\d+:\d+:\d+)\s+(?P<host>\S+)\s+sshd\[\d+\]:\s+'
    r'Accepted\s+(?P<method>\S+)\s+for\s+(?P<user>\S+)\s+from\s+(?P<ip>\S+)\s+port\s+(?P<port>\d+)'
)

MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}

def parse_syslog_ts(mon: str, day: str, t: str, year: int) -> str:
    dt = datetime(year, MONTHS[mon], int(day),
                  int(t[0:2]), int(t[3:5]), int(t[6:8]))
    # store as ISO string (local time for now; later we can convert to UTC)
    return dt.isoformat(sep=" ")

def main():
    root = Path(__file__).resolve().parents[3]
    db_path = root / "data" / "db" / "soc.db"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # only parse raw lines that came from auth.log and haven't been parsed yet
    # (we check by "raw_log_id not in events")
    rows = cur.execute(
        """
        SELECT id, line
        FROM raw_logs
        WHERE source = 'auth.log'
          AND id NOT IN (SELECT raw_log_id FROM events WHERE raw_log_id IS NOT NULL)
        ORDER BY id
        """
    ).fetchall()

    year = datetime.now().year
    inserted = 0

    for raw_id, line in rows:
        m = FAILED_RE.match(line)
        if m:
            event_time = parse_syslog_ts(m["mon"], m["day"], m["time"], year)
            host = m["host"]
            user = m["user"]
            ip = m["ip"]

            cur.execute(
                """
                INSERT INTO events (
                  raw_log_id, event_time, event_type, product, host,
                  src_ip, username, outcome, message
                )
                VALUES (?, ?, 'ssh_auth', 'linux', ?, ?, ?, 'fail', ?)
                """,
                (raw_id, event_time, host, ip, user, f"SSH failed password for {user} from {ip}")
            )
            inserted += 1
            continue

        m = ACCEPTED_RE.match(line)
        if m:
            event_time = parse_syslog_ts(m["mon"], m["day"], m["time"], year)
            host = m["host"]
            user = m["user"]
            ip = m["ip"]
            method = m["method"]

            cur.execute(
                """
                INSERT INTO events (
                  raw_log_id, event_time, event_type, product, host,
                  src_ip, username, outcome, message
                )
                VALUES (?, ?, 'ssh_auth', 'linux', ?, ?, ?, 'success', ?)
                """,
                (raw_id, event_time, host, ip, user, f"SSH accepted {method} for {user} from {ip}")
            )
            inserted += 1
            continue

        # ignore non-matching auth lines for now

    conn.commit()
    conn.close()

    print(f"✅ Parsed auth.log -> inserted {inserted} events")

if __name__ == "__main__":
    main()