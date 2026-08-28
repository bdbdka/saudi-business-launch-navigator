"""Static fail-closed checks for deployment assets."""

from __future__ import annotations

import re
from pathlib import Path

import yaml  # type: ignore[import-untyped]

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")


def test_backend_image_is_locked_non_root_and_production_only() -> None:
    dockerfile = _read("Dockerfile")

    assert "FROM python:3.13-slim-bookworm AS runtime" in dockerfile
    assert "ghcr.io/astral-sh/uv:0.12.2" in dockerfile
    assert "uv sync --frozen --no-dev --no-editable" in dockerfile
    assert "WORKDIR /app" in dockerfile
    assert "/build/.venv" not in dockerfile
    assert "COPY --chown=navigator:navigator alembic ./alembic" in dockerfile
    assert "COPY --chown=navigator:navigator public_demo ./public_demo" in dockerfile
    assert "COPY src ./src" not in dockerfile
    assert "src/saudi_business_launch_navigator/rules/conditions.py" in dockerfile
    assert 'os.getenv(\\"PORT\\", \\"8000\\")' in dockerfile
    assert "${PORT:-8000}" in dockerfile
    assert "USER navigator" in dockerfile
    assert "/health/live" in dockerfile
    assert "--reload" not in dockerfile
    assert "COPY .env" not in dockerfile


def test_frontend_image_requires_public_api_origin_and_runs_non_root() -> None:
    dockerfile = _read("frontend/Dockerfile")

    assert "FROM node:22-bookworm-slim AS runtime" in dockerfile
    assert "npm ci" in dockerfile
    assert 'test -n "$NEXT_PUBLIC_API_BASE_URL"' in dockerfile
    assert "NEXT_PUBLIC_CATALOG_MODE" in dockerfile
    assert "process.env.PORT" in dockerfile
    assert "/app/.next/standalone" in dockerfile
    assert "USER node" in dockerfile
    assert "npm run dev" not in dockerfile
    assert "COPY .env" not in dockerfile


def test_portfolio_demo_compose_is_loopback_only_and_identity_bound() -> None:
    compose = _read("compose.portfolio-demo.yaml")

    assert "navigator_portfolio_demo" in compose
    assert "PORTFOLIO_DEMO_CATALOG" in compose
    assert "143e0ec8-ff17-5955-8e89-aab9932a2577" in compose
    assert "SBLN_EXPECTED_DATABASE_NAME: navigator_portfolio_demo" in compose
    assert "navigator_demo_runtime:" in compose
    assert "SBLN_DEMO_RUNTIME_DATABASE_PASSWORD" in compose
    assert "saudi_business_launch_navigator.portfolio_demo.initialize" in compose
    assert "synthetic-portfolio-demo-only" in compose
    assert "127.0.0.1:${SBLN_DEMO_DATABASE_PORT:-55434}:5432" in compose
    assert "127.0.0.1:${SBLN_DEMO_API_PORT:-18002}:8000" in compose
    assert "127.0.0.1:${SBLN_DEMO_WEB_PORT:-13002}:3000" in compose
    assert "ALLOW_UNPUBLISHED" not in compose
    assert "backend_database" in compose
    assert "frontend_backend" in compose
    assert not re.search(r'(?m)^\s*-\s*"?(?:0\.0\.0\.0|\[::\]):', compose)


def test_render_blueprint_requests_manual_free_evaluation_and_blocks_database_access() -> None:
    blueprint = _read("render.yaml")
    parsed = yaml.safe_load(blueprint)

    assert blueprint.count("plan: free") == 3
    assert 'postgresMajorVersion: "18"' in blueprint
    assert "ipAllowList: []" in blueprint
    assert blueprint.count('autoDeployTrigger: "off"') == 2
    assert "healthCheckPath: /health/ready" in blueprint
    assert "healthCheckPath: /ar" in blueprint
    assert "PORTFOLIO_DEMO_CATALOG" in blueprint
    assert "SBLN_DATABASE_URL" in blueprint
    assert "saudi_business_launch_navigator.portfolio_demo.run_server" in blueprint
    assert "SBLN_DEMO_RUNTIME_DATABASE_PASSWORD" in blueprint
    assert "generateValue: true" in blueprint
    assert "SBLN_EXPECTED_DATABASE_NAME" in blueprint
    assert "property: connectionString" in blueprint
    assert "NEXT_PUBLIC_API_BASE_URL" in blueprint
    assert "NEXT_PUBLIC_CATALOG_MODE" in blueprint
    assert "sync: false" in blueprint
    assert "OPENAI_API_KEY" not in blueprint
    assert "ALLOW_UNPUBLISHED" not in blueprint
    assert not re.search(r"postgresql(?:\+psycopg)?://[^\s]+:[^\s]+@", blueprint)
    assert len(parsed["databases"]) == 1
    assert [service["type"] for service in parsed["services"]] == ["web", "web"]
    assert all(service["autoDeployTrigger"] == "off" for service in parsed["services"])


def test_production_environment_templates_are_secret_free_and_fail_closed() -> None:
    backend_environment = _read(".env.production.example")
    frontend_environment = _read("frontend/.env.production.example")
    gitignore = _read(".gitignore")
    frontend_gitignore = _read("frontend/.gitignore")

    assert "SBLN_ENVIRONMENT=production" in backend_environment
    assert "SBLN_DATABASE_URL=\n" in backend_environment
    assert "SBLN_CATALOG_MODE=PORTFOLIO_DEMO_CATALOG" in backend_environment
    assert "SBLN_EXPECTED_DATABASE_IDENTITY" in backend_environment
    assert "SBLN_EXPECTED_DATABASE_NAME" in backend_environment
    assert "SBLN_DEMO_RUNTIME_DATABASE_PASSWORD" in backend_environment
    assert "SBLN_API_DOCS_ENABLED=false" in backend_environment
    assert "OPENAI_API_KEY=\n" in backend_environment
    assert "example.invalid" in backend_environment
    assert "NEXT_PUBLIC_API_BASE_URL=https://" in frontend_environment
    assert "NEXT_PUBLIC_CATALOG_MODE=PORTFOLIO_DEMO_CATALOG" in frontend_environment
    assert "example.invalid" in frontend_environment
    assert "API_KEY" not in frontend_environment
    assert "DATABASE_URL" not in frontend_environment
    assert "!.env.production.example" in gitignore
    assert "!frontend/.env.production.example" in gitignore
    assert "!.env.production.example" in frontend_gitignore


def test_ci_supplies_explicit_frontend_production_build_contract() -> None:
    workflow = _read(".github/workflows/ci.yml")

    assert workflow.count("NEXT_PUBLIC_API_BASE_URL: https://api.example.invalid") == 1
    assert workflow.count("NEXT_PUBLIC_CATALOG_MODE: PORTFOLIO_DEMO_CATALOG") == 1
    assert "--build-arg NEXT_PUBLIC_API_BASE_URL=https://api.example.invalid" in workflow
    assert "--build-arg NEXT_PUBLIC_CATALOG_MODE=PORTFOLIO_DEMO_CATALOG" in workflow


def test_postgres_role_policy_denies_public_and_runtime_writes() -> None:
    role_policy = _read("deploy/postgres/roles.sql.example")

    assert "CREATE ROLE navigator_migration" in role_policy
    assert "CREATE ROLE navigator_runtime" in role_policy
    assert role_policy.count("NOLOGIN") >= 4
    assert "REVOKE ALL PRIVILEGES ON DATABASE" in role_policy
    assert "REVOKE CREATE ON SCHEMA public FROM PUBLIC" in role_policy
    assert "REVOKE ALL PRIVILEGES ON SCHEMA navigator FROM PUBLIC" in role_policy
    runtime_table_revoke = (
        "REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA navigator FROM navigator_runtime"
    )
    assert runtime_table_revoke in role_policy
    assert "GRANT SELECT ON ALL TABLES IN SCHEMA navigator TO navigator_runtime" not in role_policy
    assert "REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER" in role_policy
    assert "default_transaction_read_only = on" in role_policy
    assert not re.search(r"\bPASSWORD\s+['\"]", role_policy, re.IGNORECASE)
    assert not re.search(r"CREATE\s+ROLE\s+\w+\s+LOGIN", role_policy, re.IGNORECASE)


def test_docker_contexts_exclude_secrets_data_and_test_artifacts() -> None:
    backend_ignore = _read(".dockerignore")
    frontend_ignore = _read("frontend/.dockerignore")

    for excluded in (".git", ".env", "data", "docs", "tests", "frontend", "*.dump"):
        assert excluded in backend_ignore
    for excluded in (".git", ".env", ".next", "node_modules", "test-results"):
        assert excluded in frontend_ignore
