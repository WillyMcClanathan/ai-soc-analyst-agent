PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS raw_logs (
  id INTEGER PRIMARY KEY,
  source TEXT NOT NULL,
  ingested_at TEXT NOT NULL DEFAULT (datetime('now')),
  line TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY,
  raw_log_id INTEGER,
  event_time TEXT NOT NULL,
  event_type TEXT NOT NULL,
  product TEXT NOT NULL,
  host TEXT,
  src_ip TEXT,
  username TEXT,
  outcome TEXT,
  http_method TEXT,
  http_path TEXT,
  http_status INTEGER,
  http_user_agent TEXT,
  message TEXT,
  FOREIGN KEY(raw_log_id) REFERENCES raw_logs(id)
);

CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY,
  rule_name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  severity INTEGER NOT NULL,
  src_ip TEXT,
  description TEXT
);

CREATE TABLE IF NOT EXISTS incidents (
  id INTEGER PRIMARY KEY,
  incident_key TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  status TEXT NOT NULL DEFAULT 'New',
  severity INTEGER NOT NULL,
  primary_ip TEXT,
  summary TEXT,
  source_alert_id INTEGER UNIQUE
);

-- Agent Zero run history (per-incident)
CREATE TABLE IF NOT EXISTS agent_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  incident_key TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  status TEXT NOT NULL DEFAULT 'queued',   -- queued|exported|completed|failed
  model TEXT DEFAULT 'agentzero',
  requested_by TEXT DEFAULT 'analyst',

  analyst_prompt TEXT,
  export_path TEXT,
  output_path TEXT,
  error TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_incident_key_created
ON agent_runs (incident_key, created_at DESC);