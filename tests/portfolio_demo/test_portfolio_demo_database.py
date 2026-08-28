"""Disposable PostgreSQL tests for the demo identity, seed, and production API."""

from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from typing import cast
from unittest.mock import patch

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from psycopg import sql
from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection

from saudi_business_launch_navigator.api.app import create_app
from saudi_business_launch_navigator.core.config import Settings, get_settings
from saudi_business_launch_navigator.db.engine import (
    create_database_engine,
    dispose_database_engine,
)
from saudi_business_launch_navigator.portfolio_demo.catalog import (
    DEMO_MIGRATION_REVISION,
    dataset_fingerprint,
    graph_sha256,
    load_portfolio_demo_spec,
)
from saudi_business_launch_navigator.portfolio_demo.initialize import (
    _initialization_lock,
    _initialize,
)
from saudi_business_launch_navigator.portfolio_demo.store import (
    PortfolioDemoDatabaseError,
    _rotate_portfolio_demo_runtime_password,
    assert_portfolio_demo_migration_target,
    assert_portfolio_demo_runtime_access,
    portfolio_demo_runtime_database_url,
    provision_portfolio_demo_runtime_role,
    seed_portfolio_demo_database,
    verify_portfolio_demo_database,
)

pytestmark = pytest.mark.integration
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
RUNTIME_PASSWORD = "portfolio_demo_runtime_test_password_only"
RESTRICTED_OWNER_PASSWORD = "portfolio_demo_restricted_owner_password"


def _connect(
    url: URL,
    database: str,
    *,
    autocommit: bool = True,
) -> psycopg.Connection[tuple[object, ...]]:
    if url.username is None or url.password is None or url.host is None:
        raise RuntimeError("portfolio demo tests require the configured local PostgreSQL service")
    return psycopg.connect(
        dbname=database,
        user=url.username,
        password=url.password,
        host=url.host,
        port=url.port or 5432,
        autocommit=autocommit,
    )


def _create_database() -> tuple[str, str]:
    base = make_url(Settings(_env_file=None).database_url.get_secret_value())
    name = f"navigator_portfolio_demo_test_{uuid.uuid4().hex[:12]}"
    with _connect(base, "postgres") as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    return name, base.set(database=name).render_as_string(hide_password=False)


def _drop_database(name: str) -> None:
    if not name.startswith("navigator_portfolio_demo_test_"):
        raise RuntimeError("refusing to drop a non-demo-test database")
    base = make_url(Settings(_env_file=None).database_url.get_secret_value())
    with _connect(base, "postgres") as admin:
        admin.execute(
            """
            SELECT pg_catalog.pg_terminate_backend(pid)
            FROM pg_catalog.pg_stat_activity
            WHERE datname = %s AND pid <> pg_catalog.pg_backend_pid()
            """,
            (name,),
        )
        admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))


def _drop_runtime_role() -> None:
    base = make_url(Settings(_env_file=None).database_url.get_secret_value())
    with _connect(base, "postgres") as admin:
        admin.execute("DROP ROLE IF EXISTS navigator_demo_runtime")


@contextmanager
def _migration_url(database_url: str) -> Iterator[None]:
    previous = os.environ.get("SBLN_DATABASE_URL")
    os.environ["SBLN_DATABASE_URL"] = database_url
    get_settings.cache_clear()
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("SBLN_DATABASE_URL", None)
        else:
            os.environ["SBLN_DATABASE_URL"] = previous
        get_settings.cache_clear()


def _upgrade(database_url: str) -> None:
    with _migration_url(database_url):
        command.upgrade(Config(os.path.join(ROOT, "alembic.ini")), DEMO_MIGRATION_REVISION)


def _demo_settings(database_url: str, *, production: bool = False) -> Settings:
    spec = load_portfolio_demo_spec()
    database_name = make_url(database_url).database
    assert database_name is not None
    return Settings(
        _env_file=None,
        environment="production" if production else "test",
        production_rehearsal=production,
        api_docs_enabled=not production,
        database_url=database_url,
        catalog_mode="PORTFOLIO_DEMO_CATALOG",
        expected_database_identity=spec.database_identity,
        expected_database_name=database_name,
        cors_allowed_origins=("http://127.0.0.1:13001",),
        allowed_hosts=("testserver", "127.0.0.1", "localhost"),
    )


def _create_restricted_owner_database(*, can_create_roles: bool) -> tuple[str, str, str]:
    _drop_runtime_role()
    base = make_url(Settings(_env_file=None).database_url.get_secret_value())
    name = f"navigator_portfolio_demo_test_{uuid.uuid4().hex[:12]}"
    owner = f"navigator_demo_owner_{uuid.uuid4().hex[:12]}"
    role_capability = sql.SQL(" CREATEROLE") if can_create_roles else sql.SQL("")
    with _connect(base, "postgres") as admin:
        admin.execute(
            sql.SQL("CREATE ROLE {} LOGIN{} PASSWORD {}").format(
                sql.Identifier(owner),
                role_capability,
                sql.Literal(RESTRICTED_OWNER_PASSWORD),
            )
        )
        admin.execute(
            sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(name),
                sql.Identifier(owner),
            )
        )
    database_url = base.set(
        username=owner,
        password=RESTRICTED_OWNER_PASSWORD,
        database=name,
    ).render_as_string(hide_password=False)
    return name, owner, database_url


def _drop_restricted_owner_database(name: str, owner: str) -> None:
    _drop_database(name)
    base = make_url(Settings(_env_file=None).database_url.get_secret_value())
    with _connect(base, "postgres") as admin:
        admin.execute("DROP ROLE IF EXISTS navigator_demo_runtime")
        admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(owner)))


def test_runtime_role_provisioning_works_for_a_non_superuser_database_owner() -> None:
    name, owner, database_url = _create_restricted_owner_database(can_create_roles=True)
    try:
        _upgrade(database_url)

        async def exercise_managed_postgres_boundary() -> None:
            settings = _demo_settings(database_url)
            engine = create_database_engine(settings)
            try:
                async with engine.connect() as connection:
                    bootstrap_state = (
                        await connection.execute(
                            text(
                                "SELECT current_user, rolsuper, rolcreaterole, rolcreatedb, "
                                "rolreplication, rolbypassrls FROM pg_catalog.pg_roles "
                                "WHERE rolname = current_user"
                            )
                        )
                    ).one()
                assert tuple(bootstrap_state) == (owner, False, True, False, False, False)

                await seed_portfolio_demo_database(engine, settings)
                await provision_portfolio_demo_runtime_role(engine, settings, RUNTIME_PASSWORD)
                await provision_portfolio_demo_runtime_role(engine, settings, RUNTIME_PASSWORD)
            finally:
                await dispose_database_engine(engine)

            runtime_url = portfolio_demo_runtime_database_url(database_url, RUNTIME_PASSWORD)
            runtime_settings = _demo_settings(runtime_url, production=True)
            runtime_engine = create_database_engine(runtime_settings)
            try:
                await assert_portfolio_demo_runtime_access(runtime_engine)
                await verify_portfolio_demo_database(runtime_engine, runtime_settings)
                async with runtime_engine.connect() as connection:
                    assert (
                        await connection.execute(
                            text("SELECT count(*) FROM portfolio_demo.catalog_identity")
                        )
                    ).scalar_one() == 1
                with pytest.raises(DBAPIError):
                    async with runtime_engine.begin() as connection:
                        await connection.execute(text("CREATE SCHEMA forbidden_runtime_schema"))
                with pytest.raises(DBAPIError):
                    async with runtime_engine.begin() as connection:
                        await connection.execute(
                            text("UPDATE portfolio_demo.catalog_identity SET dataset_revision = 2")
                        )
            finally:
                await dispose_database_engine(runtime_engine)

            runtime_connection_url = make_url(runtime_url)
            with (
                _connect(runtime_connection_url, name) as runtime_connection,
                pytest.raises(psycopg.errors.InsufficientPrivilege),
            ):
                runtime_connection.execute("SET default_transaction_read_only = off")
                runtime_connection.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(f"forbidden_{uuid.uuid4().hex[:12]}")
                    )
                )

        asyncio.run(exercise_managed_postgres_boundary())
    finally:
        _drop_restricted_owner_database(name, owner)


def test_runtime_role_provisioning_requires_createrole() -> None:
    name, owner, database_url = _create_restricted_owner_database(can_create_roles=False)
    try:
        _upgrade(database_url)

        async def exercise_missing_capability() -> None:
            settings = _demo_settings(database_url)
            engine = create_database_engine(settings)
            try:
                await seed_portfolio_demo_database(engine, settings)
                with pytest.raises(
                    PortfolioDemoDatabaseError,
                    match="database owner requires CREATEROLE",
                ):
                    await provision_portfolio_demo_runtime_role(
                        engine,
                        settings,
                        RUNTIME_PASSWORD,
                    )
            finally:
                await dispose_database_engine(engine)

        asyncio.run(exercise_missing_capability())
    finally:
        _drop_restricted_owner_database(name, owner)


@pytest.fixture(scope="module")
def demo_database() -> Iterator[tuple[str, Settings]]:
    name, database_url = _create_database()
    try:
        _upgrade(database_url)
        settings = _demo_settings(database_url)

        async def initialize() -> None:
            engine = create_database_engine(settings)
            try:
                await seed_portfolio_demo_database(engine, settings)
                await provision_portfolio_demo_runtime_role(engine, settings, RUNTIME_PASSWORD)
            finally:
                await dispose_database_engine(engine)

        asyncio.run(initialize())
        yield database_url, settings
    finally:
        _drop_database(name)
        _drop_runtime_role()


@pytest.mark.asyncio
async def test_seed_is_exact_idempotent_and_navigator_schema_stays_empty(
    demo_database: tuple[str, Settings],
) -> None:
    _database_url, settings = demo_database
    engine = create_database_engine(settings)
    spec = load_portfolio_demo_spec()
    try:
        first = await verify_portfolio_demo_database(engine, settings)
        second = await seed_portfolio_demo_database(engine, settings)
        async with engine.connect() as connection:
            counts = (
                await connection.execute(
                    text(
                        "SELECT "
                        "(SELECT count(*) FROM portfolio_demo.catalog_identity), "
                        "(SELECT count(*) FROM portfolio_demo.catalog_graph), "
                        "(SELECT count(*) FROM navigator.requirements), "
                        "(SELECT count(*) FROM navigator.requirement_publications), "
                        "(SELECT count(*) FROM navigator.journey_topic_releases), "
                        "(SELECT count(*) FROM navigator.requirement_actionability_releases)"
                    )
                )
            ).one()
    finally:
        await dispose_database_engine(engine)

    first_identity = asdict(first)
    second_identity = asdict(second)
    first_identity.pop("database_timestamp")
    second_identity.pop("database_timestamp")
    assert first_identity == second_identity
    assert second.database_timestamp >= first.database_timestamp
    assert first.database_identity == spec.database_identity
    assert first.graph_sha256 == graph_sha256(spec)
    assert first.dataset_fingerprint_sha256 == dataset_fingerprint(spec)
    assert tuple(counts) == (1, 1, 0, 0, 0, 0)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "statement",
    (
        "UPDATE portfolio_demo.catalog_identity SET dataset_revision = 2",
        "DELETE FROM portfolio_demo.catalog_graph",
        "TRUNCATE portfolio_demo.catalog_graph",
    ),
)
async def test_demo_identity_and_graph_are_immutable(
    demo_database: tuple[str, Settings],
    statement: str,
) -> None:
    _database_url, settings = demo_database
    engine = create_database_engine(settings)
    try:
        with pytest.raises(DBAPIError, match="portfolio demo catalog is immutable"):
            async with engine.begin() as connection:
                await connection.execute(text(statement))
        await verify_portfolio_demo_database(engine, settings)
    finally:
        await dispose_database_engine(engine)


@pytest.mark.asyncio
async def test_wrong_configured_identity_fails_closed(
    demo_database: tuple[str, Settings],
) -> None:
    database_url, _settings = demo_database
    wrong = Settings(
        _env_file=None,
        environment="test",
        database_url=database_url,
        catalog_mode="PORTFOLIO_DEMO_CATALOG",
        expected_database_identity=uuid.uuid4(),
        expected_database_name=make_url(database_url).database,
    )
    engine = create_database_engine(wrong)
    try:
        with pytest.raises(PortfolioDemoDatabaseError, match="configuration differs"):
            await verify_portfolio_demo_database(engine, wrong)
    finally:
        await dispose_database_engine(engine)


@pytest.mark.asyncio
async def test_wrong_configured_database_name_fails_closed(
    demo_database: tuple[str, Settings],
) -> None:
    database_url, _settings = demo_database
    spec = load_portfolio_demo_spec()
    wrong = Settings(
        _env_file=None,
        environment="test",
        database_url=database_url,
        catalog_mode="PORTFOLIO_DEMO_CATALOG",
        expected_database_identity=spec.database_identity,
        expected_database_name="different_portfolio_database",
    )
    engine = create_database_engine(wrong)
    try:
        with pytest.raises(PortfolioDemoDatabaseError, match="database name differs"):
            await verify_portfolio_demo_database(engine, wrong)
    finally:
        await dispose_database_engine(engine)


@pytest.mark.asyncio
async def test_exact_seed_is_an_approved_migration_reentry_target(
    demo_database: tuple[str, Settings],
) -> None:
    _database_url, settings = demo_database
    engine = create_database_engine(settings)
    try:
        state = await assert_portfolio_demo_migration_target(engine, settings)
    finally:
        await dispose_database_engine(engine)
    assert state.value == "EXACT_DEMO"


@pytest.mark.asyncio
async def test_runtime_role_can_read_demo_but_cannot_read_or_mutate_governed_state(
    demo_database: tuple[str, Settings],
) -> None:
    database_url, _settings = demo_database
    runtime_url = portfolio_demo_runtime_database_url(database_url, RUNTIME_PASSWORD)
    runtime_settings = _demo_settings(runtime_url, production=True)
    engine = create_database_engine(runtime_settings)
    try:
        await assert_portfolio_demo_runtime_access(engine)
        await verify_portfolio_demo_database(engine, runtime_settings)
        async with engine.connect() as connection:
            assert (
                await connection.execute(
                    text("SELECT count(*) FROM portfolio_demo.catalog_identity")
                )
            ).scalar_one() == 1
        with pytest.raises(DBAPIError):
            async with engine.begin() as connection:
                await connection.execute(text("SELECT count(*) FROM navigator.requirements"))
        with pytest.raises(DBAPIError):
            async with engine.begin() as connection:
                await connection.execute(text("CREATE TABLE public.forbidden_demo_write (id int)"))
        with pytest.raises(DBAPIError):
            async with engine.begin() as connection:
                await connection.execute(
                    text("UPDATE portfolio_demo.catalog_identity SET dataset_revision = 2")
                )
    finally:
        await dispose_database_engine(engine)


@pytest.mark.asyncio
async def test_runtime_password_rotation_never_embeds_secret_in_sql_or_public_error() -> None:
    password = "portfolio_demo_runtime_password_never_log_this"

    class FailingConnection:
        def __init__(self) -> None:
            self.statements: list[str] = []

        async def execute(self, statement: object, parameters: object = None) -> object:
            self.statements.append(str(statement))
            if len(self.statements) == 2:
                raise RuntimeError(f"simulated driver failure containing {password}")
            return object()

    fake_connection = FailingConnection()
    with pytest.raises(
        PortfolioDemoDatabaseError,
        match="credential rotation failed",
    ) as error:
        await _rotate_portfolio_demo_runtime_password(
            cast(AsyncConnection, fake_connection),
            password,
        )

    assert error.value.__suppress_context__ is True
    assert password not in str(error.value)
    assert all(password not in statement for statement in fake_connection.statements)


def test_production_demo_api_runs_real_guided_flow_without_ai_key(
    demo_database: tuple[str, Settings],
) -> None:
    database_url, _settings = demo_database
    runtime_url = portfolio_demo_runtime_database_url(database_url, RUNTIME_PASSWORD)
    settings = _demo_settings(runtime_url, production=True)
    app = create_app(settings)

    with TestClient(app) as client:
        activities = client.get("/api/v1/activities", headers={"Host": "testserver"})
        questionnaire = client.post(
            "/api/v1/questionnaire",
            headers={"Host": "testserver"},
            json={"activity_code": "restaurant"},
        )
        checklist = client.post(
            "/api/v1/checklist",
            headers={"Host": "testserver"},
            json={
                "activity_code": "restaurant",
                "facts": {
                    "has_employees": True,
                    "has_food_establishment_workers": True,
                    "offers_home_delivery": False,
                    "uses_public_sidewalk_for_customer_service": None,
                    "zatca_confirmed_mandatory_vat_registration_applies": False,
                },
                "navigation_facts": {
                    "ownership_investor_route": "saudi_person_or_saudi_owned_entity",
                    "planned_legal_form": "limited_liability_company",
                    "has_selected_business_premises": True,
                },
            },
        )
        ai = client.post(
            "/api/v1/navigator",
            headers={"Host": "testserver"},
            json={"text": "I want to open a restaurant"},
        )

    assert activities.status_code == 200
    assert activities.json()["metadata"] == {
        "catalog_mode": "PORTFOLIO_DEMO_CATALOG",
        "publication_state": "SAMPLE_ONLY",
        "data_classification": "SYNTHETIC_PORTFOLIO_DEMO",
        "public_catalog_approved": False,
        "warning_ar": load_portfolio_demo_spec().warning_ar,
        "warning_en": load_portfolio_demo_spec().warning_en,
    }
    assert len(activities.json()["activities"]) == 3
    assert questionnaire.status_code == 200
    assert len(questionnaire.json()["questionnaire"]["questions"]) == 8
    assert checklist.status_code == 200
    result = checklist.json()["result"]
    assert len(result["applies"]) == 3
    assert len(result["does_not_apply"]) == 2
    assert len(result["needs_information"]) == 1
    assert len(result["journey_guidance"]) == 6
    assert result["regulatory_snapshot"]["catalog_mode"] == "PORTFOLIO_DEMO"
    assert result["regulatory_snapshot"]["publication_count"] == 0
    assert ai.status_code == 503
    assert ai.json()["error"]["code"] == "AI_UNAVAILABLE"


def test_seed_rejects_a_database_with_any_governed_row() -> None:
    name, database_url = _create_database()
    try:
        _upgrade(database_url)

        async def exercise_rejection() -> None:
            settings = _demo_settings(database_url)
            engine = create_database_engine(settings)
            try:
                async with engine.begin() as connection:
                    await connection.execute(
                        text(
                            "INSERT INTO navigator.business_activities "
                            "(id, code, name_ar, name_en, is_active) "
                            "VALUES (:id, 'synthetic_blocker', 'اختبار', 'Test', false)"
                        ),
                        {"id": uuid.uuid4()},
                    )
                with pytest.raises(PortfolioDemoDatabaseError, match="governed rows"):
                    await seed_portfolio_demo_database(engine, settings)
            finally:
                await dispose_database_engine(engine)

        asyncio.run(exercise_rejection())
    finally:
        _drop_database(name)


def test_pre_migration_guard_rejects_ambiguous_schema_without_mutating_it() -> None:
    name, database_url = _create_database()
    settings = _demo_settings(database_url)

    async def exercise_rejection() -> None:
        engine = create_database_engine(settings)
        try:
            async with engine.begin() as connection:
                await connection.execute(text("CREATE SCHEMA navigator"))
            with pytest.raises(PortfolioDemoDatabaseError, match="not an approved"):
                await assert_portfolio_demo_migration_target(engine, settings)
            async with engine.connect() as connection:
                schemas = set(
                    (
                        await connection.execute(
                            text(
                                "SELECT nspname FROM pg_catalog.pg_namespace "
                                "WHERE nspname IN ('navigator', 'portfolio_demo')"
                            )
                        )
                    ).scalars()
                )
                migration_table = (
                    await connection.execute(
                        text("SELECT to_regclass('navigator.alembic_version')")
                    )
                ).scalar_one()
            assert schemas == {"navigator"}
            assert migration_table is None
        finally:
            await dispose_database_engine(engine)

    try:
        asyncio.run(exercise_rejection())
    finally:
        _drop_database(name)


def test_verifier_rejects_an_unexpected_user_relation() -> None:
    name, database_url = _create_database()
    try:
        _upgrade(database_url)

        async def exercise_rejection() -> None:
            settings = _demo_settings(database_url)
            engine = create_database_engine(settings)
            try:
                await seed_portfolio_demo_database(engine, settings)
                await provision_portfolio_demo_runtime_role(engine, settings, RUNTIME_PASSWORD)
                async with engine.begin() as connection:
                    await connection.execute(
                        text("CREATE TABLE portfolio_demo.unexpected_private_copy (value text)")
                    )
                with pytest.raises(PortfolioDemoDatabaseError, match="table inventory"):
                    await verify_portfolio_demo_database(engine, settings)
            finally:
                await dispose_database_engine(engine)

        asyncio.run(exercise_rejection())
    finally:
        _drop_database(name)


@pytest.mark.parametrize(
    "unexpected_object_sql",
    (
        "CREATE SEQUENCE public.unexpected_demo_sequence",
        (
            "CREATE FUNCTION public.unexpected_demo_function() RETURNS integer "
            "LANGUAGE sql AS 'SELECT 1'"
        ),
    ),
)
def test_pre_migration_guard_rejects_other_user_objects_without_mutating_target(
    unexpected_object_sql: str,
) -> None:
    name, database_url = _create_database()
    settings = _demo_settings(database_url)

    async def exercise_rejection() -> None:
        engine = create_database_engine(settings)
        try:
            async with engine.begin() as connection:
                await connection.execute(text(unexpected_object_sql))
            with pytest.raises(PortfolioDemoDatabaseError, match="not an approved"):
                await assert_portfolio_demo_migration_target(engine, settings)
            async with engine.connect() as connection:
                migration_table = (
                    await connection.execute(
                        text("SELECT to_regclass('navigator.alembic_version')")
                    )
                ).scalar_one()
            assert migration_table is None
        finally:
            await dispose_database_engine(engine)

    try:
        asyncio.run(exercise_rejection())
    finally:
        _drop_database(name)


def test_initializer_lock_rejects_a_concurrent_initializer() -> None:
    name, database_url = _create_database()
    settings = _demo_settings(database_url)

    async def exercise_lock() -> None:
        first_engine = create_database_engine(settings)
        second_engine = create_database_engine(settings)
        try:
            async with _initialization_lock(first_engine):
                with pytest.raises(RuntimeError, match="initializer is already running"):
                    async with _initialization_lock(second_engine):
                        raise AssertionError(
                            "concurrent initializer unexpectedly acquired the lock"
                        )
        finally:
            await dispose_database_engine(second_engine)
            await dispose_database_engine(first_engine)

    try:
        asyncio.run(exercise_lock())
    finally:
        _drop_database(name)


def test_initializer_classifies_migrates_reclassifies_and_seeds_a_pristine_database() -> None:
    name, database_url = _create_database()
    settings = _demo_settings(database_url)
    try:
        with (
            _migration_url(database_url),
            patch(
                "saudi_business_launch_navigator.portfolio_demo.initialize.get_settings",
                return_value=settings,
            ),
            patch.dict(
                os.environ,
                {"SBLN_DEMO_RUNTIME_DATABASE_PASSWORD": RUNTIME_PASSWORD},
            ),
        ):
            pre_migration, post_migration, result = asyncio.run(_initialize())

        assert pre_migration == "PRISTINE"
        assert post_migration == "MIGRATED_EMPTY"
        assert result.migration_revision == DEMO_MIGRATION_REVISION
        assert result.database_identity == load_portfolio_demo_spec().database_identity
    finally:
        _drop_database(name)


@pytest.mark.parametrize(
    "replacement_sql",
    (
        (
            "CREATE OR REPLACE FUNCTION "
            "portfolio_demo.reject_catalog_mutation() RETURNS trigger "
            "LANGUAGE plpgsql AS $$ BEGIN RETURN OLD; END; $$"
        ),
        (
            "CREATE OR REPLACE FUNCTION "
            "portfolio_demo.governed_catalog_is_empty() RETURNS boolean "
            "LANGUAGE sql SECURITY DEFINER AS $$ SELECT false $$"
        ),
    ),
)
def test_verifier_rejects_replaced_demo_security_function_before_execution(
    replacement_sql: str,
) -> None:
    name, database_url = _create_database()
    try:
        _upgrade(database_url)

        async def exercise_rejection() -> None:
            settings = _demo_settings(database_url)
            engine = create_database_engine(settings)
            try:
                await seed_portfolio_demo_database(engine, settings)
                async with engine.begin() as connection:
                    await connection.execute(text(replacement_sql))
                with pytest.raises(PortfolioDemoDatabaseError, match="function inventory"):
                    await verify_portfolio_demo_database(engine, settings)
            finally:
                await dispose_database_engine(engine)

        asyncio.run(exercise_rejection())
    finally:
        _drop_database(name)


@pytest.mark.parametrize(
    ("mutation_sql", "expected_error"),
    (
        (
            "ALTER TABLE portfolio_demo.catalog_identity ADD COLUMN private_copy text",
            "column inventory",
        ),
        (
            "ALTER TABLE portfolio_demo.catalog_identity "
            "DROP CONSTRAINT catalog_identity_dataset_code_check",
            "constraint inventory",
        ),
        (
            "DROP TRIGGER catalog_identity_reject_row_mutation "
            "ON portfolio_demo.catalog_identity; "
            "CREATE TRIGGER catalog_identity_reject_row_mutation "
            "BEFORE UPDATE OR DELETE ON portfolio_demo.catalog_identity "
            "FOR EACH ROW WHEN (false) "
            "EXECUTE FUNCTION portfolio_demo.reject_catalog_mutation()",
            "immutability controls",
        ),
    ),
)
def test_verifier_rejects_altered_demo_table_structure(
    mutation_sql: str,
    expected_error: str,
) -> None:
    name, database_url = _create_database()
    try:
        _upgrade(database_url)

        async def exercise_rejection() -> None:
            settings = _demo_settings(database_url)
            engine = create_database_engine(settings)
            try:
                await seed_portfolio_demo_database(engine, settings)
                async with engine.begin() as connection:
                    await connection.exec_driver_sql(mutation_sql)
                with pytest.raises(PortfolioDemoDatabaseError, match=expected_error):
                    await verify_portfolio_demo_database(engine, settings)
            finally:
                await dispose_database_engine(engine)

        asyncio.run(exercise_rejection())
    finally:
        _drop_database(name)


def test_runtime_role_is_normalized_and_detects_later_governed_contamination() -> None:
    name, database_url = _create_database()
    inherited_role = f"navigator_demo_inherited_{uuid.uuid4().hex[:12]}"
    try:
        _upgrade(database_url)

        async def exercise_runtime_boundary() -> None:
            settings = _demo_settings(database_url)
            engine = create_database_engine(settings)
            try:
                await seed_portfolio_demo_database(engine, settings)
                await provision_portfolio_demo_runtime_role(engine, settings, RUNTIME_PASSWORD)
                async with engine.begin() as connection:
                    await connection.exec_driver_sql(f"CREATE ROLE {inherited_role} NOLOGIN")
                    await connection.execute(text("ALTER ROLE navigator_demo_runtime INHERIT"))
                    await connection.exec_driver_sql(
                        f"GRANT {inherited_role} TO navigator_demo_runtime"
                    )
                    assert settings.expected_database_name is not None
                    quoted_database = '"' + settings.expected_database_name + '"'
                    await connection.exec_driver_sql(
                        f"GRANT CREATE, TEMPORARY ON DATABASE {quoted_database} "
                        "TO navigator_demo_runtime"
                    )
                    await connection.execute(
                        text(
                            "GRANT SELECT ON navigator.published_requirement_versions "
                            "TO navigator_demo_runtime"
                        )
                    )
                await provision_portfolio_demo_runtime_role(engine, settings, RUNTIME_PASSWORD)
                async with engine.begin() as connection:
                    role_state = (
                        await connection.execute(
                            text(
                                "SELECT rolsuper, rolinherit, rolcreaterole, rolcreatedb, "
                                "rolreplication, rolbypassrls, "
                                "(SELECT count(*) FROM pg_catalog.pg_auth_members membership "
                                "WHERE membership.member = role.oid) "
                                "FROM pg_catalog.pg_roles role "
                                "WHERE role.rolname = 'navigator_demo_runtime'"
                            )
                        )
                    ).one()
                    normalized_privileges = (
                        await connection.execute(
                            text(
                                "SELECT "
                                "has_database_privilege('navigator_demo_runtime', "
                                "current_database(), 'CREATE'), "
                                "has_database_privilege('navigator_demo_runtime', "
                                "current_database(), 'TEMP'), "
                                "has_table_privilege('navigator_demo_runtime', "
                                "'navigator.published_requirement_versions', 'SELECT')"
                            )
                        )
                    ).one()
                    await connection.execute(
                        text(
                            "INSERT INTO navigator.business_activities "
                            "(id, code, name_ar, name_en, is_active) "
                            "VALUES (:id, 'synthetic_runtime_blocker', 'اختبار', 'Test', false)"
                        ),
                        {"id": uuid.uuid4()},
                    )
                assert tuple(role_state) == (False, False, False, False, False, False, 0)
                assert tuple(normalized_privileges) == (False, False, False)
            finally:
                await dispose_database_engine(engine)

            runtime_url = portfolio_demo_runtime_database_url(database_url, RUNTIME_PASSWORD)
            runtime_settings = _demo_settings(runtime_url, production=True)
            runtime_engine = create_database_engine(runtime_settings)
            try:
                with pytest.raises(PortfolioDemoDatabaseError, match="governed rows"):
                    await verify_portfolio_demo_database(runtime_engine, runtime_settings)
            finally:
                await dispose_database_engine(runtime_engine)

        asyncio.run(exercise_runtime_boundary())
    finally:
        base = make_url(Settings(_env_file=None).database_url.get_secret_value())
        with _connect(base, "postgres") as admin:
            admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(inherited_role)))
        _drop_database(name)


def test_runtime_role_with_elevated_attributes_fails_closed() -> None:
    name, database_url = _create_database()
    try:
        _upgrade(database_url)

        async def exercise_elevated_role_rejection() -> None:
            settings = _demo_settings(database_url)
            engine = create_database_engine(settings)
            try:
                await seed_portfolio_demo_database(engine, settings)
                await provision_portfolio_demo_runtime_role(engine, settings, RUNTIME_PASSWORD)
                async with engine.begin() as connection:
                    await connection.execute(text("ALTER ROLE navigator_demo_runtime CREATEROLE"))
                with pytest.raises(
                    PortfolioDemoDatabaseError,
                    match="runtime role has unexpected elevated privileges",
                ):
                    await provision_portfolio_demo_runtime_role(
                        engine,
                        settings,
                        RUNTIME_PASSWORD,
                    )
                async with engine.connect() as connection:
                    remains_elevated = (
                        await connection.execute(
                            text(
                                "SELECT rolcreaterole FROM pg_catalog.pg_roles "
                                "WHERE rolname = 'navigator_demo_runtime'"
                            )
                        )
                    ).scalar_one()
                assert remains_elevated is True
            finally:
                async with engine.begin() as connection:
                    await connection.execute(
                        text("ALTER ROLE navigator_demo_runtime NOCREATEROLE NOINHERIT")
                    )
                await dispose_database_engine(engine)

        asyncio.run(exercise_elevated_role_rejection())
    finally:
        _drop_database(name)


def test_runtime_boundary_rejects_an_unapproved_view_grant(
    demo_database: tuple[str, Settings],
) -> None:
    database_url, settings = demo_database

    async def exercise_view_grant() -> None:
        owner_engine = create_database_engine(settings)
        runtime_url = portfolio_demo_runtime_database_url(database_url, RUNTIME_PASSWORD)
        runtime_engine = create_database_engine(_demo_settings(runtime_url, production=True))
        try:
            async with owner_engine.begin() as connection:
                await connection.execute(
                    text(
                        "GRANT SELECT ON navigator.published_requirement_versions "
                        "TO navigator_demo_runtime"
                    )
                )
            with pytest.raises(PortfolioDemoDatabaseError, match="privileges differ"):
                await assert_portfolio_demo_runtime_access(runtime_engine)
        finally:
            async with owner_engine.begin() as connection:
                await connection.execute(
                    text(
                        "REVOKE SELECT ON navigator.published_requirement_versions "
                        "FROM navigator_demo_runtime"
                    )
                )
            await dispose_database_engine(runtime_engine)
            await dispose_database_engine(owner_engine)

    asyncio.run(exercise_view_grant())
