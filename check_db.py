import sqlite3

c = sqlite3.connect('data/db/soc.db')

print("events rows:", c.execute("select count(*) from events").fetchone()[0])
print("ssh fail:", c.execute("select count(*) from events where event_type='ssh_auth' and outcome='fail'").fetchone()[0])
print("ssh success:", c.execute("select count(*) from events where event_type='ssh_auth' and outcome='success'").fetchone()[0])
print("alerts:", c.execute("select count(*) from alerts").fetchone()[0])
print("http_access:", c.execute("select count(*) from events where event_type='http_access'").fetchone()[0])

print("\nAlert rows:")
for row in c.execute("select id, rule_name, src_ip, description from alerts"):
    print(row)

print("\nIncidents:")
for row in c.execute("select id, incident_key, status, severity, primary_ip, summary from incidents"):
    print(row)

c.close()