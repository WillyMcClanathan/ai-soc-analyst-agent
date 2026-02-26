# System Architecture

## Overview

The AI SOC Analyst Agent is designed as a modular, layered Security Operations Center (SOC) automation system.

It follows a structured pipeline:

Log ingestion → Parsing → Detection → Alerting → Incident management → AI analysis → Reporting

---

## High-Level Flow


Raw Logs
(auth.log, nginx_access.log)
↓
Log Parsers
↓
Structured Events
↓
Detection Engine
↓
Alerts
↓
Correlation Engine
↓
Incidents
↓
Agent Zero AI Analysis
↓
Web Dashboard / Exported Reports


---

## Component Breakdown

### 1. Ingestion Layer

Location:

src/soc/ingestion/


Responsibilities:
- Batch import log files
- Normalize log entries
- Store structured records in database

---

### 2. Parsing Layer

Location:

src/soc/parsers/


Responsibilities:
- Parse Linux authentication logs
- Parse Nginx access logs
- Extract IP, timestamp, user, status codes, request paths
- Standardize event structure

---

### 3. Detection Layer

Location:

src/soc/detection/


Responsibilities:
- SSH brute-force detection
- Suspicious authentication activity detection
- Web scanning detection
- Rule-based threshold logic
- Severity assignment

This layer implements detection engineering principles similar to those used in real SOC environments.

---

### 4. Alert & Correlation Layer

Location:

src/soc/correlation/
src/soc/incidents/


Responsibilities:
- Create alerts from detection triggers
- Group related alerts into incidents
- Maintain incident lifecycle states:
  - New
  - Triage
  - Investigating
  - Contained
  - Closed

---

### 5. AI Analysis Layer

Location:

src/soc/agentzero/


Responsibilities:
- Generate structured incident summaries
- Provide automated threat analysis
- Suggest remediation steps
- Export security reports

This layer integrates Agent Zero to enhance incident triage and documentation workflows.

---

### 6. Web Dashboard

Location:

src/soc/web/


Responsibilities:
- Display incidents
- Update status
- Trigger AI analysis
- View structured metadata

---

## Database Design

The system uses SQLite as a lightweight local datastore.

Core entities include:
- Events
- Alerts
- Incidents
- Incident Notes

Indexes are implemented to support efficient alert lookups and correlation logic.

---

## Design Principles

- Modular architecture
- Clear separation of concerns
- Detection-first design
- AI augmentation (not AI replacement)
- Local, self-contained deployment
- Educational transparency

---

## Limitations

- No production authentication layer
- No real-time streaming ingestion
- No distributed scalability
- Designed for local demonstration use

---

## Future Improvements

- Real-time log streaming (tail-based ingestion)
- MITRE ATT&CK technique mapping
- Threat intelligence enrichment
- Authentication and RBAC
- REST API layer
- Containerized deployment