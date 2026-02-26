import sqlite3

conn = sqlite3.connect("data/db/soc.db")
cur = conn.cursor()

# Deduplicate alerts first (keep newest per rule+ip)
cur.execute("""
DELETE FROM alerts
WHERE id NOT IN (
    SELECT MAX(id)
    FROM alerts
    GROUP BY rule_name, src_ip
)
""")

# Add unique index
cur.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS ux_alert_rule_ip
ON alerts(rule_name, src_ip)
""")

conn.commit()
conn.close()

print("✅ alerts deduped and unique index created")