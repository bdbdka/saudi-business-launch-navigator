"""Fail-closed production configuration tests."""

import uuid

import pytest
from pydantic import ValidationError

from saudi_business_launch_navigator.core.config import Settings


def _production_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "_env_file": None,
        "environment": "production",
        "api_docs_enabled": False,
        "database_url": (
            "postgresql+psycopg://runtime:secret@db.internal/navigator?sslmode=require"
        ),
        "cors_allowed_origins": ("https://navigator.example.invalid",),
        "allowed_hosts": ("api.example.invalid",),
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def test_production_accepts_only_explicit_hardened_configuration() -> None:
    settings = _production_settings()

    assert settings.environment == "production"
    assert settings.api_docs_enabled is False
    assert settings.production_rehearsal is False
    assert settings.catalog_mode.value == "GOVERNED_REAL_CATALOG"


@pytest.mark.parametrize(
    ("origin_value", "host_value"),
    [
        ("https://sbln-portfolio-demo-web.onrender.com", "sbln-portfolio-demo-api.onrender.com"),
        (
            '["https://sbln-portfolio-demo-web.onrender.com"]',
            '["sbln-portfolio-demo-api.onrender.com"]',
        ),
    ],
)
def test_render_service_reference_values_are_normalized_without_weakening_validation(
    monkeypatch: pytest.MonkeyPatch,
    origin_value: str,
    host_value: str,
) -> None:
    monkeypatch.setenv("SBLN_ENVIRONMENT", "production")
    monkeypatch.setenv("SBLN_API_DOCS_ENABLED", "false")
    monkeypatch.setenv(
        "SBLN_DATABASE_URL",
        "postgresql+psycopg://runtime:secret@db.internal/navigator?sslmode=require",
    )
    monkeypatch.setenv("SBLN_CATALOG_MODE", "PORTFOLIO_DEMO_CATALOG")
    monkeypatch.setenv(
        "SBLN_EXPECTED_DATABASE_IDENTITY",
        "143e0ec8-ff17-5955-8e89-aab9932a2577",
    )
    monkeypatch.setenv("SBLN_EXPECTED_DATABASE_NAME", "navigator_portfolio_demo")
    monkeypatch.setenv("SBLN_CORS_ALLOWED_ORIGINS", origin_value)
    monkeypatch.setenv("SBLN_ALLOWED_HOSTS", host_value)

    settings = Settings(_env_file=None)

    assert settings.cors_allowed_origins == ("https://sbln-portfolio-demo-web.onrender.com",)
    assert settings.allowed_hosts == ("sbln-portfolio-demo-api.onrender.com",)


def test_standard_managed_provider_url_is_forced_to_psycopg3_and_tls() -> None:
    settings = _production_settings(
        database_url="postgresql://runtime:secret@db.internal/navigator"
    )

    normalized = settings.database_url.get_secret_value()
    assert normalized.startswith("postgresql+psycopg://")
    assert normalized.endswith("?sslmode=require")


def test_portfolio_demo_mode_requires_an_explicit_database_identity_and_name() -> None:
    with pytest.raises(ValidationError, match="requires expected_database_identity"):
        _production_settings(catalog_mode="PORTFOLIO_DEMO_CATALOG")

    identity = uuid.UUID("143e0ec8-ff17-5955-8e89-aab9932a2577")
    settings = _production_settings(
        catalog_mode="PORTFOLIO_DEMO_CATALOG",
        expected_database_identity=identity,
        expected_database_name="navigator_portfolio_demo",
    )
    assert settings.expected_database_identity == identity
    assert settings.expected_database_name == "navigator_portfolio_demo"

    with pytest.raises(ValidationError, match="only valid for portfolio demo"):
        _production_settings(expected_database_identity=identity)


def test_nonproduction_governed_mode_cannot_bind_external_infrastructure() -> None:
    with pytest.raises(ValidationError, match="loopback host"):
        Settings(
            _env_file=None,
            environment="local",
            database_url="postgresql+psycopg://runtime:secret@db.internal/navigator",
        )
    with pytest.raises(ValidationError, match="CORS origins"):
        Settings(
            _env_file=None,
            cors_allowed_origins=("http://navigator.example.invalid",),
        )
    with pytest.raises(ValidationError, match="allowed_hosts"):
        Settings(_env_file=None, allowed_hosts=("api.example.invalid",))


def test_blank_optional_openai_key_keeps_guided_mode_enabled_without_ai() -> None:
    settings = _production_settings(openai_api_key="   ")

    assert settings.openai_api_key is None


def test_production_rejects_implicit_local_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SBLN_DATABASE_URL", raising=False)

    with pytest.raises(ValidationError, match="database_url must be explicitly configured"):
        Settings(_env_file=None, environment="production", api_docs_enabled=False)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("database_url", "postgresql+psycopg://runtime:secret@127.0.0.1/db", "loopback"),
        (
            "database_url",
            "postgresql+psycopg://runtime:secret@db.internal/navigator",
            "PostgreSQL TLS",
        ),
        ("cors_allowed_origins", ("http://navigator.example.invalid",), "nonlocal HTTPS"),
        ("cors_allowed_origins", ("https://localhost:3000",), "nonlocal HTTPS"),
        ("cors_allowed_origins", ("https://0.0.0.0:3000",), "wildcard network"),
        ("allowed_hosts", ("127.0.0.1",), "nonlocal hosts"),
    ],
)
def test_production_rejects_local_or_insecure_values(
    field: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        _production_settings(**{field: value})


def test_production_rehearsal_is_explicit_and_local_only() -> None:
    settings = _production_settings(
        production_rehearsal=True,
        database_url="postgresql+psycopg://runtime:rehearsal@127.0.0.1:55432/navigator",
        cors_allowed_origins=("http://127.0.0.1:13000",),
        allowed_hosts=("127.0.0.1",),
    )

    assert settings.production_rehearsal is True

    compose_settings = _production_settings(
        production_rehearsal=True,
        database_url="postgresql+psycopg://runtime:rehearsal@database:5432/navigator",
        cors_allowed_origins=("http://127.0.0.1:13002",),
        allowed_hosts=("127.0.0.1",),
    )
    assert compose_settings.production_rehearsal is True


def test_rehearsal_cannot_use_default_database_or_nonlocal_http() -> None:
    with pytest.raises(ValidationError, match="explicitly configured"):
        _production_settings(
            production_rehearsal=True,
            cors_allowed_origins=("http://127.0.0.1:13000",),
            allowed_hosts=("127.0.0.1",),
            database_url="postgresql+psycopg://navigator:navigator_dev@localhost:5432/navigator",
        )
    with pytest.raises(ValidationError, match="HTTP loopback"):
        _production_settings(
            production_rehearsal=True,
            database_url=("postgresql+psycopg://runtime:rehearsal@127.0.0.1:55432/navigator"),
            cors_allowed_origins=("http://navigator.example.invalid",),
            allowed_hosts=("127.0.0.1",),
        )
    with pytest.raises(ValidationError, match="isolated Compose database service"):
        _production_settings(
            production_rehearsal=True,
            database_url="postgresql+psycopg://runtime:rehearsal@db.internal/navigator",
            cors_allowed_origins=("http://127.0.0.1:13002",),
            allowed_hosts=("127.0.0.1",),
        )


@pytest.mark.parametrize(
    ("address", "url_host"),
    (("0.0.0.0", "0.0.0.0"), ("::", "[::]")),
)
def test_production_rehearsal_rejects_ipv4_and_ipv6_wildcards(
    address: str,
    url_host: str,
) -> None:
    safe_database_url = "postgresql+psycopg://runtime:rehearsal@127.0.0.1:55432/navigator"
    with pytest.raises(ValidationError, match="database_url must not use a wildcard host"):
        _production_settings(
            production_rehearsal=True,
            database_url=(f"postgresql+psycopg://runtime:rehearsal@{url_host}:55432/navigator"),
            cors_allowed_origins=("http://127.0.0.1:13000",),
            allowed_hosts=("127.0.0.1",),
        )
    with pytest.raises(ValidationError, match="wildcard network"):
        _production_settings(
            production_rehearsal=True,
            database_url=safe_database_url,
            cors_allowed_origins=(f"http://{url_host}:13000",),
            allowed_hosts=("127.0.0.1",),
        )
    with pytest.raises(ValidationError, match="wildcard network"):
        _production_settings(
            production_rehearsal=True,
            database_url=safe_database_url,
            cors_allowed_origins=("http://127.0.0.1:13000",),
            allowed_hosts=(address,),
        )


def test_local_defaults_remain_available_outside_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SBLN_ENVIRONMENT", raising=False)
    monkeypatch.delenv("SBLN_DATABASE_URL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.environment == "local"
    assert settings.cors_allowed_origins == ("http://localhost:3000",)
