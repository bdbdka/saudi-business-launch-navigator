"""Create governance, source, research, and freshness schema.

Revision ID: 0001_governance_source
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_governance_source"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def execute(sql: str) -> None:
    """Execute one explicitly schema-qualified PostgreSQL statement."""
    op.execute(sa.text(sql))


def upgrade() -> None:
    """Create governance, source, research, and freshness structures."""
    execute("CREATE SCHEMA IF NOT EXISTS navigator")

    execute(
        """
        CREATE TABLE navigator.government_entities (
            id UUID NOT NULL,
            code TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            official_name_ar TEXT NOT NULL,
            official_name_en TEXT,
            explanatory_name_en TEXT,
            parent_entity_id UUID,
            supervising_entity_id UUID,
            valid_from DATE,
            valid_until DATE,
            verification_status TEXT DEFAULT 'discovered' NOT NULL,
            verification_review_event_id UUID,
            last_verified_at TIMESTAMPTZ,
            review_interval_days INTEGER,
            next_review_at TIMESTAMPTZ,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_government_entities PRIMARY KEY (id),
            CONSTRAINT uq_government_entities_code UNIQUE (code),
            CONSTRAINT ck_government_entities_code_format
                CHECK (code ~ '^[a-z][a-z0-9_]*$'),
            CONSTRAINT ck_government_entities_entity_type CHECK (
                entity_type IN (
                    'government_ministry', 'government_authority', 'government_center',
                    'government_organization', 'historical_entity'
                )
            ),
            CONSTRAINT ck_government_entities_verification_status CHECK (
                verification_status IN (
                    'discovered', 'research_in_progress', 'pending_review', 'approved',
                    'rejected', 'requires_additional_review', 'blocked_by_conflict',
                    'stale', 'expired', 'inaccessible', 'superseded', 'historical'
                )
            ),
            CONSTRAINT ck_government_entities_official_name_ar_nonblank
                CHECK (btrim(official_name_ar) <> ''),
            CONSTRAINT ck_government_entities_valid_date_order
                CHECK (valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from),
            CONSTRAINT ck_government_entities_freshness_order CHECK (
                (last_verified_at IS NULL AND review_interval_days IS NULL
                    AND next_review_at IS NULL)
                OR
                (last_verified_at IS NOT NULL AND review_interval_days IS NOT NULL
                    AND next_review_at IS NOT NULL
                    AND next_review_at =
                        last_verified_at + make_interval(days => review_interval_days))
            ),
            CONSTRAINT ck_government_entities_review_interval
                CHECK (review_interval_days BETWEEN 30 AND 180),
            CONSTRAINT ck_government_entities_not_own_parent
                CHECK (parent_entity_id IS DISTINCT FROM id),
            CONSTRAINT ck_government_entities_not_own_supervisor
                CHECK (supervising_entity_id IS DISTINCT FROM id),
            CONSTRAINT fk_government_entities_parent
                FOREIGN KEY (parent_entity_id)
                REFERENCES navigator.government_entities (id) ON DELETE RESTRICT,
            CONSTRAINT fk_government_entities_supervisor
                FOREIGN KEY (supervising_entity_id)
                REFERENCES navigator.government_entities (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE INDEX ix_government_entities_parent_entity_id "
        "ON navigator.government_entities (parent_entity_id)"
    )
    execute(
        "CREATE INDEX ix_government_entities_supervising_entity_id "
        "ON navigator.government_entities (supervising_entity_id)"
    )
    execute(
        "CREATE INDEX ix_government_entities_verification_status "
        "ON navigator.government_entities (verification_status)"
    )
    execute(
        "CREATE INDEX ix_government_entities_next_review_at "
        "ON navigator.government_entities (next_review_at)"
    )
    execute(
        "CREATE INDEX ix_government_entities_verification_review_event_id "
        "ON navigator.government_entities (verification_review_event_id)"
    )

    execute(
        """
        CREATE TABLE navigator.platforms (
            id UUID NOT NULL,
            code TEXT NOT NULL,
            platform_type TEXT NOT NULL,
            official_name_ar TEXT NOT NULL,
            official_name_en TEXT,
            explanatory_name_en TEXT,
            responsible_entity_id UUID NOT NULL,
            valid_from DATE,
            valid_until DATE,
            verification_status TEXT DEFAULT 'discovered' NOT NULL,
            verification_review_event_id UUID,
            last_verified_at TIMESTAMPTZ,
            review_interval_days INTEGER,
            next_review_at TIMESTAMPTZ,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_platforms PRIMARY KEY (id),
            CONSTRAINT uq_platforms_code UNIQUE (code),
            CONSTRAINT ck_platforms_code_format CHECK (code ~ '^[a-z][a-z0-9_]*$'),
            CONSTRAINT ck_platforms_platform_type CHECK (
                platform_type IN (
                    'government_platform', 'official_legal_portal',
                    'official_dataset_portal'
                )
            ),
            CONSTRAINT ck_platforms_verification_status CHECK (
                verification_status IN (
                    'discovered', 'research_in_progress', 'pending_review', 'approved',
                    'rejected', 'requires_additional_review', 'blocked_by_conflict',
                    'stale', 'expired', 'inaccessible', 'superseded', 'historical'
                )
            ),
            CONSTRAINT ck_platforms_official_name_ar_nonblank
                CHECK (btrim(official_name_ar) <> ''),
            CONSTRAINT ck_platforms_valid_date_order
                CHECK (valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from),
            CONSTRAINT ck_platforms_freshness_order CHECK (
                (last_verified_at IS NULL AND review_interval_days IS NULL
                    AND next_review_at IS NULL)
                OR
                (last_verified_at IS NOT NULL AND review_interval_days IS NOT NULL
                    AND next_review_at IS NOT NULL
                    AND next_review_at =
                        last_verified_at + make_interval(days => review_interval_days))
            ),
            CONSTRAINT ck_platforms_review_interval
                CHECK (review_interval_days BETWEEN 30 AND 180),
            CONSTRAINT fk_platforms_responsible_entity
                FOREIGN KEY (responsible_entity_id)
                REFERENCES navigator.government_entities (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE INDEX ix_platforms_responsible_entity_id "
        "ON navigator.platforms (responsible_entity_id)"
    )
    execute(
        "CREATE INDEX ix_platforms_verification_status ON navigator.platforms (verification_status)"
    )
    execute("CREATE INDEX ix_platforms_next_review_at ON navigator.platforms (next_review_at)")
    execute(
        "CREATE INDEX ix_platforms_verification_review_event_id "
        "ON navigator.platforms (verification_review_event_id)"
    )

    execute(
        r"""
        CREATE TABLE navigator.domains (
            id UUID NOT NULL,
            domain_name TEXT NOT NULL,
            domain_category TEXT NOT NULL,
            responsible_entity_id UUID NOT NULL,
            platform_id UUID,
            verification_status TEXT DEFAULT 'discovered' NOT NULL,
            verification_method TEXT,
            redirect_target TEXT,
            verification_review_event_id UUID,
            last_verified_at TIMESTAMPTZ,
            review_interval_days INTEGER,
            next_review_at TIMESTAMPTZ,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_domains PRIMARY KEY (id),
            CONSTRAINT uq_domains_domain_name UNIQUE (domain_name),
            CONSTRAINT uq_domains_id_domain_name UNIQUE (id, domain_name),
            CONSTRAINT ck_domains_domain_name_format CHECK (
                domain_name = lower(domain_name)
                AND domain_name ~ '^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$'
            ),
            CONSTRAINT ck_domains_domain_name_labels
                CHECK (domain_name !~ '(^-|-$|\.\.|\.-|-\.)'),
            CONSTRAINT ck_domains_domain_category CHECK (
                domain_category IN (
                    'government_agency_domain', 'verified_government_platform',
                    'official_subdomain', 'pending_verification', 'rejected'
                )
            ),
            CONSTRAINT ck_domains_verification_status CHECK (
                verification_status IN (
                    'discovered', 'research_in_progress', 'pending_review', 'approved',
                    'rejected', 'requires_additional_review', 'blocked_by_conflict',
                    'stale', 'expired', 'inaccessible', 'superseded', 'historical'
                )
            ),
            CONSTRAINT ck_domains_approved_has_method CHECK (
                verification_status <> 'approved'
                OR (verification_method IS NOT NULL AND btrim(verification_method) <> '')
            ),
            CONSTRAINT ck_domains_freshness_order CHECK (
                (last_verified_at IS NULL AND review_interval_days IS NULL
                    AND next_review_at IS NULL)
                OR
                (last_verified_at IS NOT NULL AND review_interval_days IS NOT NULL
                    AND next_review_at IS NOT NULL
                    AND next_review_at =
                        last_verified_at + make_interval(days => review_interval_days))
            ),
            CONSTRAINT ck_domains_review_interval
                CHECK (review_interval_days BETWEEN 30 AND 180),
            CONSTRAINT fk_domains_responsible_entity
                FOREIGN KEY (responsible_entity_id)
                REFERENCES navigator.government_entities (id) ON DELETE RESTRICT,
            CONSTRAINT fk_domains_platform
                FOREIGN KEY (platform_id)
                REFERENCES navigator.platforms (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE INDEX ix_domains_responsible_entity_id ON navigator.domains (responsible_entity_id)"
    )
    execute("CREATE INDEX ix_domains_platform_id ON navigator.domains (platform_id)")
    execute(
        "CREATE INDEX ix_domains_verification_status ON navigator.domains (verification_status)"
    )
    execute("CREATE INDEX ix_domains_next_review_at ON navigator.domains (next_review_at)")
    execute(
        "CREATE INDEX ix_domains_verification_review_event_id "
        "ON navigator.domains (verification_review_event_id)"
    )

    execute(
        r"""
        CREATE TABLE navigator.sources (
            id UUID NOT NULL,
            code TEXT NOT NULL,
            responsible_entity_id UUID NOT NULL,
            domain_id UUID NOT NULL,
            canonical_url TEXT NOT NULL,
            canonical_host TEXT NOT NULL,
            source_type TEXT NOT NULL,
            official_title_ar TEXT,
            official_title_en TEXT,
            governance_purpose TEXT,
            verification_status TEXT DEFAULT 'discovered' NOT NULL,
            verification_review_event_id UUID,
            last_verified_at TIMESTAMPTZ,
            review_interval_days INTEGER,
            next_review_at TIMESTAMPTZ,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_sources PRIMARY KEY (id),
            CONSTRAINT uq_sources_code UNIQUE (code),
            CONSTRAINT uq_sources_canonical_url UNIQUE (canonical_url),
            CONSTRAINT fk_sources_domain_host
                FOREIGN KEY (domain_id, canonical_host)
                REFERENCES navigator.domains (id, domain_name) ON DELETE RESTRICT,
            CONSTRAINT fk_sources_responsible_entity
                FOREIGN KEY (responsible_entity_id)
                REFERENCES navigator.government_entities (id) ON DELETE RESTRICT,
            CONSTRAINT ck_sources_code_format CHECK (code ~ '^[a-z][a-z0-9_]*$'),
            CONSTRAINT ck_sources_source_type CHECK (
                source_type IN (
                    'entity_homepage', 'entity_about_page', 'entity_policy_page',
                    'entity_news_release', 'official_news_release',
                    'official_gazette_decision', 'official_gazette_regulation',
                    'official_guide', 'official_bulletin', 'official_dataset',
                    'platform_about_page', 'official_legal_portal',
                    'governance_document_page', 'official_service_page'
                )
            ),
            CONSTRAINT ck_sources_verification_status CHECK (
                verification_status IN (
                    'discovered', 'research_in_progress', 'pending_review', 'approved',
                    'rejected', 'requires_additional_review', 'blocked_by_conflict',
                    'stale', 'expired', 'inaccessible', 'superseded', 'historical'
                )
            ),
            CONSTRAINT ck_sources_canonical_url_https
                CHECK (canonical_url ~ '^https://'),
            CONSTRAINT ck_sources_canonical_host_format CHECK (
                canonical_host = lower(canonical_host)
                AND canonical_host ~ '^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$'
                AND canonical_host !~ '(^-|-$|\.\.|\.-|-\.)'
            ),
            CONSTRAINT ck_sources_freshness_order CHECK (
                (last_verified_at IS NULL AND review_interval_days IS NULL
                    AND next_review_at IS NULL)
                OR
                (last_verified_at IS NOT NULL AND review_interval_days IS NOT NULL
                    AND next_review_at IS NOT NULL
                    AND next_review_at =
                        last_verified_at + make_interval(days => review_interval_days))
            ),
            CONSTRAINT ck_sources_review_interval
                CHECK (review_interval_days BETWEEN 30 AND 180)
        )
        """
    )
    execute(
        "CREATE INDEX ix_sources_responsible_entity_id ON navigator.sources (responsible_entity_id)"
    )
    execute("CREATE INDEX ix_sources_domain_id ON navigator.sources (domain_id)")
    execute(
        "CREATE INDEX ix_sources_verification_status ON navigator.sources (verification_status)"
    )
    execute("CREATE INDEX ix_sources_next_review_at ON navigator.sources (next_review_at)")
    execute(
        "CREATE INDEX ix_sources_verification_review_event_id "
        "ON navigator.sources (verification_review_event_id)"
    )

    execute(
        """
        CREATE TABLE navigator.source_versions (
            id UUID NOT NULL,
            source_id UUID NOT NULL,
            version_number INTEGER NOT NULL,
            reviewed_url TEXT NOT NULL,
            resolved_url TEXT NOT NULL,
            domain_id_at_review UUID NOT NULL,
            responsible_entity_id_at_review UUID NOT NULL,
            platform_id_at_review UUID,
            retrieved_at TIMESTAMPTZ NOT NULL,
            publication_date DATE,
            effective_from DATE,
            effective_until DATE,
            content_hash TEXT,
            hash_algorithm TEXT,
            review_status TEXT DEFAULT 'pending_review' NOT NULL,
            is_current BOOLEAN DEFAULT false NOT NULL,
            verification_review_event_id UUID,
            last_verified_at TIMESTAMPTZ,
            review_interval_days INTEGER,
            next_review_at TIMESTAMPTZ,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_source_versions PRIMARY KEY (id),
            CONSTRAINT uq_source_versions_source_version
                UNIQUE (source_id, version_number),
            CONSTRAINT ck_source_versions_positive_version_number
                CHECK (version_number > 0),
            CONSTRAINT ck_source_versions_reviewed_url_https
                CHECK (reviewed_url ~ '^https://'),
            CONSTRAINT ck_source_versions_resolved_url_https
                CHECK (resolved_url ~ '^https://'),
            CONSTRAINT ck_source_versions_hash_pair CHECK (
                (content_hash IS NULL AND hash_algorithm IS NULL)
                OR (content_hash IS NOT NULL AND hash_algorithm IS NOT NULL)
            ),
            CONSTRAINT ck_source_versions_effective_date_order CHECK (
                effective_until IS NULL OR effective_from IS NULL
                OR effective_until >= effective_from
            ),
            CONSTRAINT ck_source_versions_review_status CHECK (
                review_status IN (
                    'discovered', 'research_in_progress', 'pending_review', 'approved',
                    'rejected', 'requires_additional_review', 'blocked_by_conflict',
                    'stale', 'expired', 'inaccessible', 'superseded', 'historical'
                )
            ),
            CONSTRAINT ck_source_versions_inactive_status_not_current CHECK (
                review_status NOT IN ('expired', 'superseded', 'historical')
                OR NOT is_current
            ),
            CONSTRAINT ck_source_versions_freshness_order CHECK (
                (last_verified_at IS NULL AND review_interval_days IS NULL
                    AND next_review_at IS NULL)
                OR
                (last_verified_at IS NOT NULL AND review_interval_days IS NOT NULL
                    AND next_review_at IS NOT NULL
                    AND next_review_at =
                        last_verified_at + make_interval(days => review_interval_days))
            ),
            CONSTRAINT ck_source_versions_review_interval
                CHECK (review_interval_days BETWEEN 30 AND 180),
            CONSTRAINT fk_source_versions_source
                FOREIGN KEY (source_id)
                REFERENCES navigator.sources (id) ON DELETE RESTRICT,
            CONSTRAINT fk_source_versions_domain_at_review
                FOREIGN KEY (domain_id_at_review)
                REFERENCES navigator.domains (id) ON DELETE RESTRICT,
            CONSTRAINT fk_source_versions_entity_at_review
                FOREIGN KEY (responsible_entity_id_at_review)
                REFERENCES navigator.government_entities (id) ON DELETE RESTRICT,
            CONSTRAINT fk_source_versions_platform_at_review
                FOREIGN KEY (platform_id_at_review)
                REFERENCES navigator.platforms (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE UNIQUE INDEX uq_source_versions_one_current "
        "ON navigator.source_versions (source_id) WHERE is_current"
    )
    execute(
        "CREATE INDEX ix_source_versions_review_status ON navigator.source_versions (review_status)"
    )
    execute(
        "CREATE INDEX ix_source_versions_next_review_at "
        "ON navigator.source_versions (next_review_at)"
    )
    execute(
        "CREATE INDEX ix_source_versions_domain_id_at_review "
        "ON navigator.source_versions (domain_id_at_review)"
    )
    execute(
        "CREATE INDEX ix_source_versions_responsible_entity_id_at_review "
        "ON navigator.source_versions (responsible_entity_id_at_review)"
    )
    execute(
        "CREATE INDEX ix_source_versions_platform_id_at_review "
        "ON navigator.source_versions (platform_id_at_review)"
    )
    execute(
        "CREATE INDEX ix_source_versions_verification_review_event_id "
        "ON navigator.source_versions (verification_review_event_id)"
    )

    execute(
        """
        CREATE TABLE navigator.business_activities (
            id UUID NOT NULL,
            code TEXT NOT NULL,
            name_ar TEXT NOT NULL,
            name_en TEXT NOT NULL,
            is_active BOOLEAN DEFAULT false NOT NULL,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_business_activities PRIMARY KEY (id),
            CONSTRAINT uq_business_activities_code UNIQUE (code),
            CONSTRAINT ck_business_activities_code_format
                CHECK (code ~ '^[a-z][a-z0-9_]*$'),
            CONSTRAINT ck_business_activities_name_ar_nonblank
                CHECK (btrim(name_ar) <> ''),
            CONSTRAINT ck_business_activities_name_en_nonblank
                CHECK (btrim(name_en) <> '')
        )
        """
    )
    execute(
        "CREATE INDEX ix_business_activities_is_active ON navigator.business_activities (is_active)"
    )

    execute(
        """
        CREATE TABLE navigator.supported_locations (
            id UUID NOT NULL,
            code TEXT NOT NULL,
            location_type TEXT NOT NULL,
            name_ar TEXT NOT NULL,
            name_en TEXT NOT NULL,
            country_code TEXT DEFAULT 'SA' NOT NULL,
            is_pilot BOOLEAN DEFAULT false NOT NULL,
            is_active BOOLEAN DEFAULT false NOT NULL,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_supported_locations PRIMARY KEY (id),
            CONSTRAINT uq_supported_locations_code UNIQUE (code),
            CONSTRAINT ck_supported_locations_code_format
                CHECK (code ~ '^[a-z][a-z0-9_]*$'),
            CONSTRAINT ck_supported_locations_location_type
                CHECK (location_type IN ('city')),
            CONSTRAINT ck_supported_locations_saudi_country CHECK (country_code = 'SA'),
            CONSTRAINT ck_supported_locations_name_ar_nonblank
                CHECK (btrim(name_ar) <> ''),
            CONSTRAINT ck_supported_locations_name_en_nonblank
                CHECK (btrim(name_en) <> '')
        )
        """
    )
    execute(
        "CREATE INDEX ix_supported_locations_active_pilot "
        "ON navigator.supported_locations (is_active, is_pilot)"
    )

    execute(
        """
        CREATE TABLE navigator.research_events (
            id UUID NOT NULL,
            event_code TEXT NOT NULL,
            government_entity_id UUID,
            platform_id UUID,
            domain_id UUID,
            source_id UUID,
            source_version_id UUID,
            research_status TEXT NOT NULL,
            recommendation TEXT,
            researched_at TIMESTAMPTZ NOT NULL,
            researched_by_role TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_research_events PRIMARY KEY (id),
            CONSTRAINT uq_research_events_event_code UNIQUE (event_code),
            CONSTRAINT ck_research_events_event_code_format
                CHECK (event_code ~ '^[a-z][a-z0-9_]*$'),
            CONSTRAINT ck_research_events_exactly_one_target CHECK (
                num_nonnulls(
                    government_entity_id, platform_id, domain_id, source_id,
                    source_version_id
                ) = 1
            ),
            CONSTRAINT ck_research_events_research_status CHECK (
                research_status IN (
                    'in_progress', 'completed', 'blocked',
                    'requires_additional_research'
                )
            ),
            CONSTRAINT ck_research_events_recommendation CHECK (
                recommendation IS NULL OR recommendation IN (
                    'approve', 'reject', 'requires_additional_review',
                    'blocked_by_conflict'
                )
            ),
            CONSTRAINT ck_research_events_researcher_role
                CHECK (researched_by_role ~ '^[a-z][a-z0-9_]*$'),
            CONSTRAINT fk_research_events_government_entity
                FOREIGN KEY (government_entity_id)
                REFERENCES navigator.government_entities (id) ON DELETE RESTRICT,
            CONSTRAINT fk_research_events_platform
                FOREIGN KEY (platform_id)
                REFERENCES navigator.platforms (id) ON DELETE RESTRICT,
            CONSTRAINT fk_research_events_domain
                FOREIGN KEY (domain_id)
                REFERENCES navigator.domains (id) ON DELETE RESTRICT,
            CONSTRAINT fk_research_events_source
                FOREIGN KEY (source_id)
                REFERENCES navigator.sources (id) ON DELETE RESTRICT,
            CONSTRAINT fk_research_events_source_version
                FOREIGN KEY (source_version_id)
                REFERENCES navigator.source_versions (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE INDEX ix_research_events_government_entity_id "
        "ON navigator.research_events (government_entity_id)"
    )
    execute(
        "CREATE INDEX ix_research_events_platform_id ON navigator.research_events (platform_id)"
    )
    execute("CREATE INDEX ix_research_events_domain_id ON navigator.research_events (domain_id)")
    execute("CREATE INDEX ix_research_events_source_id ON navigator.research_events (source_id)")
    execute(
        "CREATE INDEX ix_research_events_source_version_id "
        "ON navigator.research_events (source_version_id)"
    )
    execute(
        "CREATE INDEX ix_research_events_research_status "
        "ON navigator.research_events (research_status)"
    )

    execute(
        """
        CREATE TABLE navigator.research_event_evidence (
            research_event_id UUID NOT NULL,
            source_version_id UUID NOT NULL,
            evidence_role TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_research_event_evidence
                PRIMARY KEY (research_event_id, source_version_id),
            CONSTRAINT ck_research_event_evidence_evidence_role CHECK (
                evidence_role IN (
                    'primary', 'supporting', 'conflicting', 'historical', 'context'
                )
            ),
            CONSTRAINT fk_research_event_evidence_research_event
                FOREIGN KEY (research_event_id)
                REFERENCES navigator.research_events (id) ON DELETE RESTRICT,
            CONSTRAINT fk_research_event_evidence_source_version
                FOREIGN KEY (source_version_id)
                REFERENCES navigator.source_versions (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE INDEX ix_research_event_evidence_source_version_id "
        "ON navigator.research_event_evidence (source_version_id)"
    )

    execute(
        """
        CREATE TABLE navigator.review_events (
            id UUID NOT NULL,
            research_event_id UUID NOT NULL,
            decision TEXT NOT NULL,
            reviewed_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            reviewed_by_role TEXT NOT NULL,
            independent_review BOOLEAN DEFAULT false NOT NULL,
            reason TEXT NOT NULL,
            authorized_review_interval_days INTEGER,
            review_interval_reason TEXT,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_review_events PRIMARY KEY (id),
            CONSTRAINT ck_review_events_decision CHECK (
                decision IN (
                    'approved', 'rejected', 'returned_for_research',
                    'requires_additional_review', 'blocked_by_conflict',
                    'marked_stale', 'marked_inaccessible', 'marked_superseded',
                    'marked_historical', 'marked_expired'
                )
            ),
            CONSTRAINT ck_review_events_reviewer_role
                CHECK (reviewed_by_role ~ '^[a-z][a-z0-9_]*$'),
            CONSTRAINT ck_review_events_reason_nonblank CHECK (btrim(reason) <> ''),
            CONSTRAINT ck_review_events_authorized_review_interval CHECK (
                authorized_review_interval_days IS NULL
                OR authorized_review_interval_days BETWEEN 30 AND 180
            ),
            CONSTRAINT ck_review_events_review_interval_requires_approval CHECK (
                authorized_review_interval_days IS NULL OR decision = 'approved'
            ),
            CONSTRAINT ck_review_events_review_interval_justification CHECK (
                (authorized_review_interval_days IS NULL
                    AND review_interval_reason IS NULL)
                OR
                (authorized_review_interval_days IS NOT NULL
                    AND review_interval_reason IS NOT NULL
                    AND btrim(review_interval_reason) <> '')
            ),
            CONSTRAINT fk_review_events_research_event
                FOREIGN KEY (research_event_id)
                REFERENCES navigator.research_events (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE INDEX ix_review_events_research_event_id "
        "ON navigator.review_events (research_event_id)"
    )
    execute(
        "CREATE INDEX ix_review_events_decision_reviewed_at "
        "ON navigator.review_events (decision, reviewed_at)"
    )

    for table_name in (
        "government_entities",
        "platforms",
        "domains",
        "sources",
        "source_versions",
    ):
        execute(
            f"""
            ALTER TABLE navigator.{table_name}
            ADD CONSTRAINT fk_{table_name}_verification_review
            FOREIGN KEY (verification_review_event_id)
            REFERENCES navigator.review_events (id) ON DELETE RESTRICT
            """
        )

    execute(
        """
        CREATE FUNCTION navigator.url_host(value TEXT)
        RETURNS TEXT
        LANGUAGE sql
        IMMUTABLE
        STRICT
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
            SELECT lower(split_part(split_part(value, '://', 2), '/', 1))
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.set_updated_at_on_change()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        BEGIN
            IF NEW.created_at IS DISTINCT FROM OLD.created_at THEN
                RAISE EXCEPTION 'created_at is immutable';
            END IF;
            IF (pg_catalog.to_jsonb(NEW) - 'created_at' - 'updated_at')
                IS DISTINCT FROM
               (pg_catalog.to_jsonb(OLD) - 'created_at' - 'updated_at')
            THEN
                NEW.updated_at := pg_catalog.clock_timestamp();
            ELSE
                NEW.updated_at := OLD.updated_at;
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_review_event()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            target_research_status TEXT;
            target_recommendation TEXT;
            target_researched_at TIMESTAMPTZ;
        BEGIN
            NEW.created_at := pg_catalog.clock_timestamp();
            IF NEW.reviewed_at IS NULL THEN
                NEW.reviewed_at := NEW.created_at;
            END IF;
            IF NEW.reviewed_at > NEW.created_at THEN
                RAISE EXCEPTION 'future review timestamps are prohibited';
            END IF;

            SELECT research_status, recommendation, researched_at
            INTO target_research_status, target_recommendation, target_researched_at
            FROM navigator.research_events
            WHERE id = NEW.research_event_id;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'review requires an existing research event';
            END IF;
            IF NEW.reviewed_at < target_researched_at THEN
                RAISE EXCEPTION 'review cannot predate its research event';
            END IF;
            IF NEW.decision = 'approved' THEN
                IF target_research_status <> 'completed'
                    OR target_recommendation <> 'approve'
                THEN
                    RAISE EXCEPTION 'approval requires completed research recommending approval';
                END IF;
                IF NOT EXISTS (
                    SELECT 1
                    FROM navigator.research_event_evidence
                    WHERE research_event_id = NEW.research_event_id
                ) THEN
                    RAISE EXCEPTION 'approval requires recorded source-version evidence';
                END IF;
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.apply_verification_review()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            new_status TEXT;
            old_status TEXT;
            review_decision TEXT;
            review_time TIMESTAMPTZ;
            authorized_interval INTEGER;
            target_matches BOOLEAN;
            old_review_time TIMESTAMPTZ;
            identity_changed BOOLEAN := false;
        BEGIN
            new_status := COALESCE(
                pg_catalog.to_jsonb(NEW)->>'verification_status',
                pg_catalog.to_jsonb(NEW)->>'review_status'
            );

            IF TG_OP = 'INSERT' THEN
                IF NEW.verification_review_event_id IS NOT NULL
                    OR NEW.last_verified_at IS NOT NULL
                    OR NEW.review_interval_days IS NOT NULL
                    OR NEW.next_review_at IS NOT NULL
                    OR new_status NOT IN (
                        'discovered', 'research_in_progress', 'pending_review'
                    )
                    OR (
                        TG_TABLE_NAME = 'source_versions'
                        AND COALESCE((pg_catalog.to_jsonb(NEW)->>'is_current')::boolean, false)
                    )
                THEN
                    RAISE EXCEPTION 'governed records begin in an unverified workflow state';
                END IF;
                RETURN NEW;
            END IF;

            old_status := COALESCE(
                pg_catalog.to_jsonb(OLD)->>'verification_status',
                pg_catalog.to_jsonb(OLD)->>'review_status'
            );

            identity_changed := CASE TG_TABLE_NAME
                WHEN 'government_entities' THEN
                    (pg_catalog.to_jsonb(NEW)
                        - 'verification_status' - 'verification_review_event_id'
                        - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                        - 'notes' - 'updated_at')
                    IS DISTINCT FROM
                    (pg_catalog.to_jsonb(OLD)
                        - 'verification_status' - 'verification_review_event_id'
                        - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                        - 'notes' - 'updated_at')
                WHEN 'platforms' THEN
                    (pg_catalog.to_jsonb(NEW)
                        - 'verification_status' - 'verification_review_event_id'
                        - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                        - 'notes' - 'updated_at')
                    IS DISTINCT FROM
                    (pg_catalog.to_jsonb(OLD)
                        - 'verification_status' - 'verification_review_event_id'
                        - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                        - 'notes' - 'updated_at')
                WHEN 'domains' THEN
                    (pg_catalog.to_jsonb(NEW)
                        - 'verification_status' - 'verification_review_event_id'
                        - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                        - 'notes' - 'updated_at')
                    IS DISTINCT FROM
                    (pg_catalog.to_jsonb(OLD)
                        - 'verification_status' - 'verification_review_event_id'
                        - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                        - 'notes' - 'updated_at')
                WHEN 'sources' THEN
                    (pg_catalog.to_jsonb(NEW)
                        - 'verification_status' - 'verification_review_event_id'
                        - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                        - 'notes' - 'updated_at')
                    IS DISTINCT FROM
                    (pg_catalog.to_jsonb(OLD)
                        - 'verification_status' - 'verification_review_event_id'
                        - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                        - 'notes' - 'updated_at')
                ELSE false
            END;

            IF NEW.last_verified_at IS DISTINCT FROM OLD.last_verified_at
                OR NEW.review_interval_days IS DISTINCT FROM OLD.review_interval_days
                OR NEW.next_review_at IS DISTINCT FROM OLD.next_review_at
            THEN
                RAISE EXCEPTION 'verification dates are database derived';
            END IF;

            IF NEW.verification_review_event_id IS NOT DISTINCT FROM
                OLD.verification_review_event_id
            THEN
                IF identity_changed THEN
                    RAISE EXCEPTION 'reviewed identity changes require a new review event';
                END IF;
                IF TG_TABLE_NAME = 'source_versions'
                    AND NOT COALESCE(
                        (pg_catalog.to_jsonb(OLD)->>'is_current')::boolean,
                        false
                    )
                    AND COALESCE(
                        (pg_catalog.to_jsonb(NEW)->>'is_current')::boolean,
                        false
                    )
                THEN
                    RAISE EXCEPTION 'restoring a source version requires a new review event';
                END IF;
                IF new_status IS DISTINCT FROM old_status THEN
                    IF OLD.verification_review_event_id IS NULL
                        AND old_status <> 'approved'
                        AND new_status IN (
                            'discovered', 'research_in_progress', 'pending_review'
                        )
                    THEN
                        RETURN NEW;
                    END IF;
                    RAISE EXCEPTION 'status changes require a new review event';
                END IF;
                RETURN NEW;
            END IF;

            IF NEW.verification_review_event_id IS NULL THEN
                RAISE EXCEPTION 'verification review cannot be cleared';
            END IF;

            SELECT
                rv.decision,
                rv.reviewed_at,
                rv.authorized_review_interval_days,
                CASE TG_TABLE_NAME
                    WHEN 'government_entities' THEN re.government_entity_id = NEW.id
                    WHEN 'platforms' THEN re.platform_id = NEW.id
                    WHEN 'domains' THEN re.domain_id = NEW.id
                    WHEN 'sources' THEN re.source_id = NEW.id
                    WHEN 'source_versions' THEN re.source_version_id = NEW.id
                    ELSE false
                END
            INTO review_decision, review_time, authorized_interval, target_matches
            FROM navigator.review_events AS rv
            JOIN navigator.research_events AS re ON re.id = rv.research_event_id
            WHERE rv.id = NEW.verification_review_event_id;

            IF NOT FOUND OR target_matches IS DISTINCT FROM TRUE THEN
                RAISE EXCEPTION 'review event does not target this record';
            END IF;
            IF review_time > pg_catalog.clock_timestamp() THEN
                RAISE EXCEPTION 'future review timestamps are prohibited';
            END IF;
            IF target_matches IS DISTINCT FROM TRUE THEN
                RAISE EXCEPTION 'review event does not target this record';
            END IF;
            IF OLD.verification_review_event_id IS NOT NULL THEN
                SELECT reviewed_at
                INTO old_review_time
                FROM navigator.review_events
                WHERE id = OLD.verification_review_event_id;
                IF review_time <= old_review_time THEN
                    RAISE EXCEPTION 'replacement review must be newer';
                END IF;
            END IF;
            IF new_status = 'approved' AND review_decision <> 'approved' THEN
                RAISE EXCEPTION 'approved status requires an approved review';
            END IF;
            IF new_status = 'rejected' AND review_decision <> 'rejected' THEN
                RAISE EXCEPTION 'rejected status requires a rejected review';
            END IF;
            IF new_status = 'requires_additional_review'
                AND review_decision <> 'requires_additional_review'
            THEN
                RAISE EXCEPTION 'status and review decision do not match';
            END IF;
            IF new_status = 'blocked_by_conflict'
                AND review_decision <> 'blocked_by_conflict'
            THEN
                RAISE EXCEPTION 'status and review decision do not match';
            END IF;
            IF new_status = 'stale' AND review_decision <> 'marked_stale' THEN
                RAISE EXCEPTION 'stale status requires a reviewed decision';
            END IF;
            IF new_status = 'inaccessible'
                AND review_decision <> 'marked_inaccessible'
            THEN
                RAISE EXCEPTION 'inaccessible status requires a reviewed decision';
            END IF;
            IF new_status = 'superseded'
                AND review_decision <> 'marked_superseded'
            THEN
                RAISE EXCEPTION 'superseded status requires a reviewed decision';
            END IF;
            IF new_status = 'historical'
                AND review_decision <> 'marked_historical'
            THEN
                RAISE EXCEPTION 'historical status requires a reviewed decision';
            END IF;
            IF new_status = 'expired' AND review_decision <> 'marked_expired' THEN
                RAISE EXCEPTION 'expired status requires a reviewed decision';
            END IF;

            IF new_status = 'approved' THEN
                IF OLD.last_verified_at IS NOT NULL
                    AND review_time <= OLD.last_verified_at
                THEN
                    RAISE EXCEPTION 'renewal review must be newer';
                END IF;
                NEW.last_verified_at := review_time;
                NEW.review_interval_days := COALESCE(authorized_interval, 90);
                NEW.next_review_at :=
                    review_time
                    + pg_catalog.make_interval(
                        days => COALESCE(authorized_interval, 90)
                    );
            ELSE
                NEW.last_verified_at := NULL;
                NEW.review_interval_days := NULL;
                NEW.next_review_at := NULL;
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_source_identity()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        BEGIN
            IF navigator.url_host(NEW.canonical_url) <> NEW.canonical_host THEN
                RAISE EXCEPTION 'source URL host does not match approved domain';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_source_version_snapshot()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            source_domain UUID;
            source_entity UUID;
            source_host TEXT;
            domain_platform UUID;
            domain_name_value TEXT;
        BEGIN
            SELECT s.domain_id, s.responsible_entity_id, s.canonical_host
            INTO source_domain, source_entity, source_host
            FROM navigator.sources AS s
            WHERE s.id = NEW.source_id;

            SELECT d.platform_id, d.domain_name
            INTO domain_platform, domain_name_value
            FROM navigator.domains AS d
            WHERE d.id = NEW.domain_id_at_review;

            IF source_domain IS DISTINCT FROM NEW.domain_id_at_review
                OR source_entity IS DISTINCT FROM NEW.responsible_entity_id_at_review
                OR domain_platform IS DISTINCT FROM NEW.platform_id_at_review
                OR navigator.url_host(NEW.reviewed_url) IS DISTINCT FROM source_host
                OR NEW.reviewed_url IS DISTINCT FROM (
                    SELECT canonical_url
                    FROM navigator.sources
                    WHERE id = NEW.source_id
                )
                OR navigator.url_host(NEW.resolved_url) IS DISTINCT FROM domain_name_value
            THEN
                RAISE EXCEPTION 'source snapshot context is inconsistent';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.guard_source_version_snapshot()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        BEGIN
            IF (
                pg_catalog.to_jsonb(NEW)
                    - 'review_status' - 'is_current' - 'verification_review_event_id'
                    - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                    - 'notes' - 'updated_at'
            ) IS DISTINCT FROM (
                pg_catalog.to_jsonb(OLD)
                    - 'review_status' - 'is_current' - 'verification_review_event_id'
                    - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                    - 'notes' - 'updated_at'
            ) THEN
                RAISE EXCEPTION 'source snapshot evidence is immutable';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.guard_append_only()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        BEGIN
            RAISE EXCEPTION 'governance history is append only';
        END
        $$
        """
    )

    mutable_tables = (
        "government_entities",
        "platforms",
        "domains",
        "sources",
        "source_versions",
        "business_activities",
        "supported_locations",
    )
    for table_name in mutable_tables:
        execute(
            f"""
            CREATE TRIGGER trg_90_set_updated_at
            BEFORE UPDATE ON navigator.{table_name}
            FOR EACH ROW EXECUTE FUNCTION navigator.set_updated_at_on_change()
            """
        )

    for table_name in (
        "government_entities",
        "platforms",
        "domains",
        "sources",
        "source_versions",
    ):
        execute(
            f"""
            CREATE TRIGGER trg_20_apply_verification_review
            BEFORE INSERT OR UPDATE ON navigator.{table_name}
            FOR EACH ROW EXECUTE FUNCTION navigator.apply_verification_review()
            """
        )

    execute(
        """
        CREATE TRIGGER trg_05_validate_review_event
        BEFORE INSERT ON navigator.review_events
        FOR EACH ROW EXECUTE FUNCTION navigator.validate_review_event()
        """
    )

    execute(
        """
        CREATE TRIGGER trg_10_validate_source_identity
        BEFORE INSERT OR UPDATE OF canonical_url, canonical_host, domain_id
        ON navigator.sources
        FOR EACH ROW EXECUTE FUNCTION navigator.validate_source_identity()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_10_validate_source_version_snapshot
        BEFORE INSERT ON navigator.source_versions
        FOR EACH ROW EXECUTE FUNCTION navigator.validate_source_version_snapshot()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_10_guard_source_version_snapshot
        BEFORE UPDATE ON navigator.source_versions
        FOR EACH ROW EXECUTE FUNCTION navigator.guard_source_version_snapshot()
        """
    )

    for table_name in ("research_events", "research_event_evidence", "review_events"):
        execute(
            f"""
            CREATE TRIGGER trg_10_append_only
            BEFORE UPDATE OR DELETE ON navigator.{table_name}
            FOR EACH ROW EXECUTE FUNCTION navigator.guard_append_only()
            """
        )


def downgrade() -> None:
    """Remove migration-owned objects while retaining Alembic's navigator schema."""
    execute("DROP TRIGGER IF EXISTS trg_05_validate_review_event ON navigator.review_events")
    for table_name in ("research_events", "research_event_evidence", "review_events"):
        execute(f"DROP TRIGGER IF EXISTS trg_10_append_only ON navigator.{table_name}")

    execute(
        "DROP TRIGGER IF EXISTS trg_10_guard_source_version_snapshot ON navigator.source_versions"
    )
    execute(
        "DROP TRIGGER IF EXISTS trg_10_validate_source_version_snapshot "
        "ON navigator.source_versions"
    )
    execute("DROP TRIGGER IF EXISTS trg_10_validate_source_identity ON navigator.sources")

    for table_name in (
        "government_entities",
        "platforms",
        "domains",
        "sources",
        "source_versions",
    ):
        execute(
            f"DROP TRIGGER IF EXISTS trg_20_apply_verification_review ON navigator.{table_name}"
        )

    for table_name in (
        "government_entities",
        "platforms",
        "domains",
        "sources",
        "source_versions",
        "business_activities",
        "supported_locations",
    ):
        execute(f"DROP TRIGGER IF EXISTS trg_90_set_updated_at ON navigator.{table_name}")

    execute("DROP FUNCTION navigator.guard_append_only()")
    execute("DROP FUNCTION navigator.guard_source_version_snapshot()")
    execute("DROP FUNCTION navigator.validate_source_version_snapshot()")
    execute("DROP FUNCTION navigator.validate_source_identity()")
    execute("DROP FUNCTION navigator.apply_verification_review()")
    execute("DROP FUNCTION navigator.validate_review_event()")
    execute("DROP FUNCTION navigator.set_updated_at_on_change()")
    execute("DROP FUNCTION navigator.url_host(TEXT)")

    for table_name in (
        "government_entities",
        "platforms",
        "domains",
        "sources",
        "source_versions",
    ):
        execute(
            f"ALTER TABLE navigator.{table_name} "
            f"DROP CONSTRAINT fk_{table_name}_verification_review"
        )

    execute("DROP TABLE navigator.review_events")
    execute("DROP TABLE navigator.research_event_evidence")
    execute("DROP TABLE navigator.research_events")
    execute("DROP TABLE navigator.supported_locations")
    execute("DROP TABLE navigator.business_activities")
    execute("DROP TABLE navigator.source_versions")
    execute("DROP TABLE navigator.sources")
    execute("DROP TABLE navigator.domains")
    execute("DROP TABLE navigator.platforms")
    execute("DROP TABLE navigator.government_entities")
