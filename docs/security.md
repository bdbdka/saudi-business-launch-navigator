# Security architecture

Security controls are applied at configuration, network, application,
database, and supply-chain boundaries. The portfolio demo uses only synthetic
business data and does not require names, national IDs, or exact addresses.

## Secrets and configuration

- Backend secrets are injected through environment variables or a hosting
  provider's secret manager.
- `.env` files, private keys, dumps, and backups are excluded from Git and
  container build contexts.
- Browser-visible `NEXT_PUBLIC_*` values contain only the API origin and catalog
  mode. They must never contain an API key or database URL.
- The OpenAI API key is optional, remains server-side, and is never sent to the
  browser or logged.
- Production startup validates required configuration and rejects local,
  wildcard, or non-TLS values outside an explicitly local environment.

## HTTP boundary

FastAPI uses explicit CORS origins and trusted hosts. Wildcard CORS is not part
of the deployment configuration. Security middleware adds response headers,
limits request bodies, and converts internal failures into structured errors
without returning SQL, connection strings, credentials, or stack traces.

The frontend applies a restrictive Content Security Policy. It connects only
to its configured API origin and does not call OpenAI directly.

## Catalog boundary

Catalog mode is explicit. The public deployment serves only the synthetic
portfolio catalog. Startup checks the expected database name, catalog identity,
schema inventory, migration revision, and dataset fingerprint before accepting
traffic. A mismatch fails closed.

The demo seed uses fictional authorities, requirements, and `example.invalid`
source links. API responses expose the catalog mode and sample-data warning.

## Database and containers

- PostgreSQL is not published by `render.yaml` and is bound to loopback in the
  local Compose stack.
- The demo initializer creates a separate restricted runtime role.
- Runtime transactions are read-only and grants are checked before readiness
  succeeds.
- Backend and frontend containers run as non-root users with read-only filesystems
  in Compose, dropped capabilities, and `no-new-privileges`.
- Liveness avoids a database dependency; readiness verifies the database and
  catalog boundary.

## User data

Questionnaire answers remain in browser memory for the current interaction.
The interface does not require an account, national ID, or exact address. The
optional free-text description rejects common sensitive identifiers before a
configured AI request is attempted.

## Supply chain

CI runs Ruff, mypy, pytest, pip-audit, frontend linting, type checking, unit
tests, npm audit, and production builds. CodeQL scans Python and TypeScript.
Dependabot covers Python, npm, GitHub Actions, and Docker dependencies.

GitHub Actions are pinned to commit SHAs. Container base images use versioned
tags and are monitored for updates; they are not currently digest-pinned.

## Reporting

Follow the private reporting process in the root [security policy](../SECURITY.md).
Never test a finding against third-party government services.
