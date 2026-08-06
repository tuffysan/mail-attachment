# Security Policy

Please do not disclose vulnerabilities in public issues. Contact the repository owner privately through GitHub.

Supported versions will be listed when the first release is published.

## Development safeguards

- Never commit `.env` or credentials.
- Database and Redis development ports bind to loopback only.
- Generated secrets should be unique per installation.
- Production deployment must use TLS and a secret manager where possible.
