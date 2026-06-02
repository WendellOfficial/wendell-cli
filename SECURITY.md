# Security Policy

## Reporting a Vulnerability

Please do not open a public issue for a suspected vulnerability.

Report security issues to security@wendellai.com with:

- affected command or package version
- reproduction steps
- expected impact
- any relevant logs with secrets removed

We will acknowledge reports as soon as practical and coordinate fixes privately
before public disclosure.

## Secrets and Credentials

The CLI may read local credentials from `~/.config/wendell/credentials.json` or
from environment variables such as `WENDELL_INKPASS_API_KEY`. Never include real
API keys, customer transcripts, or private run outputs in issues, pull requests,
or test fixtures.
