# Saudi Business Launch Navigator

## دليل تأسيس المنشآت في السعودية

An Arabic-first, bilingual web application that turns structured business
answers into an explainable launch checklist for coffee shops, restaurants,
and cloud kitchens. The project demonstrates deterministic decision rules,
source-aware data modeling, and a production-shaped Next.js/FastAPI/PostgreSQL
stack.

This repository uses explicitly synthetic portfolio-demo data. It demonstrates
the application architecture without presenting its sample authorities,
sources, or checklist items as Saudi regulation.

## Overview

The Navigator guides a user through the minimum questions needed for the
selected activity, evaluates the answers with three-valued logic, and groups
the result into items that apply, do not apply, or need more information. Each
result includes an applicability reason, source metadata, coverage warnings,
and practical next-step guidance.

The stated pilot context is Riyadh and Jeddah. The current synthetic demo does
not collect or evaluate city, and it implements no city-specific logic.

## Features

- Arabic-first interface with English routes and full RTL/LTR support
- Guided questionnaire for coffee shops, restaurants, and cloud kitchens
- Deterministic applicability rules where unknown remains distinct from false
- Personalized checklist with traceable reasons for every outcome
- Navigation and actionability guidance kept separate from applicability
- Source, authority, freshness, and coverage metadata in API results
- Missing-information links back to the relevant questionnaire item
- Optional OpenAI-assisted structured interpretation and explanation
- Responsive Next.js frontend and typed FastAPI API
- PostgreSQL migrations, identity-bound synthetic demo data, and health checks
- Docker Compose and Render deployment configuration

## Architecture

```text
Next.js browser interface
          |
          v
      FastAPI API  ------>  Optional OpenAI API
          |                 interpretation/explanation only
          v
Deterministic Python rules
          |
          v
      PostgreSQL
```

AI does not decide regulatory applicability. The guided questionnaire and
deterministic checklist remain fully usable without an OpenAI API key.

See [Architecture](docs/architecture.md) and
[Methodology](docs/methodology.md) for the component boundaries and decision
model.

## Tech stack

| Area | Technologies |
| --- | --- |
| Frontend | Next.js 16, React 19, TypeScript, CSS |
| Backend | Python 3.13, FastAPI, Pydantic, SQLAlchemy async |
| Data | PostgreSQL 18, Alembic |
| Optional AI | OpenAI Responses API with strict structured outputs |
| Testing | pytest, Vitest, Testing Library, Playwright |
| Quality and security | Ruff, mypy, pip-audit, npm audit, CodeQL, Dependabot |
| Delivery | Docker, Docker Compose, Render blueprint |

## Reliability design

- Applicability is computed from versioned structured conditions, not prose.
- `true`, `false`, and `unknown` are independent values; unknown is never
  silently converted to false.
- Catalog mode, database name, schema, and dataset identity are verified before
  demo traffic is served.
- Invalid catalog state fails closed instead of falling back to invented data.
- Liveness is independent from database readiness.
- API errors omit database details, credentials, and internal exceptions.
- The runtime database role is read-only and narrowly granted.
- CORS and trusted hosts use explicit allowlists.

## Portfolio demo

The bundled dataset contains fictional authorities, sources, requirements, and
guidance. Sample links use the reserved `example.invalid` domain, and the UI
labels demo responses so they cannot be mistaken for official evidence.

The local demo exposes:

- frontend: `http://127.0.0.1:13002/ar`
- backend: `http://127.0.0.1:18002`
- liveness: `http://127.0.0.1:18002/health/live`
- readiness: `http://127.0.0.1:18002/health/ready`
- PostgreSQL: `127.0.0.1:55434`

## Running locally

### Docker Compose

Prerequisites: Docker with Compose v2.

```bash
export SBLN_DEMO_DATABASE_PASSWORD="$(openssl rand -hex 24)"
export SBLN_DEMO_RUNTIME_DATABASE_PASSWORD="$(openssl rand -hex 24)"
docker compose -f compose.portfolio-demo.yaml up -d --build
```

Open `http://127.0.0.1:13002/ar` for Arabic or
`http://127.0.0.1:13002/en` for English.

The OpenAI feature is optional. To enable it for a local session, set
`OPENAI_API_KEY` in the shell before starting Compose. Never commit the key.

Stop the stack with:

```bash
docker compose -f compose.portfolio-demo.yaml down
```

Add `--volumes` only when you intentionally want to remove the synthetic local
database volume.

## Testing

Backend quality and test suite:

```bash
docker run --name sbln-test-postgres --rm -d \
  -e POSTGRES_DB=navigator \
  -e POSTGRES_USER=navigator \
  -e POSTGRES_PASSWORD=navigator_test_only \
  -p 127.0.0.1:55435:5432 \
  postgres:18
export SBLN_DATABASE_URL='postgresql+psycopg://navigator:navigator_test_only@127.0.0.1:55435/navigator'
uv sync --locked
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest -q
uv run pip-audit
docker stop sbln-test-postgres
```

The credential above is an intentionally disposable local-test value. The
integration tests create and remove only uniquely prefixed databases on that
dedicated PostgreSQL service; never point them at a real catalog.

Frontend quality and test suite:

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm test
npm run build
npm audit
```

With the Compose stack running, install Playwright's browser once and run the
real browser flow:

```bash
cd frontend
npx playwright install chromium
SBLN_E2E_BASE_URL=http://127.0.0.1:13002 npm run test:e2e
```

See [Testing](docs/testing.md) for test layers and expected prerequisites.

## Deployment

`render.yaml` defines a PostgreSQL database, FastAPI service, and Next.js
service for the synthetic portfolio demo. Automatic deployment is disabled;
origins, trusted hosts, and secrets must be configured before a manual deploy.

See [Deployment](docs/deployment.md) and [Security](docs/security.md).

## Project structure

```text
alembic/                    PostgreSQL schema migrations
docs/                       architecture, deployment, security, and testing
frontend/                   Next.js application and browser tests
public_demo/                synthetic portfolio catalog
src/saudi_business_launch_navigator/
  api/                      FastAPI routes and application composition
  checklist/                questionnaire and checklist services
  core/                     typed configuration and logging
  db/                       SQLAlchemy models and database helpers
  interpretation/           optional bounded OpenAI integration
  portfolio_demo/           demo database initialization and validation
  rules/                    deterministic three-valued conditions
tests/                      backend, database, API, and deployment tests
compose.portfolio-demo.yaml local production-shaped demo stack
render.yaml                 Render infrastructure blueprint
```

## Disclaimer

This portfolio demo uses sample data. It is not a government service, does not
provide legal or regulatory advice, and does not guarantee compliance,
licensing, approval, cost, or processing time.
