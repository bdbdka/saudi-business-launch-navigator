# Deployment

The deployable portfolio topology consists of a Next.js web service, a FastAPI
API service, and PostgreSQL. `render.yaml` describes that topology for Render;
`compose.portfolio-demo.yaml` provides a production-shaped local equivalent.

Only the bundled synthetic catalog is intended for this public deployment.

## Environment variables

### Backend

| Variable | Purpose |
| --- | --- |
| `SBLN_ENVIRONMENT` | Selects local, CI, or production validation rules. |
| `SBLN_DATABASE_URL` | Server-side PostgreSQL connection string. |
| `SBLN_CATALOG_MODE` | Must be `PORTFOLIO_DEMO_CATALOG` for the public demo. |
| `SBLN_EXPECTED_DATABASE_IDENTITY` | Binds startup to the synthetic catalog database. |
| `SBLN_EXPECTED_DATABASE_NAME` | Prevents connecting to a substituted database. |
| `SBLN_DEMO_RUNTIME_DATABASE_PASSWORD` | Creates the separate read-only runtime role. |
| `SBLN_CORS_ALLOWED_ORIGINS` | Exact browser origin allowlist. |
| `SBLN_ALLOWED_HOSTS` | Exact API host allowlist. |
| `SBLN_API_DOCS_ENABLED` | Enables or disables OpenAPI documentation routes. |
| `OPENAI_API_KEY` | Optional server-side key for interpretation and explanation. |

See `.env.production.example` for the complete contract. Do not commit a real
environment file.

### Frontend

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Browser-reachable HTTPS API origin. |
| `NEXT_PUBLIC_CATALOG_MODE` | Must match `PORTFOLIO_DEMO_CATALOG`. |

These values are compiled into the frontend and are not secrets.

## Local Docker deployment

```bash
export SBLN_DEMO_DATABASE_PASSWORD="$(openssl rand -hex 24)"
export SBLN_DEMO_RUNTIME_DATABASE_PASSWORD="$(openssl rand -hex 24)"
docker compose -f compose.portfolio-demo.yaml up -d --build
docker compose -f compose.portfolio-demo.yaml ps
```

Generate URL-safe passwords, as above, because Compose interpolates them into
PostgreSQL connection URLs.

The stack binds all published ports to `127.0.0.1`. The initializer migrates an
empty database, loads the synthetic seed, verifies the catalog graph, creates a
read-only runtime role, and exits before the API starts. Inside the isolated
Compose network, services connect to PostgreSQL through the exact service name
`database`; other nonlocal database hosts remain invalid in rehearsal mode.

## Render

`render.yaml` is configured to provision:

1. PostgreSQL 18 with no public IP allowlist;
2. the FastAPI Docker service with `/health/ready`; and
3. the Next.js Docker service with `/ar` as its health path.

Before a manual deployment:

1. set `SBLN_CORS_ALLOWED_ORIGINS` to the exact frontend HTTPS origin;
2. set `SBLN_ALLOWED_HOSTS` to the exact API hostname;
3. set `NEXT_PUBLIC_API_BASE_URL` to the exact API HTTPS origin;
4. verify both services select `PORTFOLIO_DEMO_CATALOG`;
5. keep generated database credentials in the platform secret manager; and
6. confirm `/health/live`, `/health/ready`, `/ar`, and `/en` after deployment.

Automatic deploys are disabled in the blueprint. Plan names and availability
should be reviewed against Render's current offerings before use.

## Migrations and demo seed

The API service starts through
`saudi_business_launch_navigator.portfolio_demo.run_server`. On an empty target,
the initializer applies the expected Alembic revision and inserts the synthetic
catalog. On later starts, it verifies the existing database instead of silently
replacing it.

Startup fails if the database name, identity, migration, schema, catalog
fingerprint, row boundary, or runtime privileges differ from the expected demo
state.

## Health and observability

- `/health/live` confirms that the API process is running.
- `/health/ready` confirms database connectivity and the catalog boundary.
- Structured logs include safe event names and exception categories without
  secrets or connection strings.

Configure platform log retention and alerts for repeated readiness failures,
startup rejection, and elevated server errors.

## Recovery and rollback

Treat the demo database as replaceable synthetic state. Before a schema change,
take and verify a PostgreSQL backup outside Git. A failed application release
can be rolled back to the previous container image when its migration contract
is still compatible.

For an intentionally disposable demo database, the safest recovery is to
recreate an empty database and let the verified initializer rebuild it from the
checked-in migrations and synthetic catalog. Never run destructive recovery
commands against an unidentified database.
