"""Create canonical requirements, versioned meaning, and evidence relationships.

Revision ID: 0002_requirement_evidence
Revises: 0001_governance_source
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_requirement_evidence"
down_revision: str | None = "0001_governance_source"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def execute(sql: str) -> None:
    """Execute one explicitly schema-qualified PostgreSQL statement."""
    op.execute(sa.text(sql))


def upgrade() -> None:
    """Create stable requirement identities, versions, activities, and evidence."""
    execute(
        """
        CREATE TABLE navigator.requirements (
            id UUID NOT NULL,
            code TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_requirements PRIMARY KEY (id),
            CONSTRAINT uq_requirements_code UNIQUE (code),
            CONSTRAINT ck_requirements_code_format
                CHECK (code ~ '^[a-z][a-z0-9_]*$')
        )
        """
    )

    execute(
        """
        CREATE TABLE navigator.requirement_versions (
            id UUID NOT NULL,
            requirement_id UUID NOT NULL,
            version_number INTEGER NOT NULL,
            scope_type TEXT NOT NULL,
            responsible_entity_id UUID NOT NULL,
            canonical_title_ar TEXT NOT NULL,
            canonical_description_ar TEXT NOT NULL,
            canonical_title_en TEXT,
            canonical_description_en TEXT,
            simplified_explanation_ar TEXT,
            simplified_explanation_en TEXT,
            effective_from DATE,
            effective_until DATE,
            verification_status TEXT DEFAULT 'pending_source_verification' NOT NULL,
            is_current BOOLEAN DEFAULT false NOT NULL,
            supersedes_requirement_version_id UUID,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_requirement_versions PRIMARY KEY (id),
            CONSTRAINT uq_requirement_versions_requirement_version
                UNIQUE (requirement_id, version_number),
            CONSTRAINT uq_requirement_versions_supersedes_requirement_version
                UNIQUE (supersedes_requirement_version_id),
            CONSTRAINT ck_requirement_versions_positive_version_number
                CHECK (version_number > 0),
            CONSTRAINT ck_requirement_versions_scope_type
                CHECK (scope_type IN ('national', 'activity_specific', 'site_dependent')),
            CONSTRAINT ck_requirement_versions_title_ar_nonblank
                CHECK (btrim(canonical_title_ar) <> ''),
            CONSTRAINT ck_requirement_versions_description_ar_nonblank
                CHECK (btrim(canonical_description_ar) <> ''),
            CONSTRAINT ck_requirement_versions_effective_date_order CHECK (
                effective_until IS NULL OR effective_from IS NULL
                OR effective_until >= effective_from
            ),
            CONSTRAINT ck_requirement_versions_verification_status CHECK (
                verification_status IN (
                    'pending_source_verification', 'pending_review', 'approved',
                    'rejected', 'conflicting', 'stale', 'expired', 'superseded',
                    'historical'
                )
            ),
            CONSTRAINT ck_requirement_versions_inactive_status_not_current CHECK (
                verification_status NOT IN ('expired', 'superseded', 'historical')
                OR NOT is_current
            ),
            CONSTRAINT ck_requirement_versions_not_self_superseding
                CHECK (supersedes_requirement_version_id IS DISTINCT FROM id),
            CONSTRAINT fk_requirement_versions_requirement
                FOREIGN KEY (requirement_id)
                REFERENCES navigator.requirements (id) ON DELETE RESTRICT,
            CONSTRAINT fk_requirement_versions_responsible_entity
                FOREIGN KEY (responsible_entity_id)
                REFERENCES navigator.government_entities (id) ON DELETE RESTRICT,
            CONSTRAINT fk_requirement_versions_supersedes
                FOREIGN KEY (supersedes_requirement_version_id)
                REFERENCES navigator.requirement_versions (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE UNIQUE INDEX uq_requirement_versions_one_current "
        "ON navigator.requirement_versions (requirement_id) WHERE is_current"
    )
    execute(
        "CREATE INDEX ix_requirement_versions_responsible_entity_id "
        "ON navigator.requirement_versions (responsible_entity_id)"
    )
    execute(
        "CREATE INDEX ix_requirement_versions_verification_status "
        "ON navigator.requirement_versions (verification_status)"
    )
    execute(
        "CREATE INDEX ix_requirement_versions_effective_until "
        "ON navigator.requirement_versions (effective_until)"
    )

    execute(
        """
        CREATE TABLE navigator.requirement_activities (
            requirement_version_id UUID NOT NULL,
            activity_id UUID NOT NULL,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_requirement_activities
                PRIMARY KEY (requirement_version_id, activity_id),
            CONSTRAINT fk_requirement_activities_requirement_version
                FOREIGN KEY (requirement_version_id)
                REFERENCES navigator.requirement_versions (id) ON DELETE RESTRICT,
            CONSTRAINT fk_requirement_activities_activity
                FOREIGN KEY (activity_id)
                REFERENCES navigator.business_activities (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE INDEX ix_requirement_activities_activity_id "
        "ON navigator.requirement_activities (activity_id)"
    )

    execute(
        """
        CREATE TABLE navigator.requirement_sources (
            id UUID NOT NULL,
            requirement_version_id UUID NOT NULL,
            source_version_id UUID NOT NULL,
            source_role TEXT NOT NULL,
            official_excerpt_ar TEXT,
            official_excerpt_en TEXT,
            excerpt_locator TEXT,
            relationship_status TEXT DEFAULT 'pending_review' NOT NULL,
            role_review_event_id UUID,
            resolved_at TIMESTAMPTZ,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_requirement_sources PRIMARY KEY (id),
            CONSTRAINT uq_requirement_sources_requirement_source
                UNIQUE (requirement_version_id, source_version_id),
            CONSTRAINT ck_requirement_sources_source_role CHECK (
                source_role IN (
                    'primary', 'supporting', 'clarifying', 'conflicting',
                    'superseding', 'historical'
                )
            ),
            CONSTRAINT ck_requirement_sources_relationship_status CHECK (
                relationship_status IN (
                    'pending_review', 'active', 'resolved', 'superseded'
                )
            ),
            CONSTRAINT ck_requirement_sources_relied_evidence_complete CHECK (
                relationship_status <> 'active'
                OR source_role = 'historical'
                OR (
                    official_excerpt_ar IS NOT NULL
                    AND btrim(official_excerpt_ar) <> ''
                    AND excerpt_locator IS NOT NULL
                    AND btrim(excerpt_locator) <> ''
                )
            ),
            CONSTRAINT ck_requirement_sources_active_has_review CHECK (
                relationship_status <> 'active' OR role_review_event_id IS NOT NULL
            ),
            CONSTRAINT ck_requirement_sources_resolution_timestamp CHECK (
                (relationship_status = 'resolved' AND resolved_at IS NOT NULL)
                OR
                (relationship_status <> 'resolved' AND resolved_at IS NULL)
            ),
            CONSTRAINT fk_requirement_sources_requirement_version
                FOREIGN KEY (requirement_version_id)
                REFERENCES navigator.requirement_versions (id) ON DELETE RESTRICT,
            CONSTRAINT fk_requirement_sources_source_version
                FOREIGN KEY (source_version_id)
                REFERENCES navigator.source_versions (id) ON DELETE RESTRICT,
            CONSTRAINT fk_requirement_sources_role_review
                FOREIGN KEY (role_review_event_id)
                REFERENCES navigator.review_events (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE UNIQUE INDEX uq_requirement_sources_one_active_primary "
        "ON navigator.requirement_sources (requirement_version_id) "
        "WHERE source_role = 'primary' AND relationship_status = 'active'"
    )
    execute(
        "CREATE INDEX ix_requirement_sources_source_version_id "
        "ON navigator.requirement_sources (source_version_id)"
    )
    execute(
        "CREATE INDEX ix_requirement_sources_role_review_event_id "
        "ON navigator.requirement_sources (role_review_event_id)"
    )
    execute(
        "CREATE INDEX ix_requirement_sources_requirement_status "
        "ON navigator.requirement_sources "
        "(requirement_version_id, relationship_status)"
    )

    execute(
        """
        ALTER TABLE navigator.research_events
        ADD COLUMN requirement_version_id UUID,
        ADD COLUMN requirement_source_id UUID
        """
    )
    execute(
        """
        ALTER TABLE navigator.research_events
        ADD CONSTRAINT fk_research_events_requirement_version
            FOREIGN KEY (requirement_version_id)
            REFERENCES navigator.requirement_versions (id) ON DELETE RESTRICT,
        ADD CONSTRAINT fk_research_events_requirement_source
            FOREIGN KEY (requirement_source_id)
            REFERENCES navigator.requirement_sources (id) ON DELETE RESTRICT
        """
    )
    execute(
        "ALTER TABLE navigator.research_events "
        "DROP CONSTRAINT ck_research_events_exactly_one_target"
    )
    execute(
        """
        ALTER TABLE navigator.research_events
        ADD CONSTRAINT ck_research_events_exactly_one_target CHECK (
            num_nonnulls(
                government_entity_id, platform_id, domain_id, source_id,
                source_version_id, requirement_version_id, requirement_source_id
            ) = 1
        )
        """
    )
    execute(
        "CREATE INDEX ix_research_events_requirement_version_id "
        "ON navigator.research_events (requirement_version_id)"
    )
    execute(
        "CREATE INDEX ix_research_events_requirement_source_id "
        "ON navigator.research_events (requirement_source_id)"
    )

    execute(
        """
        CREATE FUNCTION navigator.guard_requirement_identity()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        BEGIN
            RAISE EXCEPTION 'canonical requirement identity is immutable';
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_requirement_supersession()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            expected_predecessor UUID;
        BEGIN
            IF TG_OP = 'UPDATE' AND (
                NEW.id IS DISTINCT FROM OLD.id
                OR NEW.requirement_id IS DISTINCT FROM OLD.requirement_id
                OR NEW.version_number IS DISTINCT FROM OLD.version_number
                OR NEW.supersedes_requirement_version_id
                    IS DISTINCT FROM OLD.supersedes_requirement_version_id
            ) THEN
                RAISE EXCEPTION 'requirement version identity is immutable';
            END IF;
            IF NEW.version_number = 1 THEN
                IF NEW.supersedes_requirement_version_id IS NOT NULL THEN
                    RAISE EXCEPTION 'first requirement version cannot supersede another';
                END IF;
                RETURN NEW;
            END IF;

            SELECT rv.id
            INTO expected_predecessor
            FROM navigator.requirement_versions AS rv
            WHERE rv.requirement_id = NEW.requirement_id
              AND rv.version_number = NEW.version_number - 1;

            IF expected_predecessor IS NULL
                OR NEW.supersedes_requirement_version_id IS DISTINCT FROM
                    expected_predecessor
            THEN
                RAISE EXCEPTION 'requirement versions must form a linear chain';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.lock_requirement_activity_parent()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            target_requirement_version UUID;
        BEGIN
            target_requirement_version :=
                CASE WHEN TG_OP = 'DELETE'
                    THEN OLD.requirement_version_id
                    ELSE NEW.requirement_version_id
                END;
            PERFORM 1
            FROM navigator.requirement_versions
            WHERE id = target_requirement_version
            FOR UPDATE;
            RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_requirement_source()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            target_requirement_version UUID;
            review_decision TEXT;
            target_matches BOOLEAN;
            governed_change BOOLEAN;
            review_time TIMESTAMPTZ;
            old_review_time TIMESTAMPTZ;
        BEGIN
            target_requirement_version :=
                CASE WHEN TG_OP = 'DELETE'
                    THEN OLD.requirement_version_id
                    ELSE NEW.requirement_version_id
                END;

            PERFORM 1
            FROM navigator.requirement_versions
            WHERE id = target_requirement_version
            FOR UPDATE;

            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;

            IF TG_OP = 'INSERT' THEN
                IF NEW.relationship_status <> 'pending_review'
                    OR NEW.role_review_event_id IS NOT NULL
                THEN
                    RAISE EXCEPTION 'evidence relationships begin pending review';
                END IF;
                RETURN NEW;
            END IF;

            IF NEW.requirement_version_id IS DISTINCT FROM OLD.requirement_version_id
                OR NEW.source_version_id IS DISTINCT FROM OLD.source_version_id
                OR NEW.id IS DISTINCT FROM OLD.id
            THEN
                RAISE EXCEPTION 'evidence relationship endpoints are immutable';
            END IF;

            governed_change :=
                NEW.source_role IS DISTINCT FROM OLD.source_role
                OR NEW.official_excerpt_ar IS DISTINCT FROM OLD.official_excerpt_ar
                OR NEW.official_excerpt_en IS DISTINCT FROM OLD.official_excerpt_en
                OR NEW.excerpt_locator IS DISTINCT FROM OLD.excerpt_locator
                OR NEW.relationship_status IS DISTINCT FROM OLD.relationship_status
                OR NEW.resolved_at IS DISTINCT FROM OLD.resolved_at
                OR NEW.role_review_event_id IS DISTINCT FROM OLD.role_review_event_id;

            IF NOT governed_change THEN
                RETURN NEW;
            END IF;
            IF NEW.role_review_event_id IS NULL
                OR NEW.role_review_event_id IS NOT DISTINCT FROM OLD.role_review_event_id
            THEN
                RAISE EXCEPTION 'evidence changes require a new exact-target review';
            END IF;

            SELECT rv.decision, rv.reviewed_at, re.requirement_source_id = NEW.id
            INTO review_decision, review_time, target_matches
            FROM navigator.review_events AS rv
            JOIN navigator.research_events AS re ON re.id = rv.research_event_id
            WHERE rv.id = NEW.role_review_event_id;

            IF NOT FOUND
                OR target_matches IS DISTINCT FROM TRUE
                OR review_decision <> 'approved'
                OR review_time > pg_catalog.clock_timestamp()
            THEN
                RAISE EXCEPTION 'evidence review does not approve this relationship';
            END IF;
            IF NOT EXISTS (
                SELECT 1
                FROM navigator.research_events AS reviewed_research
                JOIN navigator.research_event_evidence AS reviewed_evidence
                  ON reviewed_evidence.research_event_id = reviewed_research.id
                WHERE reviewed_research.id = (
                    SELECT research_event_id
                    FROM navigator.review_events
                    WHERE id = NEW.role_review_event_id
                )
                  AND reviewed_evidence.source_version_id = NEW.source_version_id
            ) THEN
                RAISE EXCEPTION 'evidence review must cite the linked source version';
            END IF;
            IF OLD.role_review_event_id IS NOT NULL THEN
                SELECT reviewed_at
                INTO old_review_time
                FROM navigator.review_events
                WHERE id = OLD.role_review_event_id;
                IF review_time <= old_review_time THEN
                    RAISE EXCEPTION 'replacement evidence review must be newer';
                END IF;
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE TRIGGER trg_10_guard_requirement_identity
        BEFORE UPDATE OR DELETE ON navigator.requirements
        FOR EACH ROW EXECUTE FUNCTION navigator.guard_requirement_identity()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_10_validate_requirement_supersession
        BEFORE INSERT OR UPDATE OF id, requirement_id, version_number,
            supersedes_requirement_version_id
        ON navigator.requirement_versions
        FOR EACH ROW EXECUTE FUNCTION navigator.validate_requirement_supersession()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_10_lock_requirement_activity_parent
        BEFORE INSERT OR UPDATE OR DELETE ON navigator.requirement_activities
        FOR EACH ROW EXECUTE FUNCTION navigator.lock_requirement_activity_parent()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_10_validate_requirement_source
        BEFORE INSERT OR UPDATE OR DELETE ON navigator.requirement_sources
        FOR EACH ROW EXECUTE FUNCTION navigator.validate_requirement_source()
        """
    )
    for table_name in ("requirement_versions", "requirement_sources"):
        execute(
            f"""
            CREATE TRIGGER trg_90_set_updated_at
            BEFORE UPDATE ON navigator.{table_name}
            FOR EACH ROW EXECUTE FUNCTION navigator.set_updated_at_on_change()
            """
        )


def downgrade() -> None:
    """Remove versioned requirement and evidence structures."""
    for table_name in ("requirement_versions", "requirement_sources"):
        execute(f"DROP TRIGGER IF EXISTS trg_90_set_updated_at ON navigator.{table_name}")
    execute("DROP TRIGGER trg_10_validate_requirement_source ON navigator.requirement_sources")
    execute(
        "DROP TRIGGER trg_10_lock_requirement_activity_parent ON navigator.requirement_activities"
    )
    execute(
        "DROP TRIGGER trg_10_validate_requirement_supersession ON navigator.requirement_versions"
    )
    execute("DROP TRIGGER trg_10_guard_requirement_identity ON navigator.requirements")
    execute("DROP FUNCTION navigator.validate_requirement_source()")
    execute("DROP FUNCTION navigator.lock_requirement_activity_parent()")
    execute("DROP FUNCTION navigator.validate_requirement_supersession()")
    execute("DROP FUNCTION navigator.guard_requirement_identity()")

    execute("DROP INDEX navigator.ix_research_events_requirement_source_id")
    execute("DROP INDEX navigator.ix_research_events_requirement_version_id")
    execute(
        "ALTER TABLE navigator.research_events "
        "DROP CONSTRAINT ck_research_events_exactly_one_target"
    )
    execute(
        "ALTER TABLE navigator.research_events "
        "DROP CONSTRAINT fk_research_events_requirement_source, "
        "DROP CONSTRAINT fk_research_events_requirement_version"
    )
    execute(
        "ALTER TABLE navigator.research_events "
        "DROP COLUMN requirement_source_id, "
        "DROP COLUMN requirement_version_id"
    )
    execute(
        """
        ALTER TABLE navigator.research_events
        ADD CONSTRAINT ck_research_events_exactly_one_target CHECK (
            num_nonnulls(
                government_entity_id, platform_id, domain_id, source_id,
                source_version_id
            ) = 1
        )
        """
    )

    execute("DROP TABLE navigator.requirement_sources")
    execute("DROP TABLE navigator.requirement_activities")
    execute("DROP TABLE navigator.requirement_versions")
    execute("DROP TABLE navigator.requirements")
