# Security policy

## Reporting a vulnerability

Please use GitHub private vulnerability reporting or a private security
advisory. Do not open a public issue containing credentials, personal data, or
an exploit that could put another system or user at risk.

Include the affected component, reproducible steps, potential impact, and a
minimal proof of concept. Remove tokens, credentials, personal data, and unsafe
request payloads from logs or screenshots.

## Scope

Reports about the FastAPI service, Next.js client, deterministic rules,
configuration, database boundaries, container images, and dependency chain are
welcome. There is no bug-bounty program or guaranteed response time.

Do not test against Saudi government systems or submit real personal or
business information when demonstrating a finding. Use the bundled synthetic
portfolio dataset and local services only.

## Supported version

Security fixes target the current `main` branch. Older commits are not
maintained as separate releases.

For implemented controls and deployment guidance, see
[Security architecture](docs/security.md) and
[Deployment](docs/deployment.md).
