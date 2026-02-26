import sqlite3

conn = sqlite3.connect("data/db/soc.db")
cur = conn.cursor()

cur.execute("DELETE FROM incidents WHERE fingerprint IS NULL")
deleted = cur.rowcount

conn.commit()
conn.close()

print(f"✅ deleted legacy incidents: {deleted}")