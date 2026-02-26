# Security Policy

## Purpose

This project is a locally developed educational SOC automation platform designed to demonstrate detection engineering, log ingestion, incident lifecycle management, and AI-assisted security analysis.

It is not intended for production deployment.

---

## Reporting Security Issues

If you discover a security issue within this repository, please do not open a public issue describing the vulnerability.

Instead, contact the repository owner directly:

William McClanathan  
Email: william.mcclanathan@gmail.com

Please include:
- A clear description of the issue
- Steps to reproduce (if applicable)
- Potential impact

All legitimate reports will be reviewed and addressed in a timely manner.

---

## Sensitive Data Policy

This repository does NOT include:

- Real production logs
- API keys or authentication tokens
- Infrastructure configuration files
- Sensitive credentials
- Operational incident data

All included data is sanitized or demo data.

---

## Secure Usage Guidelines

If you choose to run this project locally:

- Do not use real production logs.
- Do not store API keys in source files.
- Use environment variables for sensitive configuration.
- Do not expose the local web interface publicly.

---

## Limitations

This project:

- Does not implement hardened authentication
- Does not implement encryption at rest
- Is not production-grade SOC software
- Is intended for educational and demonstration purposes only

---

## Future Security Enhancements

Planned improvements include:

- Role-based access control
- Secure authentication layer
- Encrypted credential storage
- MITRE ATT&CK technique mapping
- Threat intelligence enrichment

---

By using this project, you acknowledge that it is provided for educational purposes and should not be deployed in production environments.