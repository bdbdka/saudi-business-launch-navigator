"""Typed environment-based application configuration."""

import ipaddress
import json
from enum import StrEnum
from functools import lru_cache
from typing import Annotated, Literal, Self
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEFAULT_LOCAL_DATABASE_URL = "postgresql+psycopg://navigator:navigator_dev@localhost:5432/navigator"


class CatalogDataMode(StrEnum):
    """Explicitly distinguish a governed catalog from the synthetic demo catalog."""

    GOVERNED_REAL_CATALOG = "GOVERNED_REAL_CATALOG"
    PORTFOLIO_DEMO_CATALOG = "PORTFOLIO_DEMO_CATALOG"


class Settings(BaseSettings):
    """Validated settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SBLN_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Saudi Business Launch Navigator"
    environment: Literal["local", "test", "ci", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: SecretStr = SecretStr(DEFAULT_LOCAL_DATABASE_URL)
    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "openai_api_key"),
    )
    openai_model: str = Field(default="gpt-5.6", min_length=1, max_length=100)
    openai_timeout_seconds: float = Field(default=20.0, ge=1.0, le=120.0)
    openai_max_output_tokens: int = Field(default=1200, ge=128, le=4096)
    api_max_natural_language_chars: int = Field(default=2000, ge=100, le=8000)
    api_max_request_bytes: int = Field(default=16_384, ge=1024, le=1_048_576)
    cors_allowed_origins: Annotated[tuple[str, ...], NoDecode] = ("http://localhost:3000",)
    allowed_hosts: Annotated[tuple[str, ...], NoDecode] = (
        "localhost",
        "127.0.0.1",
        "testserver",
    )
    api_docs_enabled: bool = True
    production_rehearsal: bool = False
    catalog_mode: CatalogDataMode = CatalogDataMode.GOVERNED_REAL_CATALOG
    expected_database_identity: UUID | None = None
    expected_database_name: str | None = Field(
        default=None,
        pattern=r"^[a-z][a-z0-9_]{2,62}$",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_provider_database_url(cls, value: object) -> object:
        """Use Psycopg 3 and force TLS for standard provider PostgreSQL URLs."""

        raw = value.get_secret_value() if isinstance(value, SecretStr) else value
        if not isinstance(raw, str) or not raw.startswith("postgresql://"):
            return value
        normalized = "postgresql+psycopg://" + raw.removeprefix("postgresql://")
        if "sslmode" not in parse_qs(urlsplit(normalized).query):
            separator = "&" if "?" in normalized else "?"
            normalized = f"{normalized}{separator}sslmode=require"
        return normalized

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def normalize_optional_openai_key(cls, value: object) -> object:
        """Treat an omitted or blank optional backend secret as AI disabled."""

        raw = value.get_secret_value() if isinstance(value, SecretStr) else value
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return None
        return value

    @field_validator("cors_allowed_origins", "allowed_hosts", mode="before")
    @classmethod
    def normalize_exact_value_lists(cls, value: object) -> object:
        """Accept a Render scalar reference or the existing JSON-list representation."""

        if not isinstance(value, str):
            return value
        raw = value.strip()
        if not raw.startswith("["):
            return (raw,)
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("exact value lists must contain valid JSON") from exc
        if not isinstance(decoded, list) or any(not isinstance(item, str) for item in decoded):
            raise ValueError("exact value lists must be a JSON array of strings")
        return tuple(decoded)

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_cors_origins(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Require unique, exact HTTP(S) origins and reject wildcard configuration."""
        if not values:
            raise ValueError("cors_allowed_origins must not be empty")
        if len(values) != len(set(values)):
            raise ValueError("cors_allowed_origins must not contain duplicates")
        for value in values:
            parsed = urlsplit(value)
            if (
                "*" in value
                or parsed.scheme not in {"http", "https"}
                or parsed.hostname is None
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError("cors_allowed_origins must contain explicit HTTP(S) origins")
            if _is_unspecified_host(parsed.hostname):
                raise ValueError("cors_allowed_origins must not use wildcard network addresses")
        return values

    @field_validator("allowed_hosts")
    @classmethod
    def validate_allowed_hosts(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Reject wildcard or scheme-bearing hosts; proxy trust stays provider-specific."""
        if not values:
            raise ValueError("allowed_hosts must not be empty")
        if len(values) != len(set(values)):
            raise ValueError("allowed_hosts must not contain duplicates")
        for value in values:
            if "*" in value or "://" in value or "/" in value or not value.strip():
                raise ValueError("allowed_hosts must contain explicit host names")
            if _is_unspecified_host(value):
                raise ValueError("allowed_hosts must not use wildcard network addresses")
        return values

    @model_validator(mode="after")
    def validate_database_url(self) -> Self:
        """Validate database and fail-closed production boundary configuration."""
        database_url = self.database_url.get_secret_value()
        if not database_url.startswith("postgresql+psycopg://"):
            raise ValueError("database_url must use the postgresql+psycopg scheme")
        if not self.openai_model.strip():
            raise ValueError("openai_model must not be blank")
        if self.environment == "production" and self.api_docs_enabled:
            raise ValueError("api_docs_enabled must be false in production")
        if self.catalog_mode is CatalogDataMode.PORTFOLIO_DEMO_CATALOG:
            if self.expected_database_identity is None or self.expected_database_name is None:
                raise ValueError(
                    "portfolio demo catalog_mode requires expected_database_identity and "
                    "expected_database_name"
                )
        elif self.expected_database_identity is not None or self.expected_database_name is not None:
            raise ValueError(
                "expected database identity and name are only valid for portfolio demo catalog_mode"
            )
        if self.environment == "production":
            self._validate_production_settings(database_url)
        elif self.catalog_mode is CatalogDataMode.GOVERNED_REAL_CATALOG:
            self._validate_internal_governed_settings(database_url)
        return self

    def _validate_internal_governed_settings(self, database_url: str) -> None:
        """Keep the unpublished governed catalog on an explicit loopback boundary."""

        database_host = urlsplit(database_url).hostname
        if database_host is None or not _is_loopback_host(database_host):
            raise ValueError("nonproduction governed database_url must use a loopback host")
        for origin in self.cors_allowed_origins:
            hostname = urlsplit(origin).hostname
            if hostname is None or not _is_loopback_host(hostname):
                raise ValueError("nonproduction governed CORS origins must be loopback origins")
        if any(not _is_loopback_host(host) for host in self.allowed_hosts):
            raise ValueError("nonproduction governed allowed_hosts must be loopback hosts")

    def _validate_production_settings(self, database_url: str) -> None:
        """Reject implicit, local, or mixed-mode settings at the production boundary."""

        if database_url == DEFAULT_LOCAL_DATABASE_URL:
            raise ValueError("production database_url must be explicitly configured")
        database_host = urlsplit(database_url).hostname
        if database_host is None:
            raise ValueError("production database_url must contain a host")
        if _is_unspecified_host(database_host):
            raise ValueError("production database_url must not use a wildcard host")
        database_is_loopback = _is_loopback_host(database_host)
        if self.production_rehearsal:
            if not database_is_loopback and database_host != "database":
                raise ValueError(
                    "production rehearsal database_url must use loopback or the isolated "
                    "Compose database service"
                )
        elif database_is_loopback:
            raise ValueError("production database_url must not use a loopback host")
        ssl_mode = parse_qs(urlsplit(database_url).query).get("sslmode", [None])[-1]
        secure_ssl_modes = {"require", "verify-ca", "verify-full"}
        if not self.production_rehearsal and ssl_mode not in secure_ssl_modes:
            raise ValueError("production database_url must require PostgreSQL TLS")

        for origin in self.cors_allowed_origins:
            parsed = urlsplit(origin)
            assert parsed.hostname is not None  # enforced by the field validator
            is_loopback = _is_loopback_host(parsed.hostname)
            if self.production_rehearsal:
                if parsed.scheme != "http" or not is_loopback:
                    raise ValueError(
                        "production rehearsal CORS origins must be explicit HTTP loopback origins"
                    )
            elif parsed.scheme != "https" or is_loopback:
                raise ValueError("production CORS origins must be explicit nonlocal HTTPS origins")

        for host in self.allowed_hosts:
            is_loopback = _is_loopback_host(host)
            if self.production_rehearsal and not is_loopback:
                raise ValueError("production rehearsal allowed_hosts must be loopback hosts")
            if not self.production_rehearsal and is_loopback:
                raise ValueError("production allowed_hosts must be nonlocal hosts")


def _is_loopback_host(value: str) -> bool:
    """Return whether a host is explicitly local to the current machine."""

    normalized = value.strip().removeprefix("[").removesuffix("]").lower()
    if normalized in {"localhost", "testserver"} or normalized.endswith(".localhost"):
        return True
    try:
        address = ipaddress.ip_address(normalized)
        return address.is_loopback
    except ValueError:
        return False


def _is_unspecified_host(value: str) -> bool:
    """Return whether a host is an IPv4 or IPv6 wildcard bind address."""

    normalized = value.strip().removeprefix("[").removesuffix("]").lower()
    try:
        return ipaddress.ip_address(normalized).is_unspecified
    except ValueError:
        return False


@lru_cache
def get_settings() -> Settings:
    """Return one validated settings instance for the process."""
    return Settings()
