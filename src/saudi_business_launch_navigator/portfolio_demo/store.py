"""Fail-closed PostgreSQL identity and graph boundary for the portfolio demo."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession

from saudi_business_launch_navigator.core.config import CatalogDataMode, Settings
from saudi_business_launch_navigator.portfolio_demo.catalog import (
    DEMO_MIGRATION_REVISION,
    PortfolioDemoSpec,
    dataset_fingerprint,
    graph_sha256,
    load_portfolio_demo_spec,
)

PORTFOLIO_DEMO_SCHEMA = "portfolio_demo"
PORTFOLIO_DEMO_RUNTIME_ROLE = "navigator_demo_runtime"
NAVIGATOR_APPLICATION_TABLES = (
    "requirement_actionability_releases",
    "journey_topic_releases",
    "journey_topic_destinations",
    "journey_topic_fact_links",
    "journey_topic_requirement_links",
    "journey_topic_evidence",
    "requirement_actionability_versions",
    "journey_topic_versions",
    "journey_topics",
    "requirement_publication_sources",
    "requirement_publications",
    "requirement_condition_facts",
    "requirement_condition_sets",
    "fact_definitions",
    "research_event_evidence",
    "review_events",
    "research_events",
    "requirement_sources",
    "requirement_activities",
    "requirement_versions",
    "requirements",
    "source_versions",
    "sources",
    "domains",
    "platforms",
    "government_entities",
    "business_activities",
    "supported_locations",
)
_EXPECTED_USER_SCHEMAS = {"navigator", "portfolio_demo", "public"}
_EXPECTED_USER_TABLES = {
    *(f"navigator.{table_name}" for table_name in NAVIGATOR_APPLICATION_TABLES),
    "navigator.alembic_version",
    "portfolio_demo.catalog_graph",
    "portfolio_demo.catalog_identity",
}
_EXPECTED_USER_VIEWS = {
    "navigator.published_requirement_versions",
    "navigator.released_journey_topic_versions",
    "navigator.released_requirement_actionability_versions",
}
_EXPECTED_DEMO_COLUMNS = {
    ("catalog_graph", 1, "singleton_key", "smallint", True, "", "", ""),
    ("catalog_graph", 2, "graph", "jsonb", True, "", "", ""),
    ("catalog_graph", 3, "graph_sha256", "text", True, "", "", ""),
    (
        "catalog_graph",
        4,
        "seeded_at",
        "timestamp with time zone",
        True,
        "clock_timestamp()",
        "",
        "",
    ),
    ("catalog_identity", 1, "singleton_key", "smallint", True, "", "", ""),
    ("catalog_identity", 2, "database_identity", "uuid", True, "", "", ""),
    ("catalog_identity", 3, "catalog_kind", "text", True, "", "", ""),
    ("catalog_identity", 4, "database_purpose", "text", True, "", "", ""),
    ("catalog_identity", 5, "dataset_code", "text", True, "", "", ""),
    ("catalog_identity", 6, "dataset_revision", "integer", True, "", "", ""),
    (
        "catalog_identity",
        7,
        "dataset_fingerprint_sha256",
        "text",
        True,
        "",
        "",
        "",
    ),
    ("catalog_identity", 8, "identity_format_version", "integer", True, "", "", ""),
    (
        "catalog_identity",
        9,
        "initialized_at",
        "timestamp with time zone",
        True,
        "clock_timestamp()",
        "",
        "",
    ),
}
_EXPECTED_DEMO_CONSTRAINTS = {
    (
        "catalog_graph",
        "catalog_graph_graph_check",
        "c",
        "CHECK (jsonb_typeof(graph) = 'object'::text)",
    ),
    ("catalog_graph", "catalog_graph_graph_not_null", "n", "NOT NULL graph"),
    (
        "catalog_graph",
        "catalog_graph_graph_sha256_check",
        "c",
        "CHECK (graph_sha256 ~ '^[0-9a-f]{64}$'::text)",
    ),
    ("catalog_graph", "catalog_graph_graph_sha256_not_null", "n", "NOT NULL graph_sha256"),
    ("catalog_graph", "catalog_graph_pkey", "p", "PRIMARY KEY (singleton_key)"),
    ("catalog_graph", "catalog_graph_seeded_at_not_null", "n", "NOT NULL seeded_at"),
    (
        "catalog_graph",
        "catalog_graph_singleton_key_fkey",
        "f",
        "FOREIGN KEY (singleton_key) REFERENCES "
        "portfolio_demo.catalog_identity(singleton_key) ON DELETE RESTRICT",
    ),
    ("catalog_graph", "catalog_graph_singleton_key_not_null", "n", "NOT NULL singleton_key"),
    (
        "catalog_identity",
        "catalog_identity_catalog_kind_check",
        "c",
        "CHECK (catalog_kind = 'PORTFOLIO_DEMO_CATALOG'::text)",
    ),
    (
        "catalog_identity",
        "catalog_identity_catalog_kind_not_null",
        "n",
        "NOT NULL catalog_kind",
    ),
    (
        "catalog_identity",
        "catalog_identity_database_identity_key",
        "u",
        "UNIQUE (database_identity)",
    ),
    (
        "catalog_identity",
        "catalog_identity_database_identity_not_null",
        "n",
        "NOT NULL database_identity",
    ),
    (
        "catalog_identity",
        "catalog_identity_database_purpose_check",
        "c",
        "CHECK (database_purpose = 'PORTFOLIO_DEMO'::text)",
    ),
    (
        "catalog_identity",
        "catalog_identity_database_purpose_not_null",
        "n",
        "NOT NULL database_purpose",
    ),
    (
        "catalog_identity",
        "catalog_identity_dataset_code_check",
        "c",
        "CHECK (dataset_code ~ '^[a-z][a-z0-9_]*$'::text)",
    ),
    (
        "catalog_identity",
        "catalog_identity_dataset_code_not_null",
        "n",
        "NOT NULL dataset_code",
    ),
    (
        "catalog_identity",
        "catalog_identity_dataset_fingerprint_sha256_check",
        "c",
        "CHECK (dataset_fingerprint_sha256 ~ '^[0-9a-f]{64}$'::text)",
    ),
    (
        "catalog_identity",
        "catalog_identity_dataset_fingerprint_sha256_not_null",
        "n",
        "NOT NULL dataset_fingerprint_sha256",
    ),
    (
        "catalog_identity",
        "catalog_identity_dataset_revision_check",
        "c",
        "CHECK (dataset_revision > 0)",
    ),
    (
        "catalog_identity",
        "catalog_identity_dataset_revision_not_null",
        "n",
        "NOT NULL dataset_revision",
    ),
    (
        "catalog_identity",
        "catalog_identity_identity_format_version_check",
        "c",
        "CHECK (identity_format_version = 1)",
    ),
    (
        "catalog_identity",
        "catalog_identity_identity_format_version_not_null",
        "n",
        "NOT NULL identity_format_version",
    ),
    (
        "catalog_identity",
        "catalog_identity_initialized_at_not_null",
        "n",
        "NOT NULL initialized_at",
    ),
    ("catalog_identity", "catalog_identity_pkey", "p", "PRIMARY KEY (singleton_key)"),
    (
        "catalog_identity",
        "catalog_identity_singleton_key_check",
        "c",
        "CHECK (singleton_key = 1)",
    ),
    (
        "catalog_identity",
        "catalog_identity_singleton_key_not_null",
        "n",
        "NOT NULL singleton_key",
    ),
}
_EXPECTED_DEMO_INDEXES = {
    (
        "catalog_graph",
        "catalog_graph_pkey",
        "CREATE UNIQUE INDEX catalog_graph_pkey ON "
        "portfolio_demo.catalog_graph USING btree (singleton_key)",
    ),
    (
        "catalog_identity",
        "catalog_identity_database_identity_key",
        "CREATE UNIQUE INDEX catalog_identity_database_identity_key ON "
        "portfolio_demo.catalog_identity USING btree (database_identity)",
    ),
    (
        "catalog_identity",
        "catalog_identity_pkey",
        "CREATE UNIQUE INDEX catalog_identity_pkey ON "
        "portfolio_demo.catalog_identity USING btree (singleton_key)",
    ),
}
_EXPECTED_DEMO_TRIGGERS = {
    (
        "catalog_graph",
        "catalog_graph_reject_row_mutation",
        27,
        "O",
        "CREATE TRIGGER catalog_graph_reject_row_mutation BEFORE DELETE OR UPDATE ON "
        "portfolio_demo.catalog_graph FOR EACH ROW EXECUTE FUNCTION "
        "portfolio_demo.reject_catalog_mutation()",
    ),
    (
        "catalog_graph",
        "catalog_graph_reject_truncate",
        34,
        "O",
        "CREATE TRIGGER catalog_graph_reject_truncate BEFORE TRUNCATE ON "
        "portfolio_demo.catalog_graph FOR EACH STATEMENT EXECUTE FUNCTION "
        "portfolio_demo.reject_catalog_mutation()",
    ),
    (
        "catalog_identity",
        "catalog_identity_reject_row_mutation",
        27,
        "O",
        "CREATE TRIGGER catalog_identity_reject_row_mutation BEFORE DELETE OR UPDATE ON "
        "portfolio_demo.catalog_identity FOR EACH ROW EXECUTE FUNCTION "
        "portfolio_demo.reject_catalog_mutation()",
    ),
    (
        "catalog_identity",
        "catalog_identity_reject_truncate",
        34,
        "O",
        "CREATE TRIGGER catalog_identity_reject_truncate BEFORE TRUNCATE ON "
        "portfolio_demo.catalog_identity FOR EACH STATEMENT EXECUTE FUNCTION "
        "portfolio_demo.reject_catalog_mutation()",
    ),
}
_RUNTIME_PASSWORD_SETTING = "sbln.demo_runtime_password"
_RUNTIME_PASSWORD_ROTATION_SQL = f"""
DO $password_rotation$
DECLARE
    runtime_password text := pg_catalog.current_setting('{_RUNTIME_PASSWORD_SETTING}', true);
BEGIN
    IF runtime_password IS NULL OR pg_catalog.length(runtime_password) < 24 THEN
        RAISE EXCEPTION 'portfolio demo runtime credential is unavailable';
    END IF;
    EXECUTE pg_catalog.format(
        'ALTER ROLE navigator_demo_runtime PASSWORD %L',
        runtime_password
    );
    PERFORM pg_catalog.set_config('{_RUNTIME_PASSWORD_SETTING}', '', true);
END;
$password_rotation$
"""

_REJECT_CATALOG_MUTATION_BODY = """
BEGIN
    RAISE EXCEPTION 'portfolio demo catalog is immutable';
END;
"""
_GOVERNED_CATALOG_EMPTY_BODY = (
    "\n    SELECT ("
    + " + ".join(
        f'(SELECT count(*) FROM navigator."{table_name}")'
        for table_name in NAVIGATOR_APPLICATION_TABLES
    )
    + ") = 0\n"
)

_IDENTITY_DDL = (
    "CREATE SCHEMA portfolio_demo",
    """CREATE TABLE portfolio_demo.catalog_identity (
    singleton_key smallint PRIMARY KEY CHECK (singleton_key = 1),
    database_identity uuid NOT NULL UNIQUE,
    catalog_kind text NOT NULL CHECK (catalog_kind = 'PORTFOLIO_DEMO_CATALOG'),
    database_purpose text NOT NULL CHECK (database_purpose = 'PORTFOLIO_DEMO'),
    dataset_code text NOT NULL CHECK (dataset_code ~ '^[a-z][a-z0-9_]*$'),
    dataset_revision integer NOT NULL CHECK (dataset_revision > 0),
    dataset_fingerprint_sha256 text NOT NULL
        CHECK (dataset_fingerprint_sha256 ~ '^[0-9a-f]{64}$'),
    identity_format_version integer NOT NULL CHECK (identity_format_version = 1),
    initialized_at timestamptz NOT NULL DEFAULT clock_timestamp()
)""",
    """CREATE TABLE portfolio_demo.catalog_graph (
    singleton_key smallint PRIMARY KEY
        REFERENCES portfolio_demo.catalog_identity(singleton_key) ON DELETE RESTRICT,
    graph jsonb NOT NULL CHECK (jsonb_typeof(graph) = 'object'),
    graph_sha256 text NOT NULL CHECK (graph_sha256 ~ '^[0-9a-f]{64}$'),
    seeded_at timestamptz NOT NULL DEFAULT clock_timestamp()
)""",
    f"""CREATE FUNCTION portfolio_demo.reject_catalog_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $function${_REJECT_CATALOG_MUTATION_BODY}$function$""",
    f"""CREATE FUNCTION portfolio_demo.governed_catalog_is_empty()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog
AS $function${_GOVERNED_CATALOG_EMPTY_BODY}$function$""",
    "REVOKE ALL ON FUNCTION portfolio_demo.reject_catalog_mutation() FROM PUBLIC",
    "REVOKE ALL ON FUNCTION portfolio_demo.governed_catalog_is_empty() FROM PUBLIC",
    """CREATE TRIGGER catalog_identity_reject_row_mutation
BEFORE UPDATE OR DELETE ON portfolio_demo.catalog_identity
FOR EACH ROW EXECUTE FUNCTION portfolio_demo.reject_catalog_mutation()""",
    """CREATE TRIGGER catalog_identity_reject_truncate
BEFORE TRUNCATE ON portfolio_demo.catalog_identity
FOR EACH STATEMENT EXECUTE FUNCTION portfolio_demo.reject_catalog_mutation()""",
    """CREATE TRIGGER catalog_graph_reject_row_mutation
BEFORE UPDATE OR DELETE ON portfolio_demo.catalog_graph
FOR EACH ROW EXECUTE FUNCTION portfolio_demo.reject_catalog_mutation()""",
    """CREATE TRIGGER catalog_graph_reject_truncate
BEFORE TRUNCATE ON portfolio_demo.catalog_graph
FOR EACH STATEMENT EXECUTE FUNCTION portfolio_demo.reject_catalog_mutation()""",
)


class PortfolioDemoDatabaseError(RuntimeError):
    """Raised without leaking connection strings, SQL, or private catalog details."""


class DemoMigrationTargetState(StrEnum):
    PRISTINE = "PRISTINE"
    MIGRATED_EMPTY = "MIGRATED_EMPTY"
    EXACT_DEMO = "EXACT_DEMO"


@dataclass(frozen=True)
class VerifiedPortfolioDemoDatabase:
    database_identity: UUID
    dataset_code: str
    dataset_revision: int
    dataset_fingerprint_sha256: str
    graph_sha256: str
    migration_revision: str
    database_timestamp: datetime


async def verify_portfolio_demo_database(
    engine: AsyncEngine,
    settings: Settings,
) -> VerifiedPortfolioDemoDatabase:
    """Verify the exact demo marker, graph, migration, and empty governed schema."""

    async with AsyncSession(engine, expire_on_commit=False) as session, session.begin():
        await session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        _spec, verified = await read_verified_demo_spec(session, settings)
        return verified


async def assert_portfolio_demo_migration_target(
    engine: AsyncEngine,
    settings: Settings,
) -> DemoMigrationTargetState:
    """Classify the target without DDL before Alembic is allowed to run."""

    _assert_demo_configuration(settings)
    async with AsyncSession(engine, expire_on_commit=False) as session, session.begin():
        await session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        database_name = (await session.execute(text("SELECT current_database()"))).scalar_one()
        if database_name != settings.expected_database_name:
            raise PortfolioDemoDatabaseError("portfolio demo database name differs")
        schemas = await _user_schemas(session)
        tables = await _user_relations(session, relation_kind="tables")
        views = await _user_relations(session, relation_kind="views")
        other_relations = await _user_relations(session, relation_kind="other")
        public_routines = await _schema_routine_count(session, "public")
        public_types = await _schema_standalone_type_count(session, "public")

        if (
            schemas == {"public"}
            and not tables
            and not views
            and not other_relations
            and public_routines == 0
            and public_types == 0
        ):
            return DemoMigrationTargetState.PRISTINE
        if "portfolio_demo" in schemas:
            await _read_verified_demo_spec_in_transaction(session, settings)
            return DemoMigrationTargetState.EXACT_DEMO
        expected_migrated_schemas = {"navigator", "public"}
        expected_migrated_tables = {
            *(f"navigator.{table_name}" for table_name in NAVIGATOR_APPLICATION_TABLES),
            "navigator.alembic_version",
        }
        if (
            schemas == expected_migrated_schemas
            and tables == expected_migrated_tables
            and views == _EXPECTED_USER_VIEWS
            and not other_relations
            and public_routines == 0
            and public_types == 0
        ):
            migration = (
                await session.execute(text("SELECT version_num FROM navigator.alembic_version"))
            ).scalar_one()
            if migration == DEMO_MIGRATION_REVISION and await _navigator_row_count(session) == 0:
                return DemoMigrationTargetState.MIGRATED_EMPTY
    raise PortfolioDemoDatabaseError("database is not an approved portfolio demo migration target")


async def read_verified_demo_spec(
    session: AsyncSession,
    settings: Settings,
) -> tuple[PortfolioDemoSpec, VerifiedPortfolioDemoDatabase]:
    """Read and verify the catalog in the caller's existing read-only transaction."""

    return await _read_verified_demo_spec_in_transaction(session, settings)


async def _read_verified_demo_spec_in_transaction(
    session: AsyncSession,
    settings: Settings,
) -> tuple[PortfolioDemoSpec, VerifiedPortfolioDemoDatabase]:
    _assert_demo_configuration(settings)
    expected_spec = load_portfolio_demo_spec()

    try:
        database_name = (await session.execute(text("SELECT current_database()"))).scalar_one()
        if database_name != settings.expected_database_name:
            raise PortfolioDemoDatabaseError("portfolio demo database name differs")
        migration_revision = (
            await session.execute(text("SELECT version_num FROM navigator.alembic_version"))
        ).scalar_one()
        if migration_revision != DEMO_MIGRATION_REVISION:
            raise PortfolioDemoDatabaseError("portfolio demo migration revision differs")
        await _assert_exact_relation_inventory(session)
        await _assert_governed_rows_inaccessible_or_empty(session)

        identity = (
            await session.execute(
                text(
                    "SELECT database_identity, catalog_kind, database_purpose, dataset_code, "
                    "dataset_revision, dataset_fingerprint_sha256, identity_format_version "
                    "FROM portfolio_demo.catalog_identity WHERE singleton_key = 1"
                )
            )
        ).one()
        identity_count = (
            await session.execute(text("SELECT count(*) FROM portfolio_demo.catalog_identity"))
        ).scalar_one()
        graph_row = (
            await session.execute(
                text(
                    "SELECT graph, graph_sha256 FROM portfolio_demo.catalog_graph "
                    "WHERE singleton_key = 1"
                )
            )
        ).one()
        graph_count = (
            await session.execute(text("SELECT count(*) FROM portfolio_demo.catalog_graph"))
        ).scalar_one()
        database_timestamp = (await session.execute(text("SELECT current_timestamp"))).scalar_one()
    except PortfolioDemoDatabaseError:
        raise
    except Exception as exc:
        raise PortfolioDemoDatabaseError("portfolio demo database identity is unavailable") from exc

    if identity_count != 1 or graph_count != 1:
        raise PortfolioDemoDatabaseError("portfolio demo singleton state differs")
    if (
        identity.database_identity != expected_spec.database_identity
        or identity.catalog_kind != expected_spec.classification
        or identity.database_purpose != "PORTFOLIO_DEMO"
        or identity.dataset_code != expected_spec.dataset_code
        or identity.dataset_revision != expected_spec.dataset_revision
        or identity.identity_format_version != 1
    ):
        raise PortfolioDemoDatabaseError("portfolio demo identity fields differ")

    try:
        stored_spec = PortfolioDemoSpec.model_validate(graph_row.graph)
    except Exception as exc:
        raise PortfolioDemoDatabaseError("portfolio demo graph schema is invalid") from exc
    expected_graph_hash = graph_sha256(expected_spec)
    expected_dataset_hash = dataset_fingerprint(expected_spec)
    if stored_spec != expected_spec:
        raise PortfolioDemoDatabaseError("portfolio demo graph differs from the source seed")
    if graph_row.graph_sha256 != expected_graph_hash:
        raise PortfolioDemoDatabaseError("portfolio demo graph fingerprint differs")
    if identity.dataset_fingerprint_sha256 != expected_dataset_hash:
        raise PortfolioDemoDatabaseError("portfolio demo dataset fingerprint differs")

    return stored_spec, VerifiedPortfolioDemoDatabase(
        database_identity=identity.database_identity,
        dataset_code=identity.dataset_code,
        dataset_revision=identity.dataset_revision,
        dataset_fingerprint_sha256=identity.dataset_fingerprint_sha256,
        graph_sha256=graph_row.graph_sha256,
        migration_revision=migration_revision,
        database_timestamp=database_timestamp,
    )


async def seed_portfolio_demo_database(
    engine: AsyncEngine,
    settings: Settings,
) -> VerifiedPortfolioDemoDatabase:
    """Atomically initialize only an empty 0005 database; exact replay is a no-op."""

    _assert_demo_configuration(settings)
    spec = load_portfolio_demo_spec()

    async with engine.begin() as connection:
        await connection.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
        await connection.execute(text("SET LOCAL lock_timeout = '5s'"))
        await connection.execute(text("SET LOCAL statement_timeout = '30s'"))
        await connection.execute(text("SELECT pg_advisory_xact_lock(7310462010)"))
        database_name = (await connection.execute(text("SELECT current_database()"))).scalar_one()
        if database_name != settings.expected_database_name:
            raise PortfolioDemoDatabaseError("portfolio demo database name differs")
        migration_revision = (
            await connection.execute(text("SELECT version_num FROM navigator.alembic_version"))
        ).scalar_one()
        if migration_revision != DEMO_MIGRATION_REVISION:
            raise PortfolioDemoDatabaseError("portfolio demo seed requires migration 0005")
        if await _navigator_row_count(connection) != 0:
            raise PortfolioDemoDatabaseError("refusing to seed a database with governed rows")
        schema_exists = (
            await connection.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace "
                    "WHERE nspname = 'portfolio_demo')"
                )
            )
        ).scalar_one()
        if schema_exists:
            identity_count = (
                await connection.execute(
                    text("SELECT count(*) FROM portfolio_demo.catalog_identity")
                )
            ).scalar_one()
            graph_count = (
                await connection.execute(text("SELECT count(*) FROM portfolio_demo.catalog_graph"))
            ).scalar_one()
            if identity_count != 1 or graph_count != 1:
                raise PortfolioDemoDatabaseError("existing portfolio demo seed is incomplete")
        else:
            for statement in _IDENTITY_DDL:
                await connection.execute(text(statement))
            await connection.execute(
                text(
                    "INSERT INTO portfolio_demo.catalog_identity ("
                    "singleton_key, database_identity, catalog_kind, database_purpose, "
                    "dataset_code, dataset_revision, dataset_fingerprint_sha256, "
                    "identity_format_version) VALUES (1, :identity, :kind, 'PORTFOLIO_DEMO', "
                    ":dataset_code, :revision, :fingerprint, 1)"
                ),
                {
                    "identity": spec.database_identity,
                    "kind": spec.classification,
                    "dataset_code": spec.dataset_code,
                    "revision": spec.dataset_revision,
                    "fingerprint": dataset_fingerprint(spec),
                },
            )
            await connection.execute(
                text(
                    "INSERT INTO portfolio_demo.catalog_graph "
                    "(singleton_key, graph, graph_sha256) "
                    "VALUES (1, CAST(:graph AS jsonb), :graph_sha256)"
                ),
                {
                    "graph": json.dumps(spec.model_dump(mode="json"), ensure_ascii=False),
                    "graph_sha256": graph_sha256(spec),
                },
            )
        if await _navigator_row_count(connection) != 0:
            raise PortfolioDemoDatabaseError("portfolio demo seed observed governed rows")
        await _assert_exact_relation_inventory(connection)
    return await verify_portfolio_demo_database(engine, settings)


async def provision_portfolio_demo_runtime_role(
    engine: AsyncEngine,
    settings: Settings,
    password: str,
) -> None:
    """Create or rotate the fixed SELECT-only role used by the long-running API."""

    _assert_demo_configuration(settings)
    if len(password) < 24:
        raise PortfolioDemoDatabaseError("portfolio demo runtime credential is too short")
    assert settings.expected_database_name is not None
    quoted_database = '"' + settings.expected_database_name.replace('"', '""') + '"'
    async with engine.begin() as connection:
        await connection.execute(text("SET LOCAL lock_timeout = '5s'"))
        await connection.execute(text("SET LOCAL statement_timeout = '30s'"))
        await connection.execute(
            text(
                "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles "
                "WHERE rolname = 'navigator_demo_runtime') THEN "
                "CREATE ROLE navigator_demo_runtime LOGIN; END IF; END $$"
            )
        )
        await connection.execute(
            text(
                "DO $membership$ DECLARE inherited_role text; BEGIN "
                "FOR inherited_role IN "
                "SELECT parent.rolname FROM pg_catalog.pg_auth_members membership "
                "JOIN pg_catalog.pg_roles parent ON parent.oid = membership.roleid "
                "JOIN pg_catalog.pg_roles member ON member.oid = membership.member "
                "WHERE member.rolname = 'navigator_demo_runtime' LOOP "
                "EXECUTE format('REVOKE %I FROM navigator_demo_runtime', inherited_role); "
                "END LOOP; END $membership$"
            )
        )
        await connection.exec_driver_sql(
            f"ALTER ROLE {PORTFOLIO_DEMO_RUNTIME_ROLE} WITH LOGIN NOSUPERUSER NOCREATEDB "
            "NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS"
        )
        await _rotate_portfolio_demo_runtime_password(connection, password)
        await connection.exec_driver_sql(
            f"REVOKE CONNECT, TEMPORARY ON DATABASE {quoted_database} FROM PUBLIC"
        )
        await connection.exec_driver_sql(
            f"REVOKE ALL PRIVILEGES ON DATABASE {quoted_database} "
            f"FROM {PORTFOLIO_DEMO_RUNTIME_ROLE}"
        )
        await connection.exec_driver_sql(
            f"GRANT CONNECT ON DATABASE {quoted_database} TO {PORTFOLIO_DEMO_RUNTIME_ROLE}"
        )
        await connection.execute(text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
        await connection.execute(
            text(
                "REVOKE ALL PRIVILEGES ON SCHEMA navigator, portfolio_demo "
                "FROM navigator_demo_runtime"
            )
        )
        await connection.execute(
            text(
                "REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA navigator, portfolio_demo "
                "FROM navigator_demo_runtime"
            )
        )
        await connection.execute(
            text("REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA navigator, portfolio_demo FROM PUBLIC")
        )
        await connection.execute(
            text(
                "REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA navigator, portfolio_demo "
                "FROM navigator_demo_runtime"
            )
        )
        await connection.execute(
            text("GRANT USAGE ON SCHEMA navigator, portfolio_demo TO navigator_demo_runtime")
        )
        await connection.execute(
            text(
                "GRANT SELECT ON navigator.alembic_version, "
                "portfolio_demo.catalog_identity, portfolio_demo.catalog_graph "
                "TO navigator_demo_runtime"
            )
        )
        await connection.execute(
            text(
                "GRANT EXECUTE ON FUNCTION portfolio_demo.governed_catalog_is_empty() "
                "TO navigator_demo_runtime"
            )
        )
        await connection.execute(
            text("ALTER ROLE navigator_demo_runtime SET default_transaction_read_only = on")
        )
        await connection.execute(
            text("ALTER ROLE navigator_demo_runtime SET statement_timeout = '10s'")
        )
        await connection.execute(text("ALTER ROLE navigator_demo_runtime SET lock_timeout = '2s'"))


async def assert_portfolio_demo_runtime_access(engine: AsyncEngine) -> None:
    """Prove the connected API principal has only the approved demo read surface."""

    async with AsyncSession(engine, expire_on_commit=False) as session, session.begin():
        await session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        current_user = (await session.execute(text("SELECT current_user"))).scalar_one()
        if current_user != PORTFOLIO_DEMO_RUNTIME_ROLE:
            raise PortfolioDemoDatabaseError("portfolio demo API is not using the runtime role")
        setting = (await session.execute(text("SHOW default_transaction_read_only"))).scalar_one()
        if setting != "on":
            raise PortfolioDemoDatabaseError("portfolio demo runtime is not read-only by default")
        role_is_restricted = (
            await session.execute(
                text(
                    "SELECT rolcanlogin AND NOT rolsuper AND NOT rolinherit "
                    "AND NOT rolcreaterole AND NOT rolcreatedb AND NOT rolreplication "
                    "AND NOT rolbypassrls "
                    "AND NOT EXISTS ("
                    "SELECT 1 FROM pg_catalog.pg_auth_members membership "
                    "WHERE membership.member = role.oid) "
                    "FROM pg_catalog.pg_roles role WHERE rolname = current_user"
                )
            )
        ).scalar_one()
        forbidden_grants = await _runtime_navigator_privilege_count(session)
        relation_privilege_violations = await _runtime_relation_privilege_violation_count(session)
        forbidden_functions = await _runtime_unapproved_function_privilege_count(session)
        allowed = (
            await session.execute(
                text(
                    "SELECT has_table_privilege(current_user, "
                    "'portfolio_demo.catalog_identity', 'SELECT') "
                    "AND has_table_privilege(current_user, "
                    "'portfolio_demo.catalog_graph', 'SELECT') "
                    "AND has_table_privilege(current_user, "
                    "'navigator.alembic_version', 'SELECT') "
                    "AND has_function_privilege(current_user, "
                    "'portfolio_demo.governed_catalog_is_empty()', 'EXECUTE') "
                    "AND NOT has_schema_privilege(current_user, 'public', 'CREATE') "
                    "AND NOT has_schema_privilege(current_user, 'navigator', 'CREATE') "
                    "AND NOT has_schema_privilege(current_user, 'portfolio_demo', 'CREATE') "
                    "AND has_database_privilege(current_user, current_database(), 'CONNECT') "
                    "AND NOT has_database_privilege(current_user, current_database(), 'CREATE') "
                    "AND NOT has_database_privilege(current_user, current_database(), 'TEMP')"
                )
            )
        ).scalar_one()
        if (
            not role_is_restricted
            or forbidden_grants != 0
            or relation_privilege_violations != 0
            or forbidden_functions != 0
            or not allowed
        ):
            raise PortfolioDemoDatabaseError("portfolio demo runtime privileges differ")


async def _rotate_portfolio_demo_runtime_password(
    connection: AsyncConnection,
    password: str,
) -> None:
    """Rotate through a transaction-local setting so SQL text never contains the secret."""

    try:
        await connection.execute(
            text(f"SELECT pg_catalog.set_config('{_RUNTIME_PASSWORD_SETTING}', :password, true)"),
            {"password": password},
        )
        await connection.execute(text(_RUNTIME_PASSWORD_ROTATION_SQL))
    except Exception:
        raise PortfolioDemoDatabaseError(
            "portfolio demo runtime credential rotation failed"
        ) from None


def portfolio_demo_runtime_database_url(admin_database_url: str, password: str) -> str:
    """Build the runtime URL without logging either credential."""

    return (
        make_url(admin_database_url)
        .set(
            username=PORTFOLIO_DEMO_RUNTIME_ROLE,
            password=password,
        )
        .render_as_string(hide_password=False)
    )


async def _navigator_row_count(session: AsyncConnection | AsyncSession) -> int:
    subqueries = " + ".join(
        f'(SELECT count(*) FROM navigator."{table_name}")'
        for table_name in NAVIGATOR_APPLICATION_TABLES
    )
    return int((await session.execute(text(f"SELECT {subqueries}"))).scalar_one())


async def _assert_governed_rows_inaccessible_or_empty(
    session: AsyncConnection | AsyncSession,
) -> None:
    current_user = (await session.execute(text("SELECT current_user"))).scalar_one()
    if current_user == PORTFOLIO_DEMO_RUNTIME_ROLE:
        if await _runtime_navigator_privilege_count(session) != 0:
            raise PortfolioDemoDatabaseError("portfolio demo runtime can access governed tables")
        governed_catalog_is_empty = (
            await session.execute(text("SELECT portfolio_demo.governed_catalog_is_empty()"))
        ).scalar_one()
        if not governed_catalog_is_empty:
            raise PortfolioDemoDatabaseError("portfolio demo database contains governed rows")
        return
    if await _navigator_row_count(session) != 0:
        raise PortfolioDemoDatabaseError("portfolio demo database contains governed rows")


async def _runtime_navigator_privilege_count(
    session: AsyncConnection | AsyncSession,
) -> int:
    table_names = ", ".join(f"'{name}'" for name in NAVIGATOR_APPLICATION_TABLES)
    return int(
        (
            await session.execute(
                text(
                    "SELECT count(*) FROM pg_catalog.pg_tables "
                    "WHERE schemaname = 'navigator' "
                    f"AND tablename IN ({table_names}) "
                    "AND (tableowner = current_user "
                    "OR has_table_privilege(current_user, "
                    "format('%I.%I', schemaname, tablename), 'SELECT') "
                    "OR has_table_privilege(current_user, "
                    "format('%I.%I', schemaname, tablename), 'INSERT') "
                    "OR has_table_privilege(current_user, "
                    "format('%I.%I', schemaname, tablename), 'UPDATE') "
                    "OR has_table_privilege(current_user, "
                    "format('%I.%I', schemaname, tablename), 'DELETE'))"
                )
            )
        ).scalar_one()
    )


async def _runtime_relation_privilege_violation_count(
    session: AsyncConnection | AsyncSession,
) -> int:
    """Require the runtime relation surface to be exactly three SELECT-only grants."""

    return int(
        (
            await session.execute(
                text(
                    "WITH relations AS ("
                    "SELECT class.oid, namespace.nspname, class.relname, "
                    "pg_catalog.pg_get_userbyid(class.relowner) AS owner_name, "
                    "((namespace.nspname = 'navigator' "
                    "AND class.relname = 'alembic_version') "
                    "OR (namespace.nspname = 'portfolio_demo' "
                    "AND class.relname IN ('catalog_identity', 'catalog_graph'))) AS allowed "
                    "FROM pg_catalog.pg_class class "
                    "JOIN pg_catalog.pg_namespace namespace "
                    "ON namespace.oid = class.relnamespace "
                    "WHERE namespace.nspname IN ('navigator', 'portfolio_demo') "
                    "AND class.relkind IN ('r', 'p', 'v', 'm', 'f')"
                    ") SELECT count(*) FROM relations WHERE owner_name = current_user OR "
                    "(allowed AND ("
                    "NOT has_table_privilege(current_user, oid, 'SELECT') "
                    "OR has_table_privilege(current_user, oid, 'INSERT') "
                    "OR has_table_privilege(current_user, oid, 'UPDATE') "
                    "OR has_table_privilege(current_user, oid, 'DELETE') "
                    "OR has_table_privilege(current_user, oid, 'TRUNCATE') "
                    "OR has_table_privilege(current_user, oid, 'REFERENCES') "
                    "OR has_table_privilege(current_user, oid, 'TRIGGER'))) "
                    "OR (NOT allowed AND ("
                    "has_table_privilege(current_user, oid, 'SELECT') "
                    "OR has_table_privilege(current_user, oid, 'INSERT') "
                    "OR has_table_privilege(current_user, oid, 'UPDATE') "
                    "OR has_table_privilege(current_user, oid, 'DELETE') "
                    "OR has_table_privilege(current_user, oid, 'TRUNCATE') "
                    "OR has_table_privilege(current_user, oid, 'REFERENCES') "
                    "OR has_table_privilege(current_user, oid, 'TRIGGER')))"
                )
            )
        ).scalar_one()
    )


async def _runtime_unapproved_function_privilege_count(
    session: AsyncConnection | AsyncSession,
) -> int:
    return int(
        (
            await session.execute(
                text(
                    "SELECT count(*) FROM pg_catalog.pg_proc procedure "
                    "JOIN pg_catalog.pg_namespace namespace "
                    "ON namespace.oid = procedure.pronamespace "
                    "WHERE namespace.nspname IN ('navigator', 'portfolio_demo') "
                    "AND has_function_privilege(current_user, procedure.oid, 'EXECUTE') "
                    "AND NOT (namespace.nspname = 'portfolio_demo' "
                    "AND procedure.proname = 'governed_catalog_is_empty' "
                    "AND procedure.pronargs = 0)"
                )
            )
        ).scalar_one()
    )


def _assert_demo_configuration(settings: Settings) -> None:
    if settings.catalog_mode is not CatalogDataMode.PORTFOLIO_DEMO_CATALOG:
        raise PortfolioDemoDatabaseError("portfolio demo mode is not configured")
    expected_spec = load_portfolio_demo_spec()
    if settings.expected_database_identity != expected_spec.database_identity:
        raise PortfolioDemoDatabaseError("portfolio demo database identity configuration differs")
    if settings.expected_database_name is None:
        raise PortfolioDemoDatabaseError("portfolio demo database name is not configured")


async def _user_schemas(session: AsyncConnection | AsyncSession) -> set[str]:
    rows = (
        await session.execute(
            text(
                "SELECT nspname FROM pg_catalog.pg_namespace "
                "WHERE nspname <> 'information_schema' AND nspname !~ '^pg_'"
            )
        )
    ).scalars()
    return set(rows)


async def _user_relations(
    session: AsyncConnection | AsyncSession,
    *,
    relation_kind: str,
) -> set[str]:
    if relation_kind == "tables":
        kind_filter = "c.relkind IN ('r', 'p')"
    elif relation_kind == "views":
        kind_filter = "c.relkind IN ('v', 'm')"
    elif relation_kind == "other":
        kind_filter = "c.relkind IN ('S', 'f', 'c')"
    else:
        raise ValueError("unsupported relation kind")
    rows = (
        await session.execute(
            text(
                "SELECT n.nspname || '.' || c.relname "
                "FROM pg_catalog.pg_class c "
                "JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname <> 'information_schema' AND n.nspname !~ '^pg_' "
                f"AND {kind_filter}"
            )
        )
    ).scalars()
    return set(rows)


async def _schema_routine_count(
    session: AsyncConnection | AsyncSession,
    schema_name: str,
) -> int:
    return int(
        (
            await session.execute(
                text(
                    "SELECT count(*) FROM pg_catalog.pg_proc procedure "
                    "JOIN pg_catalog.pg_namespace namespace "
                    "ON namespace.oid = procedure.pronamespace "
                    "WHERE namespace.nspname = :schema_name"
                ),
                {"schema_name": schema_name},
            )
        ).scalar_one()
    )


async def _schema_standalone_type_count(
    session: AsyncConnection | AsyncSession,
    schema_name: str,
) -> int:
    return int(
        (
            await session.execute(
                text(
                    "SELECT count(*) FROM pg_catalog.pg_type type "
                    "JOIN pg_catalog.pg_namespace namespace ON namespace.oid = type.typnamespace "
                    "WHERE namespace.nspname = :schema_name AND type.typtype IN ('d', 'e')"
                ),
                {"schema_name": schema_name},
            )
        ).scalar_one()
    )


async def _assert_exact_relation_inventory(
    session: AsyncConnection | AsyncSession,
) -> None:
    if await _user_schemas(session) != _EXPECTED_USER_SCHEMAS:
        raise PortfolioDemoDatabaseError("portfolio demo schema inventory differs")
    if await _user_relations(session, relation_kind="tables") != _EXPECTED_USER_TABLES:
        raise PortfolioDemoDatabaseError("portfolio demo table inventory differs")
    if await _user_relations(session, relation_kind="views") != _EXPECTED_USER_VIEWS:
        raise PortfolioDemoDatabaseError("portfolio demo view inventory differs")
    if await _user_relations(session, relation_kind="other"):
        raise PortfolioDemoDatabaseError("portfolio demo relation inventory differs")
    if await _schema_routine_count(session, "public") != 0:
        raise PortfolioDemoDatabaseError("portfolio demo public routine inventory differs")
    for schema_name in _EXPECTED_USER_SCHEMAS:
        if await _schema_standalone_type_count(session, schema_name) != 0:
            raise PortfolioDemoDatabaseError("portfolio demo type inventory differs")
    demo_relations = (
        await session.execute(
            text(
                "SELECT class.relname, class.relpersistence, class.relrowsecurity, "
                "class.relforcerowsecurity, class.relreplident, access_method.amname "
                "FROM pg_catalog.pg_class class "
                "JOIN pg_catalog.pg_namespace namespace "
                "ON namespace.oid = class.relnamespace "
                "JOIN pg_catalog.pg_am access_method ON access_method.oid = class.relam "
                "WHERE namespace.nspname = 'portfolio_demo' "
                "AND class.relname IN ('catalog_identity', 'catalog_graph')"
            )
        )
    ).all()
    if {
        (
            row.relname,
            row.relpersistence,
            row.relrowsecurity,
            row.relforcerowsecurity,
            row.relreplident,
            row.amname,
        )
        for row in demo_relations
    } != {
        ("catalog_identity", "p", False, False, "d", "heap"),
        ("catalog_graph", "p", False, False, "d", "heap"),
    }:
        raise PortfolioDemoDatabaseError("portfolio demo table properties differ")
    columns = (
        await session.execute(
            text(
                "SELECT class.relname, attribute.attnum, attribute.attname, "
                "pg_catalog.format_type(attribute.atttypid, attribute.atttypmod) AS data_type, "
                "attribute.attnotnull, "
                "COALESCE(pg_catalog.pg_get_expr(default_value.adbin, "
                "default_value.adrelid), '') AS default_expression, "
                "attribute.attidentity, attribute.attgenerated "
                "FROM pg_catalog.pg_attribute attribute "
                "JOIN pg_catalog.pg_class class ON class.oid = attribute.attrelid "
                "JOIN pg_catalog.pg_namespace namespace "
                "ON namespace.oid = class.relnamespace "
                "LEFT JOIN pg_catalog.pg_attrdef default_value "
                "ON default_value.adrelid = attribute.attrelid "
                "AND default_value.adnum = attribute.attnum "
                "WHERE namespace.nspname = 'portfolio_demo' "
                "AND class.relname IN ('catalog_identity', 'catalog_graph') "
                "AND attribute.attnum > 0 AND NOT attribute.attisdropped"
            )
        )
    ).all()
    if {
        (
            row.relname,
            row.attnum,
            row.attname,
            row.data_type,
            row.attnotnull,
            row.default_expression,
            row.attidentity,
            row.attgenerated,
        )
        for row in columns
    } != _EXPECTED_DEMO_COLUMNS:
        raise PortfolioDemoDatabaseError("portfolio demo column inventory differs")
    constraints = (
        await session.execute(
            text(
                "SELECT class.relname, constraint_record.conname, constraint_record.contype, "
                "constraint_record.condeferrable, constraint_record.condeferred, "
                "constraint_record.convalidated, "
                "pg_catalog.pg_get_constraintdef(constraint_record.oid, true) AS definition "
                "FROM pg_catalog.pg_constraint constraint_record "
                "JOIN pg_catalog.pg_class class ON class.oid = constraint_record.conrelid "
                "JOIN pg_catalog.pg_namespace namespace "
                "ON namespace.oid = class.relnamespace "
                "WHERE namespace.nspname = 'portfolio_demo'"
            )
        )
    ).all()
    if (
        any(row.condeferrable or row.condeferred or not row.convalidated for row in constraints)
        or {(row.relname, row.conname, row.contype, row.definition) for row in constraints}
        != _EXPECTED_DEMO_CONSTRAINTS
    ):
        raise PortfolioDemoDatabaseError("portfolio demo constraint inventory differs")
    indexes = (
        await session.execute(
            text(
                "SELECT tablename, indexname, indexdef FROM pg_catalog.pg_indexes "
                "WHERE schemaname = 'portfolio_demo'"
            )
        )
    ).all()
    if {(row.tablename, row.indexname, row.indexdef) for row in indexes} != (
        _EXPECTED_DEMO_INDEXES
    ):
        raise PortfolioDemoDatabaseError("portfolio demo index inventory differs")
    triggers = (
        await session.execute(
            text(
                "SELECT c.relname, t.tgname, t.tgtype, t.tgenabled, "
                "pg_catalog.pg_get_triggerdef(t.oid, true) AS definition "
                "FROM pg_catalog.pg_trigger t "
                "JOIN pg_catalog.pg_class c ON c.oid = t.tgrelid "
                "JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'portfolio_demo' AND NOT t.tgisinternal "
            )
        )
    ).all()
    if {
        (row.relname, row.tgname, row.tgtype, row.tgenabled, row.definition) for row in triggers
    } != _EXPECTED_DEMO_TRIGGERS:
        raise PortfolioDemoDatabaseError("portfolio demo immutability controls differ")
    functions = (
        await session.execute(
            text(
                "SELECT p.proname, pg_catalog.pg_get_function_identity_arguments(p.oid) AS args, "
                "language.lanname, p.prosecdef, p.provolatile, p.prokind, p.proconfig, p.prosrc, "
                "pg_catalog.pg_get_userbyid(p.proowner) AS owner "
                "FROM pg_catalog.pg_proc p "
                "JOIN pg_catalog.pg_namespace namespace ON namespace.oid = p.pronamespace "
                "JOIN pg_catalog.pg_language language ON language.oid = p.prolang "
                "WHERE namespace.nspname = 'portfolio_demo'"
            )
        )
    ).all()
    expected_functions = {
        "reject_catalog_mutation": (
            "",
            "plpgsql",
            False,
            "v",
            "f",
            None,
            _REJECT_CATALOG_MUTATION_BODY,
        ),
        "governed_catalog_is_empty": (
            "",
            "sql",
            True,
            "s",
            "f",
            ("search_path=pg_catalog",),
            _GOVERNED_CATALOG_EMPTY_BODY,
        ),
    }
    if len(functions) != len(expected_functions):
        raise PortfolioDemoDatabaseError("portfolio demo function inventory differs")
    table_owners = set(
        (
            await session.execute(
                text(
                    "SELECT tableowner FROM pg_catalog.pg_tables "
                    "WHERE schemaname = 'portfolio_demo' "
                    "AND tablename IN ('catalog_identity', 'catalog_graph')"
                )
            )
        ).scalars()
    )
    if len(table_owners) != 1 or PORTFOLIO_DEMO_RUNTIME_ROLE in table_owners:
        raise PortfolioDemoDatabaseError("portfolio demo object ownership differs")
    table_owner = next(iter(table_owners))
    for function in functions:
        expected = expected_functions.get(function.proname)
        actual = (
            function.args,
            function.lanname,
            function.prosecdef,
            function.provolatile,
            function.prokind,
            tuple(function.proconfig) if function.proconfig is not None else None,
            function.prosrc,
        )
        if expected is None or actual != expected or function.owner != table_owner:
            raise PortfolioDemoDatabaseError("portfolio demo function inventory differs")


__all__ = [
    "NAVIGATOR_APPLICATION_TABLES",
    "PORTFOLIO_DEMO_RUNTIME_ROLE",
    "PORTFOLIO_DEMO_SCHEMA",
    "DemoMigrationTargetState",
    "PortfolioDemoDatabaseError",
    "VerifiedPortfolioDemoDatabase",
    "assert_portfolio_demo_migration_target",
    "assert_portfolio_demo_runtime_access",
    "portfolio_demo_runtime_database_url",
    "provision_portfolio_demo_runtime_role",
    "read_verified_demo_spec",
    "seed_portfolio_demo_database",
    "verify_portfolio_demo_database",
]
