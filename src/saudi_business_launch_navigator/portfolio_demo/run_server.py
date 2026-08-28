"""Initialize with the owner connection, then exec the API as a SELECT-only login."""

from __future__ import annotations

import os

from saudi_business_launch_navigator.core.config import get_settings
from saudi_business_launch_navigator.portfolio_demo.initialize import main as initialize_demo
from saudi_business_launch_navigator.portfolio_demo.store import (
    portfolio_demo_runtime_database_url,
)

_RUNTIME_PASSWORD_ENV = "SBLN_DEMO_RUNTIME_DATABASE_PASSWORD"


def main() -> None:
    runtime_password = os.environ.get(_RUNTIME_PASSWORD_ENV, "")
    if len(runtime_password) < 24:
        raise RuntimeError("portfolio demo runtime database credential is unavailable")
    owner_settings = get_settings()
    owner_database_url = owner_settings.database_url.get_secret_value()

    initialize_demo()

    os.environ["SBLN_DATABASE_URL"] = portfolio_demo_runtime_database_url(
        owner_database_url,
        runtime_password,
    )
    os.environ.pop(_RUNTIME_PASSWORD_ENV, None)
    get_settings.cache_clear()
    get_settings()

    raw_port = os.environ.get("PORT", "8000")
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise RuntimeError("portfolio demo server port is invalid") from exc
    if not 1 <= port <= 65535:
        raise RuntimeError("portfolio demo server port is invalid")
    os.execvp(
        "uvicorn",
        (
            "uvicorn",
            "saudi_business_launch_navigator.api.app:create_app",
            "--factory",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
            "--no-server-header",
        ),
    )


if __name__ == "__main__":
    main()
