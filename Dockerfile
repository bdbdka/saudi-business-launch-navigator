FROM ghcr.io/astral-sh/uv:0.12.2 AS uv

FROM python:3.13-slim-bookworm AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md ./
COPY src/saudi_business_launch_navigator/__init__.py \
    ./src/saudi_business_launch_navigator/
COPY src/saudi_business_launch_navigator/api ./src/saudi_business_launch_navigator/api
COPY src/saudi_business_launch_navigator/core ./src/saudi_business_launch_navigator/core
COPY src/saudi_business_launch_navigator/db ./src/saudi_business_launch_navigator/db
COPY src/saudi_business_launch_navigator/checklist ./src/saudi_business_launch_navigator/checklist
COPY src/saudi_business_launch_navigator/interpretation ./src/saudi_business_launch_navigator/interpretation
COPY src/saudi_business_launch_navigator/portfolio_demo \
    ./src/saudi_business_launch_navigator/portfolio_demo
COPY src/saudi_business_launch_navigator/rules/__init__.py \
    src/saudi_business_launch_navigator/rules/conditions.py \
    ./src/saudi_business_launch_navigator/rules/

RUN uv sync --frozen --no-dev --no-editable


FROM python:3.13-slim-bookworm AS runtime

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid 10001 navigator \
    && useradd --uid 10001 --gid navigator --create-home --home-dir /home/navigator navigator

WORKDIR /app

COPY --from=builder --chown=navigator:navigator /app/.venv ./.venv
COPY --chown=navigator:navigator alembic.ini ./alembic.ini
COPY --chown=navigator:navigator alembic ./alembic
COPY --chown=navigator:navigator public_demo ./public_demo

USER navigator

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=5 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\", \"8000\")}/health/live', timeout=2).read()"]

CMD ["sh", "-c", "exec uvicorn saudi_business_launch_navigator.api.app:create_app --factory --host 0.0.0.0 --port \"${PORT:-8000}\" --no-server-header"]
