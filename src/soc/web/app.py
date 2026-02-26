from pathlib import Path
import sqlite3
import json
from flask import Flask, render_template_string, abort, request, redirect

from soc.agentzero.export_incident import export_incident
from soc.agentzero.ai_analyzer import analyze_incident

app = Flask(__name__)

def get_db_path() -> Path:
    root = Path(__file__).resolve().parents[3]
    return root / "data" / "db" / "soc.db"

def get_report_path(incident_key: str) -> Path:
    root = Path(__file__).resolve().parents[3]
    return root / "data" / "ai" / "outbox" / f"{incident_key}.report.json"

# Agent Zero I/O (host paths). Docker should mount data/ai -> /a0/ai
def get_az_inbox_path(incident_key: str) -> Path:
    root = Path(__file__).resolve().parents[3]
    return root / "data" / "ai" / "inbox" / f"{incident_key}.json"

def get_az_outbox_path(incident_key: str) -> Path:
    root = Path(__file__).resolve().parents[3]
    return root / "data" / "ai" / "az_outbox" / f"{incident_key}.agent.json"

BASE_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>AI SOC Analyst Agent</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; }
    table { border-collapse: collapse; width: 100%; margin-top: 12px; }
    th, td { border: 1px solid #ddd; padding: 8px; font-size: 14px; vertical-align: top; }
    th { background: #f5f5f5; text-align: left; }
    a { color: #0b63ce; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .nav { margin-bottom: 16px; }
    .pill { display:inline-block; padding:2px 8px; border-radius: 999px; background:#eee; }
    .box { background:#fafafa; border:1px solid #eee; padding:12px; border-radius:8px; }
    pre { white-space: pre-wrap; word-wrap: break-word; }
    select, button { padding: 6px; }
    button { cursor: pointer; }
  </style>
</head>
<body>
  <div class="nav">
    <b>AI SOC Analyst Agent</b> ·
    <a href="/alerts">Alerts</a> ·
    <a href="/incidents">Incidents</a>
  </div>
  {{ body|safe }}
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(BASE_HTML, body="""
      <h2>Dashboard</h2>
      <p>Use the links above.</p>
    """)

@app.route("/alerts")
def alerts():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT id, created_at, rule_name, severity, src_ip, description
        FROM alerts
        ORDER BY created_at DESC, id DESC
    """).fetchall()
    conn.close()

    body = ["<h2>Alerts</h2>"]
    body.append("<table><tr><th>ID</th><th>Time</th><th>Rule</th><th>Sev</th><th>IP</th><th>Description</th></tr>")
    for aid, ts, rule, sev, ip, desc in rows:
        body.append(
            "<tr>"
            f"<td>{aid}</td>"
            f"<td>{ts}</td>"
            f"<td>{rule}</td>"
            f"<td><span class='pill'>{sev}</span></td>"
            f"<td>{ip}</td>"
            f"<td>{desc}</td>"
            "</tr>"
        )
    body.append("</table>")
    return render_template_string(BASE_HTML, body="".join(body))

@app.route("/incidents")
def incidents():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT incident_key, created_at, status, severity, primary_ip, summary
        FROM incidents
        ORDER BY severity DESC, created_at DESC
    """).fetchall()
    conn.close()

    body = ["<h2>Incidents</h2>"]
    body.append("<table><tr><th>Incident</th><th>Created</th><th>Status</th><th>Sev</th><th>IP</th><th>Summary</th></tr>")
    for key, ts, status, sev, ip, summary in rows:
        body.append(
            "<tr>"
            f"<td><a href='/incident/{key}'>{key}</a></td>"
            f"<td>{ts}</td>"
            f"<td><span class='pill'>{status}</span></td>"
            f"<td><span class='pill'>{sev}</span></td>"
            f"<td>{ip}</td>"
            f"<td>{summary}</td>"
            "</tr>"
        )
    body.append("</table>")
    return render_template_string(BASE_HTML, body="".join(body))

@app.route("/incident/<incident_key>/agentzero/export")
def agentzero_export(incident_key: str):
    export_incident(incident_key)

    inbox_path = get_az_inbox_path(incident_key)
    out_path = get_az_outbox_path(incident_key)

    return render_template_string(
        BASE_HTML,
        body=f"""
        <h2>Agent Zero Export</h2>
        <div class="box">
          <p>✅ Exported <b>{incident_key}</b> to:</p>
          <pre>{inbox_path}</pre>
          <p><b>Next:</b> In Agent Zero, load that JSON and save triage output JSON to:</p>
          <pre>{out_path}</pre>
          <p><a href="/incident/{incident_key}">← Back to incident</a></p>
        </div>
        """
    )

@app.route("/incident/<incident_key>/ai/run")
def run_ai_report(incident_key: str):
    analyze_incident(incident_key)
    return render_template_string(
        BASE_HTML,
        body=f"""
        <h2>AI Report</h2>
        <div class="box">
          <p>✅ Generated/updated AI report for <b>{incident_key}</b></p>
          <p><a href="/incident/{incident_key}">← Back to incident</a></p>
        </div>
        """
    )

# ✅ Status workflow: New → Triage → Investigating → Contained → Closed
@app.route("/incident/<incident_key>/status", methods=["POST"])
def update_incident_status(incident_key: str):
    new_status = request.form.get("status", "").strip()
    allowed = {"New", "Triage", "Investigating", "Contained", "Closed"}
    if new_status not in allowed:
        return abort(400)

    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "UPDATE incidents SET status = ? WHERE incident_key = ?",
        (new_status, incident_key)
    )
    conn.commit()
    conn.close()

    return redirect(f"/incident/{incident_key}")

@app.route("/incident/<incident_key>")
def incident_detail(incident_key: str):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    inc = cur.execute("""
        SELECT incident_key, created_at, status, severity, primary_ip, summary
        FROM incidents
        WHERE incident_key = ?
    """, (incident_key,)).fetchone()
    conn.close()

    if not inc:
        abort(404)

    key, created_at, status, sev, ip, summary = inc

    report_path = get_report_path(key)
    report = None
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))

    az_out_path = get_az_outbox_path(key)
    az_report = None
    if az_out_path.exists():
        try:
            az_report = json.loads(az_out_path.read_text(encoding="utf-8"))
        except Exception:
            az_report = {"error": "invalid_json", "path": str(az_out_path)}

    body = [f"<h2>Incident {key}</h2>"]
    body.append(f"<p><b>Status:</b> {status} &nbsp; <b>Severity:</b> {sev} &nbsp; <b>IP:</b> {ip}</p>")

    # ✅ Status dropdown form
    body.append(f"""
      <form method="POST" action="/incident/{key}/status" style="margin: 10px 0;">
        <label><b>Update Status:</b></label>
        <select name="status">
          <option {"selected" if status=="New" else ""}>New</option>
          <option {"selected" if status=="Triage" else ""}>Triage</option>
          <option {"selected" if status=="Investigating" else ""}>Investigating</option>
          <option {"selected" if status=="Contained" else ""}>Contained</option>
          <option {"selected" if status=="Closed" else ""}>Closed</option>
        </select>
        <button type="submit">Save</button>
      </form>
    """)

    body.append(f"<p><b>Created:</b> {created_at}</p>")
    body.append(f"<p><b>Summary:</b> {summary}</p>")

    # OpenAI AI Report button
    body.append(f"<p><a href='/incident/{key}/ai/run'>🤖 Generate/Refresh AI Report</a></p>")

    # Agent Zero section (optional)
    body.append("<h3>Agent Zero Triage (Optional)</h3>")
    body.append(f"<p><a href='/incident/{key}/agentzero/export'>▶ Export incident to Agent Zero inbox</a></p>")

    if az_report:
        body.append("<div class='box'>")
        body.append("<h4>Agent Zero Triage Summary</h4>")

        body.append(f"<p><b>Executive:</b> {az_report.get('executive_summary','')}</p>")
        body.append(f"<p><b>Technical:</b> {az_report.get('technical_summary','')}</p>")
        body.append(f"<p><b>Attack Hypothesis:</b> {az_report.get('attack_hypothesis','')}</p>")

        body.append("<h5>Timeline</h5><ul>")
        for t in az_report.get("timeline", []):
            body.append(
                f"<li><b>{t.get('time')}</b> — {t.get('event')}"
                f"<br><small>{t.get('evidence','')}</small></li>"
            )
        body.append("</ul>")

        def az_bullets(title, keyname):
            items = az_report.get(keyname, [])
            html = [f"<h5>{title}</h5><ul>"]
            for x in items:
                html.append(f"<li>{x}</li>")
            html.append("</ul>")
            return "".join(html)

        body.append(az_bullets("Triage Checklist", "triage_checklist"))
        body.append(az_bullets("Containment Recommendations", "containment_recommendations"))
        body.append(az_bullets("Remediation Recommendations", "remediation_recommendations"))
        body.append(az_bullets("Questions for Analyst", "questions_for_analyst"))
        body.append(az_bullets("Assumptions", "assumptions"))
        body.append(f"<p><b>Confidence:</b> {az_report.get('confidence')}</p>")

        body.append("<details><summary>Raw Agent Zero JSON</summary>")
        body.append(f"<pre>{json.dumps(az_report, indent=2)}</pre>")
        body.append("</details>")

        body.append("</div>")
    else:
        body.append("<p><i>No Agent Zero triage output found yet.</i></p>")
        body.append(f"<p><small>Expected file:</small> <code>{az_out_path}</code></p>")

    # AI Report section
    if not report:
        body.append("<h3>AI Report</h3><p><i>No AI report found.</i></p>")
        return render_template_string(BASE_HTML, body="".join(body))

    body.append("<h3>AI Report</h3>")
    body.append(f"<h4>Executive Summary</h4><p>{report.get('executive_summary','')}</p>")
    body.append(f"<h4>Technical Summary</h4><p>{report.get('technical_summary','')}</p>")

    body.append("<h4>Timeline</h4><ul>")
    for item in report.get("timeline", []):
        body.append(f"<li><b>{item.get('time')}</b>: {item.get('event')}</li>")
    body.append("</ul>")

    def bullet_section(title, keyname):
        items = report.get(keyname, [])
        html = [f"<h4>{title}</h4><ul>"]
        for x in items:
            html.append(f"<li>{x}</li>")
        html.append("</ul>")
        return "".join(html)

    body.append(bullet_section("Triage Checklist", "triage_checklist"))
    body.append(bullet_section("Containment Recommendations", "containment_recommendations"))
    body.append(bullet_section("Remediation Recommendations", "remediation_recommendations"))
    body.append(bullet_section("Assumptions", "assumptions"))
    body.append(f"<p><b>Confidence:</b> {report.get('confidence')}</p>")

    return render_template_string(BASE_HTML, body="".join(body))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)