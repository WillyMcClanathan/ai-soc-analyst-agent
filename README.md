# AI SOC Analyst Agent

An AI-enhanced Security Operations Center (SOC) automation platform built with Python, SQLite, and Agent Zero.

This system ingests system and web server logs, applies rule-based detection logic, manages incidents through a structured lifecycle, and generates AI-powered threat analysis reports.

---

## Overview

The AI SOC Analyst Agent is a local SOC simulation environment designed to demonstrate log ingestion, detection engineering, incident response workflows, and AI-assisted security analysis.

The platform parses authentication and web access logs, detects suspicious behavior such as SSH brute-force attempts and web scanning activity, creates structured alerts, correlates related events into incidents, and generates automated AI summaries using Agent Zero.

This project demonstrates practical SOC automation techniques and detection engineering principles.

---

## Core Features

### Log Ingestion
- Batch import of system authentication logs (e.g., `auth.log`)
- Parsing of web server access logs (e.g., `nginx_access.log`)
- Structured normalization of raw log entries

### Detection Engineering
- SSH brute-force detection
- Suspicious authentication activity detection
- Web scanning detection
- Rule-based threshold logic
- Severity scoring

### Alert and Incident Management
- Alert creation and indexing
- Multi-alert correlation
- Incident lifecycle management:
  - New
  - Triage
  - Investigating
  - Contained
  - Closed
- Status updates via web interface

### AI-Enhanced Analysis
- Automated incident summaries
- Structured threat analysis
- Report export functionality
- Agent Zero integration for AI-driven security reasoning

### Web Dashboard
- Incident detail view
- Status update controls
- AI report generation
- Structured display of incident metadata

---

## Architecture


 Log Files
 ↓
 Parsers
 ↓
 Detection Rules
 ↓
 Alerts
 ↓
 Incident Creation & Correlation
 ↓
 Agent Zero AI Analysis
 ↓
 Web Dashboard / Reports


---

## Project Structure


src/soc/
agentzero/ # AI analysis and report generation
correlation/ # Alert correlation logic
db/ # Database schema and migrations
detection/ # Rule-based detection modules
incidents/ # Incident creation and viewing
ingestion/ # Log import pipeline
parsers/ # Log parsing modules
web/ # Web application dashboard


---

## Technology Stack

- Python 3.x
- SQLite
- Flask (or relevant web framework)
- Agent Zero
- Rule-based detection engine
- Structured JSON incident reports

---

## Setup Instructions

1. Clone the repository:


git clone https://github.com/WillyMcClanathan/ai-soc-analyst-agent.git

cd ai-soc-analyst-agent


2. Create and activate a virtual environment:

Windows:

python -m venv venv
venv\Scripts\activate


macOS / Linux:

python -m venv venv
source venv/bin/activate


3. Install dependencies:


pip install -r requirements.txt


4. Initialize the database:


python src/soc/db/migrate.py


5. Import demo logs:


python src/soc/ingestion/batch_import.py


6. Start the web application:


python src/soc/web/app.py


---

## Security Notice

This repository does not include:
- Real production logs
- API keys or credentials
- Sensitive infrastructure data

All included log files are sanitized demo data.

---

## Educational Purpose

This project was developed to demonstrate:

- Detection engineering fundamentals
- Log parsing and normalization
- Incident lifecycle modeling
- SOC workflow automation
- AI-assisted security analysis

It is not intended for direct production deployment.

---

## Planned Enhancements

- MITRE ATT&CK technique mapping
- Real-time log streaming
- Threat intelligence enrichment
- Behavioral anomaly detection
- Automated containment workflows
- Role-based access control

---

## License

Released under the MIT License.
