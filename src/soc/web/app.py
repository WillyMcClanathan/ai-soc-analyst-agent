from pathlib import Path
import sqlite3
import json
from datetime import datetime, timezone
from flask import Flask, render_template_string, abort, request, redirect, url_for

from soc.agentzero.export_incident import export_incident
from soc.agentzero.ai_analyzer import analyze_incident

app = Flask(__name__)

# ---------------------------
# Paths / Helpers
# ---------------------------

def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]

def get_db_path() -> Path:
    return get_project_root() / "data" / "db" / "soc.db"

def get_report_path(incident_key: str) -> Path:
    return get_project_root() / "data" / "ai" / "outbox" / f"{incident_key}.report.json"

# Legacy Agent Zero I/O (single-file, per incident)
def get_az_inbox_path(incident_key: str) -> Path:
    return get_project_root() / "data" / "ai" / "inbox" / f"{incident_key}.json"

def get_az_outbox_path(incident_key: str) -> Path:
    return get_project_root() / "data" / "ai" / "az_outbox" / f"{incident_key}.agent.json"

# NEW: Run-specific Agent Zero I/O (multiple runs per incident)
def get_az_run_inbox_path(incident_key: str, run_id: int) -> Path:
    return get_project_root() / "data" / "ai" / "inbox" / f"{incident_key}.run-{run_id}.json"

def get_az_run_outbox_path(incident_key: str, run_id: int) -> Path:
    return get_project_root() / "data" / "ai" / "az_outbox" / f"{incident_key}.run-{run_id}.agent.json"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def db_connect():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def ensure_ai_dirs():
    root = get_project_root()
    (root / "data" / "ai" / "inbox").mkdir(parents=True, exist_ok=True)
    (root / "data" / "ai" / "az_outbox").mkdir(parents=True, exist_ok=True)
    (root / "data" / "ai" / "outbox").mkdir(parents=True, exist_ok=True)

# ---------------------------
# HTML Base
# ---------------------------

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
    .pill.green { background:#d7f5d7; }
    .pill.yellow { background:#fff3c4; }
    .pill.red { background:#ffd1d1; }
    .box { background:#fafafa; border:1px solid #eee; padding:12px; border-radius:8px; }
    pre { white-space: pre-wrap; word-wrap: break-word; }
    select, button, textarea, input { padding: 6px; }
    button { cursor: pointer; }
    textarea { width: 100%; max-width: 900px; }
    .row { display:flex; gap:12px; flex-wrap: wrap; }
    .col { flex: 1 1 420px; min-width: 320px; }
    .muted { color:#666; font-size: 12px; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
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

# ---------------------------
# Routes
# ---------------------------

@app.route("/")
def home():
    return render_template_string(BASE_HTML, body="""
      <h2>Dashboard</h2>
      <p>Use the links above.</p>
    """)

@app.route("/alerts")
def alerts():
    conn = db_connect()
    rows = conn.execute("""
        SELECT id, created_at, rule_name, severity, src_ip, description
        FROM alerts
        ORDER BY created_at DESC, id DESC
    """).fetchall()
    conn.close()

    body = ["<h2>Alerts</h2>"]
    body.append("<table><tr><th>ID</th><th>Time</th><th>Rule</th><th>Sev</th><th>IP</th><th>Description</th></tr>")
    for r in rows:
        body.append(
            "<tr>"
            f"<td>{r['id']}</td>"
            f"<td>{r['created_at']}</td>"
            f"<td>{r['rule_name']}</td>"
            f"<td><span class='pill'>{r['severity']}</span></td>"
            f"<td>{r['src_ip'] or ''}</td>"
            f"<td>{r['description']}</td>"
            "</tr>"
        )
    body.append("</table>")
    return render_template_string(BASE_HTML, body="".join(body))

@app.route("/incidents")
def incidents():
    conn = db_connect()
    rows = conn.execute("""
        SELECT incident_key, created_at, status, severity, primary_ip, summary
        FROM incidents
        ORDER BY severity DESC, created_at DESC
    """).fetchall()
    conn.close()

    body = ["<h2>Incidents</h2>"]
    body.append("<table><tr><th>Incident</th><th>Created</th><th>Status</th><th>Sev</th><th>IP</th><th>Summary</th></tr>")
    for r in rows:
        body.append(
            "<tr>"
            f"<td><a href='/incident/{r['incident_key']}'>{r['incident_key']}</a></td>"
            f"<td>{r['created_at']}</td>"
            f"<td><span class='pill'>{r['status']}</span></td>"
            f"<td><span class='pill'>{r['severity']}</span></td>"
            f"<td>{r['primary_ip'] or ''}</td>"
            f"<td>{r['summary']}</td>"
            "</tr>"
        )
    body.append("</table>")
    return render_template_string(BASE_HTML, body="".join(body))

# Legacy manual export (kept)
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

    conn = db_connect()
    conn.execute(
        "UPDATE incidents SET status = ? WHERE incident_key = ?",
        (new_status, incident_key)
    )
    conn.commit()
    conn.close()

    return redirect(f"/incident/{incident_key}")

# ---------------------------
# NEW: Agent Zero Runs (Option A)
# ---------------------------

def refresh_agent_run_statuses(incident_key: str):
    """
    If a run is 'exported' and its output_path exists, mark completed.
    """
    conn = db_connect()
    runs = conn.execute("""
        SELECT id, status, output_path
        FROM agent_runs
        WHERE incident_key = ?
        ORDER BY created_at DESC, id DESC
    """, (incident_key,)).fetchall()

    changed = False
    for r in runs:
        if r["status"] == "exported" and r["output_path"]:
            p = Path(r["output_path"])
            if p.exists():
                conn.execute("UPDATE agent_runs SET status = 'completed' WHERE id = ?", (r["id"],))
                changed = True

    if changed:
        conn.commit()
    conn.close()

@app.route("/incident/<incident_key>/agentzero/run", methods=["POST"])
def agentzero_create_run(incident_key: str):
    """
    Create an agent_runs record, export a run-specific JSON into data/ai/inbox/,
    and update the run to status='exported' with export_path/output_path.
    """
    ensure_ai_dirs()

    analyst_prompt = request.form.get("analyst_prompt", "").strip()

    conn = db_connect()

    # Create run record first (queued)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO agent_runs (incident_key, status, model, requested_by, analyst_prompt)
        VALUES (?, 'queued', 'agentzero', 'analyst', ?)
    """, (incident_key, analyst_prompt))
    run_id = cur.lastrowid

    export_path = get_az_run_inbox_path(incident_key, run_id)
    output_path = get_az_run_outbox_path(incident_key, run_id)

    try:
        # Use your existing exporter to ensure consistent structure.
        # It currently writes a legacy file; we'll also write a run-specific file here.
        export_incident(incident_key)

        # Build a run envelope that Agent Zero can use (and can ignore fields it doesn't care about).
        # Pull incident + related data directly for completeness.
        inc = conn.execute("""
            SELECT incident_key, created_at, status, severity, primary_ip, summary
            FROM incidents WHERE incident_key = ?
        """, (incident_key,)).fetchone()
        if not inc:
            raise RuntimeError(f"Incident not found: {incident_key}")

        alerts = conn.execute("""
            SELECT id, created_at, rule_name, severity, src_ip, description
            FROM alerts
            WHERE src_ip = ?
            ORDER BY created_at DESC, id DESC
        """, (inc["primary_ip"],)).fetchall()

        notes = conn.execute("""
            SELECT id, incident_key, created_at, author, note
            FROM incident_notes
            WHERE incident_key = ?
            ORDER BY created_at DESC, id DESC
        """, (incident_key,)).fetchall()

        # OpenAI report if present
        report_path = get_report_path(incident_key)
        openai_report = None
        if report_path.exists():
            try:
                openai_report = json.loads(report_path.read_text(encoding="utf-8"))
            except Exception:
                openai_report = {"error": "invalid_json", "path": str(report_path)}

        payload = {
            "incident_key": incident_key,
            "run_id": run_id,
            "requested_at": utc_now_iso(),
            "analyst_prompt": analyst_prompt,
            "expected_output_path": str(output_path),
            "incident": dict(inc),
            "alerts": [dict(a) for a in alerts],
            "notes": [dict(n) for n in notes],
            "openai_report": openai_report,
        }

        export_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        # Update run to exported
        conn.execute("""
            UPDATE agent_runs
            SET status = 'exported', export_path = ?, output_path = ?, error = NULL
            WHERE id = ?
        """, (str(export_path), str(output_path), run_id))
        conn.commit()

    except Exception as e:
        conn.execute("""
            UPDATE agent_runs
            SET status = 'failed', error = ?
            WHERE id = ?
        """, (str(e), run_id))
        conn.commit()
        conn.close()
        return abort(500, description=f"Agent run failed: {e}")

    conn.close()
    return redirect(f"/incident/{incident_key}")

@app.route("/incident/<incident_key>/agentzero/run/<int:run_id>")
def agentzero_view_run(incident_key: str, run_id: int):
    """
    View a single run output (if present), plus metadata.
    """
    conn = db_connect()
    run = conn.execute("""
        SELECT *
        FROM agent_runs
        WHERE incident_key = ? AND id = ?
    """, (incident_key, run_id)).fetchone()
    conn.close()

    if not run:
        abort(404)

    out_json = None
    if run["output_path"]:
        p = Path(run["output_path"])
        if p.exists():
            try:
                out_json = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                out_json = {"error": "invalid_json", "path": str(p)}

    # Simple rendering
    status = run["status"]
    pill_class = "pill"
    if status == "completed":
        pill_class += " green"
    elif status in ("queued", "exported"):
        pill_class += " yellow"
    elif status == "failed":
        pill_class += " red"

    body = [f"<h2>Agent Zero Run #{run_id} — {incident_key}</h2>"]
    body.append("<div class='box'>")
    body.append(f"<p><b>Status:</b> <span class='{pill_class}'>{status}</span></p>")
    body.append(f"<p><b>Created:</b> {run['created_at']}</p>")
    body.append(f"<p><b>Prompt:</b><br><pre>{(run['analyst_prompt'] or '').strip()}</pre></p>")
    body.append(f"<p><b>Export Path:</b><br><span class='mono'>{run['export_path'] or ''}</span></p>")
    body.append(f"<p><b>Output Path:</b><br><span class='mono'>{run['output_path'] or ''}</span></p>")
    if run["error"]:
        body.append(f"<p><b>Error:</b><br><pre>{run['error']}</pre></p>")
    body.append(f"<p><a href='/incident/{incident_key}'>← Back to incident</a></p>")
    body.append("</div>")

    # ✅ FIXED: robust render across key variants + lists
    if out_json:
        body.append("<h3>Agent Output</h3>")
        body.append("<div class='box'>")

        exec_sum = out_json.get("executive_summary") or out_json.get("executive") or ""
        tech_sum = out_json.get("technical_summary") or out_json.get("technical") or ""
        hypothesis = out_json.get("attack_hypothesis") or out_json.get("hypothesis") or ""

        body.append(f"<p><b>Executive:</b> {exec_sum}</p>")
        body.append(f"<p><b>Technical:</b> {tech_sum}</p>")
        body.append(f"<p><b>Attack Hypothesis:</b> {hypothesis}</p>")

        def render_list(title: str, key: str) -> str:
            items = out_json.get(key, [])
            if not items:
                return ""
            html = [f"<h4>{title}</h4><ul>"]
            for x in items:
                html.append(f"<li>{x}</li>")
            html.append("</ul>")
            return "".join(html)

        body.append(render_list("Triage Checklist", "triage_checklist"))
        body.append(render_list("Containment Recommendations", "containment_recommendations"))
        body.append(render_list("Remediation Recommendations", "remediation_recommendations"))

        conf = out_json.get("confidence")
        if conf is not None:
            body.append(f"<p><b>Confidence:</b> {conf}</p>")

        body.append("<details><summary>Raw Output JSON</summary>")
        body.append(f"<pre>{json.dumps(out_json, indent=2)}</pre>")
        body.append("</details>")

        body.append("</div>")
    else:
        body.append("<p><i>No output JSON found yet for this run.</i></p>")

    return render_template_string(BASE_HTML, body="".join(body))

@app.route("/incident/<incident_key>")
def incident_detail(incident_key: str):
    # refresh statuses on page load (cheap + effective)
    refresh_agent_run_statuses(incident_key)

    conn = db_connect()
    inc = conn.execute("""
        SELECT incident_key, created_at, status, severity, primary_ip, summary
        FROM incidents
        WHERE incident_key = ?
    """, (incident_key,)).fetchone()

    if not inc:
        conn.close()
        abort(404)

    key = inc["incident_key"]

    report_path = get_report_path(key)
    report = None
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))

    # Legacy AZ single-output (kept for backward compatibility)
    az_out_path = get_az_outbox_path(key)
    az_report = None
    if az_out_path.exists():
        try:
            az_report = json.loads(az_out_path.read_text(encoding="utf-8"))
        except Exception:
            az_report = {"error": "invalid_json", "path": str(az_out_path)}

    # NEW: agent runs for this incident
    runs = conn.execute("""
        SELECT id, created_at, status, analyst_prompt, export_path, output_path
        FROM agent_runs
        WHERE incident_key = ?
        ORDER BY created_at DESC, id DESC
    """, (key,)).fetchall()

    conn.close()

    body = [f"<h2>Incident {key}</h2>"]
    body.append(f"<p><b>Status:</b> {inc['status']} &nbsp; <b>Severity:</b> {inc['severity']} &nbsp; <b>IP:</b> {inc['primary_ip']}</p>")

    # Status dropdown form
    status = inc["status"]
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

    body.append(f"<p><b>Created:</b> {inc['created_at']}</p>")
    body.append(f"<p><b>Summary:</b> {inc['summary']}</p>")

    # OpenAI AI Report button
    body.append(f"<p><a href='/incident/{key}/ai/run'>🤖 Generate/Refresh AI Report</a></p>")

    # ---------------------------
    # NEW: Agent Zero Runs Panel (Option A)
    # ---------------------------
    body.append("<h3>Agent Zero Runs</h3>")
    body.append("""
      <div class="box">
        <form method="POST" action="/incident/{{key}}/agentzero/run">
          <label><b>Analyst Prompt (optional)</b></label><br>
          <textarea name="analyst_prompt" rows="3" placeholder="e.g., Focus on false positive analysis, containment steps, and MITRE mapping."></textarea><br>
          <button type="submit">▶ Run Agent Zero (Export Run JSON)</button>
          <p class="muted">This creates a run record + exports a run-specific JSON to data/ai/inbox/. Agent Zero should write output to data/ai/az_outbox/ using the expected output_path.</p>
        </form>
      </div>
    """.replace("{{key}}", key))

    if runs:
        body.append("<table><tr><th>Run</th><th>Created</th><th>Status</th><th>Prompt</th><th>Output</th></tr>")
        for r in runs:
            st = r["status"]
            pill = "pill"
            if st == "completed":
                pill += " green"
            elif st in ("queued", "exported"):
                pill += " yellow"
            elif st == "failed":
                pill += " red"

            prompt_preview = (r["analyst_prompt"] or "").strip()
            if len(prompt_preview) > 80:
                prompt_preview = prompt_preview[:80] + "…"

            output_hint = r["output_path"] or ""
            if output_hint:
                output_hint = Path(output_hint).name

            body.append(
                "<tr>"
                f"<td><a href='/incident/{key}/agentzero/run/{r['id']}'>#{r['id']}</a></td>"
                f"<td>{r['created_at']}</td>"
                f"<td><span class='{pill}'>{st}</span></td>"
                f"<td>{prompt_preview}</td>"
                f"<td class='mono'>{output_hint}</td>"
                "</tr>"
            )
        body.append("</table>")
    else:
        body.append("<p><i>No Agent Zero runs yet for this incident.</i></p>")

    # ---------------------------
    # Legacy Agent Zero section (kept)
    # ---------------------------
    body.append("<h3>Agent Zero Triage (Legacy Single-File)</h3>")
    body.append(f"<p><a href='/incident/{key}/agentzero/export'>▶ Export incident to Agent Zero inbox (legacy)</a></p>")

    if az_report:
        body.append("<div class='box'>")
        body.append("<h4>Agent Zero Triage Summary</h4>")
        body.append(f"<p><b>Executive:</b> {az_report.get('executive_summary','')}</p>")
        body.append(f"<p><b>Technical:</b> {az_report.get('technical_summary','')}</p>")
        body.append(f"<p><b>Attack Hypothesis:</b> {az_report.get('attack_hypothesis','')}</p>")

        body.append("<details><summary>Raw Agent Zero JSON</summary>")
        body.append(f"<pre>{json.dumps(az_report, indent=2)}</pre>")
        body.append("</details>")
        body.append("</div>")
    else:
        body.append("<p><i>No legacy Agent Zero triage output found yet.</i></p>")
        body.append(f"<p class='muted'><small>Expected file:</small> <code>{az_out_path}</code></p>")

    # ---------------------------
    # AI Report section
    # ---------------------------
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