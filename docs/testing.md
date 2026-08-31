# Testing

The test strategy checks deterministic behavior at small units and repeats the
critical flow across database, API, frontend, and browser boundaries. Tests use
synthetic records and do not contact Saudi government services.

## Backend

The backend suite covers:

- synthetic catalog identity, fingerprints, and private-data exclusion;
- questionnaire reachability and unknown-answer behavior through the real
  deterministic service;
- checklist, navigation-guidance, and actionability behavior in the public
  demo scenarios;
- the production guided API flow without an OpenAI key;
- PostgreSQL migrations, exact seed idempotency, catalog identity, and
  restricted read-only roles;
- fail-closed startup, request-size limits, production configuration, and
  deployment contracts; and
- negative paths for altered database structure, identity mismatch, elevated
  privileges, and governed-data contamination.

Run:

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
docker stop sbln-test-postgres
```

Database integration tests require PostgreSQL 18. The command above starts a
dedicated disposable test server with an intentionally non-secret credential.
The tests create and remove only uniquely prefixed databases on that server.
Do not point the test suite at the application stack or a real catalog.

## Frontend

Vitest and Testing Library cover API-client errors, Arabic and English content,
catalog-mode warnings, activity selection, questionnaire navigation,
unknown-answer re-entry, result rendering, accessibility behavior, security
configuration, and the optional-AI unavailable state.

Run:

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm test
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:18002 \
  NEXT_PUBLIC_CATALOG_MODE=PORTFOLIO_DEMO_CATALOG npm run build
```

## Browser end-to-end flow

Playwright exercises the real Next.js, FastAPI, and PostgreSQL stack. It does
not mock catalog API responses. Start the Compose stack, then run:

```bash
cd frontend
npx playwright install chromium
SBLN_E2E_BASE_URL=http://127.0.0.1:13002 npm run test:e2e
```

Set `PLAYWRIGHT_CHROME_PATH` only when intentionally using an installed Chrome
binary; otherwise Playwright uses its managed Chromium.

## Security and dependency checks

```bash
uv run pip-audit
cd frontend
npm audit
```

CI also runs CodeQL and validates both production container builds. Browser E2E
tests remain a local, real-stack check because they require the complete Compose
topology.

## Test data boundary

The checked-in catalog and all test fixtures are fictional. Reserved `.invalid`
hosts prevent sample links from resolving to an official or third-party site.
Database tests create disposable state and must not point at a real regulatory
catalog.
