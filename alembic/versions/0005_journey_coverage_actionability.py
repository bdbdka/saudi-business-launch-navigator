"""Add governed journey coverage, routing, actionability, and release controls.

Revision ID: 0005_coverage_actionability
Revises: 0004_deterministic_conditions
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_coverage_actionability"
down_revision: str | None = "0004_deterministic_conditions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create empty governed structures; this migration inserts no content."""
    execute = op.execute

    execute(
        """
        CREATE TABLE navigator.journey_topics (
            id UUID NOT NULL,
            code TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_journey_topics PRIMARY KEY (id),
            CONSTRAINT uq_journey_topics_code UNIQUE (code),
            CONSTRAINT ck_journey_topics_code_format
                CHECK (code ~ '^[a-z][a-z0-9_]*$')
        )
        """
    )
    execute(
        """
        CREATE TABLE navigator.journey_topic_versions (
            id UUID NOT NULL,
            journey_topic_id UUID NOT NULL,
            activity_id UUID NOT NULL,
            version_number INTEGER NOT NULL,
            title_ar TEXT NOT NULL,
            title_en TEXT,
            coverage_state TEXT NOT NULL,
            limitation_type TEXT,
            verified_summary_ar TEXT,
            verified_summary_en TEXT,
            limitation_summary_ar TEXT,
            limitation_summary_en TEXT,
            what_to_verify_ar TEXT,
            what_to_verify_en TEXT,
            verification_status TEXT DEFAULT 'pending_source_verification' NOT NULL,
            approval_review_event_id UUID,
            last_verified_at TIMESTAMPTZ,
            review_interval_days INTEGER,
            next_review_at TIMESTAMPTZ,
            effective_from DATE,
            effective_until DATE,
            is_current BOOLEAN DEFAULT false NOT NULL,
            supersedes_journey_topic_version_id UUID,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_journey_topic_versions PRIMARY KEY (id),
            CONSTRAINT uq_journey_topic_versions_topic_activity_version
                UNIQUE (journey_topic_id, activity_id, version_number),
            CONSTRAINT uq_journey_topic_versions_supersedes
                UNIQUE (supersedes_journey_topic_version_id),
            CONSTRAINT ck_journey_topic_versions_positive_version_number
                CHECK (version_number > 0),
            CONSTRAINT ck_journey_topic_versions_title_ar_nonblank
                CHECK (btrim(title_ar) <> ''),
            CONSTRAINT ck_journey_topic_versions_coverage_state CHECK (
                coverage_state IN (
                    'VERIFIED', 'PARTIALLY_VERIFIED',
                    'REQUIRES_OFFICIAL_CONFIRMATION', 'UNRESOLVED', 'NOT_RESEARCHED'
                )
            ),
            CONSTRAINT ck_journey_topic_versions_limitation_type CHECK (
                limitation_type IS NULL OR limitation_type IN (
                    'insufficient_evidence', 'material_conflict',
                    'unresolved_supersession', 'case_confirmation'
                )
            ),
            CONSTRAINT ck_journey_topic_versions_verification_status CHECK (
                verification_status IN (
                    'pending_source_verification', 'pending_review', 'approved', 'rejected',
                    'conflicting', 'stale', 'expired', 'superseded', 'historical'
                )
            ),
            CONSTRAINT ck_journey_topic_versions_effective_date_order CHECK (
                effective_until IS NULL OR effective_from IS NULL
                OR effective_until >= effective_from
            ),
            CONSTRAINT ck_journey_topic_versions_freshness_order CHECK (
                (last_verified_at IS NULL AND review_interval_days IS NULL
                    AND next_review_at IS NULL)
                OR (last_verified_at IS NOT NULL AND review_interval_days IS NOT NULL
                    AND next_review_at IS NOT NULL
                    AND next_review_at = last_verified_at
                        + make_interval(days => review_interval_days))
            ),
            CONSTRAINT ck_journey_topic_versions_review_interval CHECK (
                review_interval_days IS NULL OR review_interval_days BETWEEN 30 AND 180
            ),
            CONSTRAINT ck_journey_topic_versions_approved_has_review CHECK (
                verification_status <> 'approved'
                OR (approval_review_event_id IS NOT NULL AND last_verified_at IS NOT NULL)
            ),
            CONSTRAINT ck_journey_topic_versions_current_is_approved CHECK (
                NOT is_current OR verification_status = 'approved'
            ),
            CONSTRAINT ck_journey_topic_versions_inactive_status_not_current CHECK (
                verification_status NOT IN ('expired', 'superseded', 'historical')
                OR NOT is_current
            ),
            CONSTRAINT ck_journey_topic_versions_not_self_superseding CHECK (
                supersedes_journey_topic_version_id IS DISTINCT FROM id
            ),
            CONSTRAINT ck_journey_topic_versions_state_content CHECK (
                (coverage_state <> 'VERIFIED'
                    OR (verified_summary_ar IS NOT NULL
                        AND btrim(verified_summary_ar) <> ''))
                AND (coverage_state <> 'PARTIALLY_VERIFIED'
                    OR (verified_summary_ar IS NOT NULL
                        AND btrim(verified_summary_ar) <> ''
                        AND limitation_type IS NOT NULL
                        AND limitation_summary_ar IS NOT NULL
                        AND btrim(limitation_summary_ar) <> ''))
                AND (coverage_state <> 'REQUIRES_OFFICIAL_CONFIRMATION'
                    OR (limitation_type IS NOT NULL
                        AND limitation_summary_ar IS NOT NULL
                        AND btrim(limitation_summary_ar) <> ''
                        AND what_to_verify_ar IS NOT NULL
                        AND btrim(what_to_verify_ar) <> ''))
                AND (coverage_state <> 'UNRESOLVED'
                    OR (limitation_type IN (
                            'insufficient_evidence', 'material_conflict',
                            'unresolved_supersession'
                        )
                        AND limitation_summary_ar IS NOT NULL
                        AND btrim(limitation_summary_ar) <> ''))
            ),
            CONSTRAINT ck_journey_topic_versions_not_researched_internal_only CHECK (
                coverage_state <> 'NOT_RESEARCHED'
                OR (verification_status <> 'approved'
                    AND approval_review_event_id IS NULL AND NOT is_current)
            ),
            CONSTRAINT fk_journey_topic_versions_topic FOREIGN KEY (journey_topic_id)
                REFERENCES navigator.journey_topics (id) ON DELETE RESTRICT,
            CONSTRAINT fk_journey_topic_versions_activity FOREIGN KEY (activity_id)
                REFERENCES navigator.business_activities (id) ON DELETE RESTRICT,
            CONSTRAINT fk_journey_topic_versions_approval_review
                FOREIGN KEY (approval_review_event_id)
                REFERENCES navigator.review_events (id) ON DELETE RESTRICT,
            CONSTRAINT fk_journey_topic_versions_supersedes
                FOREIGN KEY (supersedes_journey_topic_version_id)
                REFERENCES navigator.journey_topic_versions (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE UNIQUE INDEX uq_journey_topic_versions_one_current "
        "ON navigator.journey_topic_versions (journey_topic_id, activity_id) "
        "WHERE is_current"
    )
    for index_sql in (
        "CREATE INDEX ix_journey_topic_versions_activity_id "
        "ON navigator.journey_topic_versions (activity_id)",
        "CREATE INDEX ix_journey_topic_versions_verification_status "
        "ON navigator.journey_topic_versions (verification_status)",
        "CREATE INDEX ix_journey_topic_versions_next_review_at "
        "ON navigator.journey_topic_versions (next_review_at)",
        "CREATE INDEX ix_journey_topic_versions_approval_review_event_id "
        "ON navigator.journey_topic_versions (approval_review_event_id)",
    ):
        execute(index_sql)

    execute(
        """
        CREATE TABLE navigator.journey_topic_evidence (
            id UUID NOT NULL,
            journey_topic_version_id UUID NOT NULL,
            source_version_id UUID NOT NULL,
            evidence_role TEXT NOT NULL,
            official_excerpt_ar TEXT,
            official_excerpt_en TEXT,
            excerpt_locator TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_journey_topic_evidence PRIMARY KEY (id),
            CONSTRAINT uq_journey_topic_evidence_topic_source
                UNIQUE (journey_topic_version_id, source_version_id),
            CONSTRAINT uq_journey_topic_evidence_id_topic
                UNIQUE (id, journey_topic_version_id),
            CONSTRAINT ck_journey_topic_evidence_evidence_role CHECK (
                evidence_role IN ('primary', 'supporting', 'clarifying',
                                  'conflicting', 'historical')
            ),
            CONSTRAINT ck_journey_topic_evidence_relied_evidence_complete CHECK (
                evidence_role = 'historical'
                OR (official_excerpt_ar IS NOT NULL
                    AND btrim(official_excerpt_ar) <> ''
                    AND excerpt_locator IS NOT NULL
                    AND btrim(excerpt_locator) <> '')
            ),
            CONSTRAINT fk_journey_topic_evidence_topic_version
                FOREIGN KEY (journey_topic_version_id)
                REFERENCES navigator.journey_topic_versions (id) ON DELETE RESTRICT,
            CONSTRAINT fk_journey_topic_evidence_source_version
                FOREIGN KEY (source_version_id)
                REFERENCES navigator.source_versions (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE UNIQUE INDEX uq_journey_topic_evidence_one_primary "
        "ON navigator.journey_topic_evidence (journey_topic_version_id) "
        "WHERE evidence_role = 'primary'"
    )
    execute(
        "CREATE INDEX ix_journey_topic_evidence_source_version_id "
        "ON navigator.journey_topic_evidence (source_version_id)"
    )

    execute(
        """
        CREATE TABLE navigator.journey_topic_requirement_links (
            journey_topic_version_id UUID NOT NULL,
            requirement_version_id UUID NOT NULL,
            link_role TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_journey_topic_requirement_links
                PRIMARY KEY (journey_topic_version_id, requirement_version_id),
            CONSTRAINT ck_journey_topic_requirement_links_link_role CHECK (
                link_role IN ('covered_by', 'partially_covered_by', 'related')
            ),
            CONSTRAINT fk_journey_topic_requirement_links_topic_version
                FOREIGN KEY (journey_topic_version_id)
                REFERENCES navigator.journey_topic_versions (id) ON DELETE RESTRICT,
            CONSTRAINT fk_journey_topic_requirement_links_requirement_version
                FOREIGN KEY (requirement_version_id)
                REFERENCES navigator.requirement_versions (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE INDEX ix_journey_topic_requirement_links_requirement_version_id "
        "ON navigator.journey_topic_requirement_links (requirement_version_id)"
    )

    execute(
        """
        CREATE TABLE navigator.journey_topic_fact_links (
            journey_topic_version_id UUID NOT NULL,
            fact_definition_id UUID NOT NULL,
            input_role TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_journey_topic_fact_links
                PRIMARY KEY (journey_topic_version_id, fact_definition_id),
            CONSTRAINT ck_journey_topic_fact_links_input_role CHECK (
                input_role IN ('navigation', 'confirmation')
            ),
            CONSTRAINT fk_journey_topic_fact_links_topic_version
                FOREIGN KEY (journey_topic_version_id)
                REFERENCES navigator.journey_topic_versions (id) ON DELETE RESTRICT,
            CONSTRAINT fk_journey_topic_fact_links_fact_definition
                FOREIGN KEY (fact_definition_id)
                REFERENCES navigator.fact_definitions (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE INDEX ix_journey_topic_fact_links_fact_definition_id "
        "ON navigator.journey_topic_fact_links (fact_definition_id)"
    )

    execute(
        """
        CREATE TABLE navigator.journey_topic_destinations (
            id UUID NOT NULL,
            code TEXT NOT NULL,
            journey_topic_version_id UUID NOT NULL,
            journey_topic_evidence_id UUID NOT NULL,
            destination_kind TEXT NOT NULL,
            guidance_ar TEXT NOT NULL,
            guidance_en TEXT,
            what_to_verify_ar TEXT NOT NULL,
            what_to_verify_en TEXT,
            route_fact_definition_id UUID,
            route_match_kind TEXT NOT NULL,
            route_match_value JSONB,
            display_order INTEGER NOT NULL,
            is_primary BOOLEAN DEFAULT false NOT NULL,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_journey_topic_destinations PRIMARY KEY (id),
            CONSTRAINT uq_journey_topic_destinations_topic_code
                UNIQUE (journey_topic_version_id, code),
            CONSTRAINT uq_journey_topic_destinations_topic_display_order
                UNIQUE (journey_topic_version_id, display_order),
            CONSTRAINT ck_journey_topic_destinations_code_format
                CHECK (code ~ '^[a-z][a-z0-9_]*$'),
            CONSTRAINT ck_journey_topic_destinations_destination_kind CHECK (
                destination_kind IN ('authority', 'platform', 'service', 'page')
            ),
            CONSTRAINT ck_journey_topic_destinations_route_match_kind
                CHECK (route_match_kind IN ('always', 'equals')),
            CONSTRAINT ck_journey_topic_destinations_guidance_ar_nonblank
                CHECK (btrim(guidance_ar) <> ''),
            CONSTRAINT ck_journey_topic_destinations_what_to_verify_ar_nonblank
                CHECK (btrim(what_to_verify_ar) <> ''),
            CONSTRAINT ck_journey_topic_destinations_positive_display_order
                CHECK (display_order > 0),
            CONSTRAINT ck_journey_topic_destinations_route_shape CHECK (
                (route_match_kind = 'always' AND route_fact_definition_id IS NULL
                    AND route_match_value IS NULL)
                OR (route_match_kind = 'equals' AND route_fact_definition_id IS NOT NULL
                    AND route_match_value IS NOT NULL)
            ),
            CONSTRAINT fk_journey_topic_destinations_topic_version
                FOREIGN KEY (journey_topic_version_id)
                REFERENCES navigator.journey_topic_versions (id) ON DELETE RESTRICT,
            CONSTRAINT fk_journey_topic_destinations_evidence_topic
                FOREIGN KEY (journey_topic_evidence_id, journey_topic_version_id)
                REFERENCES navigator.journey_topic_evidence
                    (id, journey_topic_version_id) ON DELETE RESTRICT,
            CONSTRAINT fk_journey_topic_destinations_route_fact
                FOREIGN KEY (route_fact_definition_id)
                REFERENCES navigator.fact_definitions (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE INDEX ix_journey_topic_destinations_route_fact_id "
        "ON navigator.journey_topic_destinations (route_fact_definition_id)"
    )
    execute(
        "CREATE UNIQUE INDEX uq_journey_topic_destinations_primary_always "
        "ON navigator.journey_topic_destinations (journey_topic_version_id) "
        "WHERE is_primary AND route_match_kind = 'always'"
    )
    execute(
        "CREATE UNIQUE INDEX uq_journey_topic_destinations_primary_equals "
        "ON navigator.journey_topic_destinations "
        "(journey_topic_version_id, route_fact_definition_id, route_match_value) "
        "WHERE is_primary AND route_match_kind = 'equals'"
    )

    execute(
        """
        CREATE TABLE navigator.journey_topic_releases (
            id UUID NOT NULL,
            journey_topic_version_id UUID NOT NULL,
            release_number INTEGER NOT NULL,
            approval_review_event_id UUID NOT NULL,
            topic_graph_sha256 TEXT NOT NULL,
            release_status TEXT DEFAULT 'released' NOT NULL,
            released_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            withdrawn_at TIMESTAMPTZ,
            withdrawn_by_role TEXT,
            withdrawal_reason TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_journey_topic_releases PRIMARY KEY (id),
            CONSTRAINT uq_journey_topic_releases_release_number
                UNIQUE (journey_topic_version_id, release_number),
            CONSTRAINT uq_journey_topic_releases_approval_review_event
                UNIQUE (approval_review_event_id),
            CONSTRAINT ck_journey_topic_releases_positive_release_number
                CHECK (release_number > 0),
            CONSTRAINT ck_journey_topic_releases_topic_graph_sha256
                CHECK (topic_graph_sha256 ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_journey_topic_releases_release_status
                CHECK (release_status IN ('released', 'withdrawn')),
            CONSTRAINT ck_journey_topic_releases_withdrawal_state CHECK (
                (release_status = 'released' AND withdrawn_at IS NULL
                    AND withdrawn_by_role IS NULL AND withdrawal_reason IS NULL)
                OR (release_status = 'withdrawn' AND withdrawn_at IS NOT NULL
                    AND withdrawn_at >= released_at AND withdrawn_by_role IS NOT NULL
                    AND withdrawn_by_role ~ '^[a-z][a-z0-9_]*$'
                    AND withdrawal_reason IS NOT NULL
                    AND btrim(withdrawal_reason) <> '')
            ),
            CONSTRAINT fk_journey_topic_releases_topic_version
                FOREIGN KEY (journey_topic_version_id)
                REFERENCES navigator.journey_topic_versions (id) ON DELETE RESTRICT,
            CONSTRAINT fk_journey_topic_releases_approval_review
                FOREIGN KEY (approval_review_event_id)
                REFERENCES navigator.review_events (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE UNIQUE INDEX uq_journey_topic_releases_one_active "
        "ON navigator.journey_topic_releases (journey_topic_version_id) "
        "WHERE release_status = 'released'"
    )
    execute(
        "CREATE INDEX ix_journey_topic_releases_status "
        "ON navigator.journey_topic_releases (release_status)"
    )

    execute(
        """
        CREATE TABLE navigator.requirement_actionability_versions (
            id UUID NOT NULL,
            code TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            requirement_version_id UUID NOT NULL,
            detail_type TEXT NOT NULL,
            value_state TEXT NOT NULL,
            value_schema_version INTEGER DEFAULT 1 NOT NULL,
            value_payload JSONB,
            value_sha256 TEXT,
            primary_source_version_id UUID NOT NULL,
            official_excerpt_ar TEXT NOT NULL,
            official_excerpt_en TEXT,
            excerpt_locator TEXT NOT NULL,
            verification_status TEXT DEFAULT 'pending_source_verification' NOT NULL,
            approval_review_event_id UUID,
            last_verified_at TIMESTAMPTZ,
            review_interval_days INTEGER,
            next_review_at TIMESTAMPTZ,
            effective_from DATE,
            effective_until DATE,
            display_order INTEGER NOT NULL,
            is_current BOOLEAN DEFAULT false NOT NULL,
            supersedes_actionability_version_id UUID,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_requirement_actionability_versions PRIMARY KEY (id),
            CONSTRAINT uq_requirement_actionability_versions_code_version
                UNIQUE (code, version_number),
            CONSTRAINT uq_requirement_actionability_versions_supersedes
                UNIQUE (supersedes_actionability_version_id),
            CONSTRAINT ck_requirement_actionability_versions_code_format
                CHECK (code ~ '^[a-z][a-z0-9_]*$'),
            CONSTRAINT ck_requirement_actionability_versions_positive_version_number
                CHECK (version_number > 0),
            CONSTRAINT ck_requirement_actionability_versions_detail_type CHECK (
                detail_type IN ('official_start', 'prerequisite', 'document', 'fee',
                                'processing_time', 'sequence', 'validity')
            ),
            CONSTRAINT ck_requirement_actionability_versions_value_state
                CHECK (value_state IN ('VERIFIED', 'NOT_APPLICABLE')),
            CONSTRAINT ck_requirement_actionability_versions_value_schema_version
                CHECK (value_schema_version = 1),
            CONSTRAINT ck_requirement_actionability_versions_payload_hash_pair CHECK (
                (value_payload IS NULL AND value_sha256 IS NULL)
                OR (value_payload IS NOT NULL AND value_sha256 IS NOT NULL)
            ),
            CONSTRAINT ck_requirement_actionability_versions_value_sha256 CHECK (
                value_sha256 IS NULL OR value_sha256 ~ '^[0-9a-f]{64}$'
            ),
            CONSTRAINT ck_requirement_actionability_versions_value_state_shape CHECK (
                (value_state = 'VERIFIED' AND value_payload IS NOT NULL
                    AND jsonb_typeof(value_payload) = 'object'
                    AND value_sha256 IS NOT NULL)
                OR (value_state = 'NOT_APPLICABLE' AND value_payload IS NULL
                    AND value_sha256 IS NULL)
            ),
            CONSTRAINT ck_requirement_actionability_versions_verified_payload_kind CHECK (
                value_state <> 'VERIFIED' OR (
                    (detail_type IN ('prerequisite', 'document', 'sequence', 'validity')
                        AND value_payload ->> 'kind' = 'text'
                        AND jsonb_typeof(value_payload -> 'text_ar') = 'string'
                        AND btrim(value_payload ->> 'text_ar') <> ''
                        AND (value_payload
                            - ARRAY['kind', 'text_ar', 'text_en']::text[]) = '{}'::jsonb
                        AND (NOT value_payload ? 'text_en'
                            OR (jsonb_typeof(value_payload -> 'text_en') = 'string'
                                AND btrim(value_payload ->> 'text_en') <> '')))
                    OR (detail_type = 'official_start'
                        AND value_payload ->> 'kind' = 'official_destination'
                        AND jsonb_typeof(value_payload -> 'label_ar') = 'string'
                        AND btrim(value_payload ->> 'label_ar') <> ''
                        AND (value_payload
                            - ARRAY['kind', 'label_ar', 'label_en']::text[]) = '{}'::jsonb
                        AND (NOT value_payload ? 'label_en'
                            OR (jsonb_typeof(value_payload -> 'label_en') = 'string'
                                AND btrim(value_payload ->> 'label_en') <> '')))
                    OR (detail_type = 'fee'
                        AND value_payload ->> 'kind' IN ('money', 'fee_calculator'))
                    OR (detail_type IN ('processing_time', 'validity')
                        AND value_payload ->> 'kind' = 'duration')
                )
            ),
            CONSTRAINT ck_requirement_actionability_versions_money_payload_shape CHECK (
                value_state <> 'VERIFIED' OR detail_type <> 'fee'
                OR (value_payload ->> 'kind' = 'money'
                    AND jsonb_typeof(value_payload -> 'amount_minor') = 'number'
                    AND (value_payload ->> 'amount_minor') ~ '^(0|[1-9][0-9]*)$'
                    AND value_payload ->> 'currency' = 'SAR'
                    AND jsonb_typeof(value_payload -> 'label_ar') = 'string'
                    AND btrim(value_payload ->> 'label_ar') <> ''
                    AND (value_payload - ARRAY[
                        'kind', 'amount_minor', 'currency', 'label_ar', 'label_en'
                    ]::text[]) = '{}'::jsonb
                    AND (NOT value_payload ? 'label_en'
                        OR (jsonb_typeof(value_payload -> 'label_en') = 'string'
                            AND btrim(value_payload ->> 'label_en') <> '')))
                OR (value_payload ->> 'kind' = 'fee_calculator'
                    AND jsonb_typeof(value_payload -> 'label_ar') = 'string'
                    AND btrim(value_payload ->> 'label_ar') <> ''
                    AND (value_payload
                        - ARRAY['kind', 'label_ar', 'label_en']::text[]) = '{}'::jsonb
                    AND (NOT value_payload ? 'label_en'
                        OR (jsonb_typeof(value_payload -> 'label_en') = 'string'
                            AND btrim(value_payload ->> 'label_en') <> '')))
            ),
            CONSTRAINT ck_requirement_actionability_versions_duration_payload_shape CHECK (
                value_state <> 'VERIFIED'
                OR detail_type NOT IN ('processing_time', 'validity')
                OR value_payload ->> 'kind' <> 'duration'
                OR (value_payload ->> 'unit' IN (
                        'minute', 'hour', 'day', 'week', 'month', 'year'
                    )
                    AND jsonb_typeof(value_payload -> 'label_ar') = 'string'
                    AND btrim(value_payload ->> 'label_ar') <> ''
                    AND (value_payload - ARRAY[
                        'kind', 'value', 'minimum', 'maximum',
                        'unit', 'label_ar', 'label_en'
                    ]::text[]) = '{}'::jsonb
                    AND (NOT value_payload ? 'label_en'
                        OR (jsonb_typeof(value_payload -> 'label_en') = 'string'
                            AND btrim(value_payload ->> 'label_en') <> ''))
                    AND (NOT value_payload ? 'value'
                        OR (jsonb_typeof(value_payload -> 'value') = 'number'
                            AND (value_payload ->> 'value') ~ '^(0|[1-9][0-9]*)$'))
                    AND (NOT value_payload ? 'minimum'
                        OR (jsonb_typeof(value_payload -> 'minimum') = 'number'
                            AND (value_payload ->> 'minimum') ~ '^(0|[1-9][0-9]*)$'))
                    AND (NOT value_payload ? 'maximum'
                        OR (jsonb_typeof(value_payload -> 'maximum') = 'number'
                            AND (value_payload ->> 'maximum') ~ '^(0|[1-9][0-9]*)$'))
                    AND ((value_payload ? 'value'
                            AND NOT value_payload ? 'minimum'
                            AND NOT value_payload ? 'maximum')
                        OR (NOT value_payload ? 'value'
                            AND value_payload ? 'minimum'))
                    AND (NOT value_payload ? 'maximum'
                        OR (value_payload ->> 'maximum')::numeric
                            >= (value_payload ->> 'minimum')::numeric))
            ),
            CONSTRAINT ck_requirement_actionability_versions_official_excerpt_ar_nonblank
                CHECK (btrim(official_excerpt_ar) <> ''),
            CONSTRAINT ck_requirement_actionability_versions_excerpt_locator_nonblank
                CHECK (btrim(excerpt_locator) <> ''),
            CONSTRAINT ck_requirement_actionability_versions_verification_status CHECK (
                verification_status IN (
                    'pending_source_verification', 'pending_review', 'approved', 'rejected',
                    'conflicting', 'stale', 'expired', 'superseded', 'historical'
                )
            ),
            CONSTRAINT ck_requirement_actionability_versions_effective_date_order CHECK (
                effective_until IS NULL OR effective_from IS NULL
                OR effective_until >= effective_from
            ),
            CONSTRAINT ck_requirement_actionability_versions_freshness_order CHECK (
                (last_verified_at IS NULL AND review_interval_days IS NULL
                    AND next_review_at IS NULL)
                OR (last_verified_at IS NOT NULL AND review_interval_days IS NOT NULL
                    AND next_review_at IS NOT NULL
                    AND next_review_at = last_verified_at
                        + make_interval(days => review_interval_days))
            ),
            CONSTRAINT ck_requirement_actionability_versions_review_interval CHECK (
                review_interval_days IS NULL OR review_interval_days BETWEEN 30 AND 180
            ),
            CONSTRAINT ck_requirement_actionability_versions_approved_has_review CHECK (
                verification_status <> 'approved'
                OR (approval_review_event_id IS NOT NULL AND last_verified_at IS NOT NULL)
            ),
            CONSTRAINT ck_requirement_actionability_versions_current_is_approved CHECK (
                NOT is_current OR verification_status = 'approved'
            ),
            CONSTRAINT ck_requirement_actionability_versions_inactive_status_not_current CHECK (
                verification_status NOT IN ('expired', 'superseded', 'historical')
                OR NOT is_current
            ),
            CONSTRAINT ck_requirement_actionability_versions_not_self_superseding CHECK (
                supersedes_actionability_version_id IS DISTINCT FROM id
            ),
            CONSTRAINT ck_requirement_actionability_versions_positive_display_order
                CHECK (display_order > 0),
            CONSTRAINT fk_requirement_actionability_versions_requirement_version
                FOREIGN KEY (requirement_version_id)
                REFERENCES navigator.requirement_versions (id) ON DELETE RESTRICT,
            CONSTRAINT fk_requirement_actionability_versions_primary_source_version
                FOREIGN KEY (primary_source_version_id)
                REFERENCES navigator.source_versions (id) ON DELETE RESTRICT,
            CONSTRAINT fk_requirement_actionability_versions_approval_review
                FOREIGN KEY (approval_review_event_id)
                REFERENCES navigator.review_events (id) ON DELETE RESTRICT,
            CONSTRAINT fk_requirement_actionability_versions_supersedes
                FOREIGN KEY (supersedes_actionability_version_id)
                REFERENCES navigator.requirement_actionability_versions (id)
                ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE UNIQUE INDEX uq_requirement_actionability_versions_one_current "
        "ON navigator.requirement_actionability_versions (code) WHERE is_current"
    )
    for index_sql in (
        "CREATE INDEX ix_requirement_actionability_versions_requirement_version_id "
        "ON navigator.requirement_actionability_versions (requirement_version_id)",
        "CREATE INDEX ix_requirement_actionability_versions_primary_source_version_id "
        "ON navigator.requirement_actionability_versions (primary_source_version_id)",
        "CREATE INDEX ix_requirement_actionability_versions_approval_review_event_id "
        "ON navigator.requirement_actionability_versions (approval_review_event_id)",
        "CREATE INDEX ix_requirement_actionability_versions_verification_status "
        "ON navigator.requirement_actionability_versions (verification_status)",
        "CREATE INDEX ix_requirement_actionability_versions_next_review_at "
        "ON navigator.requirement_actionability_versions (next_review_at)",
    ):
        execute(index_sql)

    execute(
        """
        CREATE TABLE navigator.requirement_actionability_releases (
            id UUID NOT NULL,
            requirement_actionability_version_id UUID NOT NULL,
            release_number INTEGER NOT NULL,
            approval_review_event_id UUID NOT NULL,
            release_status TEXT DEFAULT 'released' NOT NULL,
            released_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            withdrawn_at TIMESTAMPTZ,
            withdrawn_by_role TEXT,
            withdrawal_reason TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_requirement_actionability_releases PRIMARY KEY (id),
            CONSTRAINT uq_requirement_actionability_releases_release_number
                UNIQUE (requirement_actionability_version_id, release_number),
            CONSTRAINT uq_requirement_actionability_releases_approval_review_event
                UNIQUE (approval_review_event_id),
            CONSTRAINT ck_requirement_actionability_releases_positive_release_number
                CHECK (release_number > 0),
            CONSTRAINT ck_requirement_actionability_releases_release_status
                CHECK (release_status IN ('released', 'withdrawn')),
            CONSTRAINT ck_requirement_actionability_releases_withdrawal_state CHECK (
                (release_status = 'released' AND withdrawn_at IS NULL
                    AND withdrawn_by_role IS NULL AND withdrawal_reason IS NULL)
                OR (release_status = 'withdrawn' AND withdrawn_at IS NOT NULL
                    AND withdrawn_at >= released_at AND withdrawn_by_role IS NOT NULL
                    AND withdrawn_by_role ~ '^[a-z][a-z0-9_]*$'
                    AND withdrawal_reason IS NOT NULL
                    AND btrim(withdrawal_reason) <> '')
            ),
            CONSTRAINT fk_requirement_actionability_releases_actionability_version
                FOREIGN KEY (requirement_actionability_version_id)
                REFERENCES navigator.requirement_actionability_versions (id)
                ON DELETE RESTRICT,
            CONSTRAINT fk_requirement_actionability_releases_approval_review
                FOREIGN KEY (approval_review_event_id)
                REFERENCES navigator.review_events (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE UNIQUE INDEX uq_requirement_actionability_releases_one_active "
        "ON navigator.requirement_actionability_releases "
        "(requirement_actionability_version_id) WHERE release_status = 'released'"
    )
    execute(
        "CREATE INDEX ix_requirement_actionability_releases_status "
        "ON navigator.requirement_actionability_releases (release_status)"
    )

    execute(
        """
        ALTER TABLE navigator.research_events
            ADD COLUMN journey_topic_version_id UUID,
            ADD COLUMN requirement_actionability_version_id UUID,
            ADD CONSTRAINT fk_research_events_journey_topic_version
                FOREIGN KEY (journey_topic_version_id)
                REFERENCES navigator.journey_topic_versions (id) ON DELETE RESTRICT,
            ADD CONSTRAINT fk_research_events_requirement_actionability_version
                FOREIGN KEY (requirement_actionability_version_id)
                REFERENCES navigator.requirement_actionability_versions (id)
                ON DELETE RESTRICT,
            DROP CONSTRAINT ck_research_events_exactly_one_target,
            ADD CONSTRAINT ck_research_events_exactly_one_target CHECK (
                num_nonnulls(
                    government_entity_id, platform_id, domain_id, source_id,
                    source_version_id, requirement_version_id, requirement_source_id,
                    journey_topic_version_id, requirement_actionability_version_id
                ) = 1
            )
        """
    )
    execute(
        "CREATE INDEX ix_research_events_journey_topic_version_id "
        "ON navigator.research_events (journey_topic_version_id)"
    )
    execute(
        "CREATE INDEX ix_research_events_requirement_actionability_version_id "
        "ON navigator.research_events (requirement_actionability_version_id)"
    )

    _create_functions_triggers_and_views()


def _create_functions_triggers_and_views() -> None:
    """Install fail-closed governance, eligibility, and release boundaries."""
    execute = op.execute

    execute(
        """
        CREATE FUNCTION navigator.canonical_json_text(candidate JSONB)
        RETURNS TEXT
        LANGUAGE sql
        IMMUTABLE
        STRICT
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
            SELECT CASE pg_catalog.jsonb_typeof(candidate)
                WHEN 'object' THEN '{' || COALESCE((
                    SELECT pg_catalog.string_agg(
                        pg_catalog.to_jsonb(
                            pg_catalog.normalize(item.key, 'NFC')
                        )::text || ':' ||
                        navigator.canonical_json_text(item.value),
                        ',' ORDER BY
                            pg_catalog.normalize(item.key, 'NFC') COLLATE "C"
                    )
                    FROM pg_catalog.jsonb_each(candidate) AS item(key, value)
                ), '') || '}'
                WHEN 'array' THEN '[' || COALESCE((
                    SELECT pg_catalog.string_agg(
                        navigator.canonical_json_text(item.value),
                        ',' ORDER BY item.ordinality
                    )
                    FROM pg_catalog.jsonb_array_elements(candidate)
                        WITH ORDINALITY AS item(value, ordinality)
                ), '') || ']'
                WHEN 'string' THEN pg_catalog.to_jsonb(
                    pg_catalog.normalize(candidate #>> '{}', 'NFC')
                )::text
                ELSE candidate::text
            END
        $$
        """
    )
    execute(
        """
        CREATE FUNCTION navigator.canonical_json_sha256(candidate JSONB)
        RETURNS TEXT
        LANGUAGE sql
        IMMUTABLE
        STRICT
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
            SELECT pg_catalog.encode(
                pg_catalog.sha256(pg_catalog.convert_to(
                    navigator.canonical_json_text(candidate), 'UTF8'
                )),
                'hex'
            )
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.source_version_is_eligible_for_current_use(
            candidate_source_version_id UUID
        )
        RETURNS BOOLEAN
        LANGUAGE sql
        STABLE
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
            SELECT EXISTS (
                SELECT 1
                FROM navigator.source_versions AS source_version
                JOIN navigator.sources AS stable_source
                  ON stable_source.id = source_version.source_id
                JOIN navigator.domains AS source_domain
                  ON source_domain.id = source_version.domain_id_at_review
                JOIN navigator.government_entities AS source_entity
                  ON source_entity.id = stable_source.responsible_entity_id
                JOIN navigator.government_entities AS domain_entity
                  ON domain_entity.id = source_domain.responsible_entity_id
                LEFT JOIN navigator.platforms AS source_platform
                  ON source_platform.id = source_domain.platform_id
                LEFT JOIN navigator.government_entities AS platform_entity
                  ON platform_entity.id = source_platform.responsible_entity_id
                WHERE source_version.id = candidate_source_version_id
                  AND source_version.is_current
                  AND (source_version.effective_from IS NULL
                       OR source_version.effective_from <= CURRENT_DATE)
                  AND (source_version.effective_until IS NULL
                       OR CURRENT_DATE <= source_version.effective_until)
                  AND navigator.is_approved_and_fresh(
                        source_version.review_status,
                        source_version.verification_review_event_id,
                        source_version.last_verified_at,
                        source_version.review_interval_days,
                        source_version.next_review_at,
                        'source_version', source_version.id
                  )
                  AND navigator.is_approved_and_fresh(
                        stable_source.verification_status,
                        stable_source.verification_review_event_id,
                        stable_source.last_verified_at,
                        stable_source.review_interval_days,
                        stable_source.next_review_at,
                        'source', stable_source.id
                  )
                  AND navigator.is_approved_and_fresh(
                        source_domain.verification_status,
                        source_domain.verification_review_event_id,
                        source_domain.last_verified_at,
                        source_domain.review_interval_days,
                        source_domain.next_review_at,
                        'domain', source_domain.id
                  )
                  AND navigator.is_approved_and_fresh(
                        source_entity.verification_status,
                        source_entity.verification_review_event_id,
                        source_entity.last_verified_at,
                        source_entity.review_interval_days,
                        source_entity.next_review_at,
                        'government_entity', source_entity.id
                  )
                  AND navigator.is_approved_and_fresh(
                        domain_entity.verification_status,
                        domain_entity.verification_review_event_id,
                        domain_entity.last_verified_at,
                        domain_entity.review_interval_days,
                        domain_entity.next_review_at,
                        'government_entity', domain_entity.id
                  )
                  AND (source_entity.valid_from IS NULL
                       OR source_entity.valid_from <= CURRENT_DATE)
                  AND (source_entity.valid_until IS NULL
                       OR CURRENT_DATE <= source_entity.valid_until)
                  AND (domain_entity.valid_from IS NULL
                       OR domain_entity.valid_from <= CURRENT_DATE)
                  AND (domain_entity.valid_until IS NULL
                       OR CURRENT_DATE <= domain_entity.valid_until)
                  AND source_version.domain_id_at_review = stable_source.domain_id
                  AND source_version.responsible_entity_id_at_review =
                      stable_source.responsible_entity_id
                  AND source_version.platform_id_at_review IS NOT DISTINCT FROM
                      source_domain.platform_id
                  AND source_version.reviewed_url = stable_source.canonical_url
                  AND navigator.url_host(source_version.reviewed_url) =
                      stable_source.canonical_host
                  AND navigator.url_host(source_version.resolved_url) =
                      source_domain.domain_name
                  AND (
                      source_domain.platform_id IS NULL
                      OR (
                          source_platform.id IS NOT NULL
                          AND platform_entity.id IS NOT NULL
                          AND navigator.is_approved_and_fresh(
                                source_platform.verification_status,
                                source_platform.verification_review_event_id,
                                source_platform.last_verified_at,
                                source_platform.review_interval_days,
                                source_platform.next_review_at,
                                'platform', source_platform.id
                          )
                          AND navigator.is_approved_and_fresh(
                                platform_entity.verification_status,
                                platform_entity.verification_review_event_id,
                                platform_entity.last_verified_at,
                                platform_entity.review_interval_days,
                                platform_entity.next_review_at,
                                'government_entity', platform_entity.id
                          )
                          AND (source_platform.valid_from IS NULL
                               OR source_platform.valid_from <= CURRENT_DATE)
                          AND (source_platform.valid_until IS NULL
                               OR CURRENT_DATE <= source_platform.valid_until)
                          AND (platform_entity.valid_from IS NULL
                               OR platform_entity.valid_from <= CURRENT_DATE)
                          AND (platform_entity.valid_until IS NULL
                               OR CURRENT_DATE <= platform_entity.valid_until)
                      )
                  )
            )
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.guard_journey_topic_identity()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM navigator.journey_topic_versions
                WHERE journey_topic_id = OLD.id
            ) THEN
                IF TG_OP = 'DELETE' THEN
                    RAISE EXCEPTION 'journey topic history is immutable';
                END IF;
                IF NEW.id IS DISTINCT FROM OLD.id OR NEW.code IS DISTINCT FROM OLD.code
                    OR NEW.created_at IS DISTINCT FROM OLD.created_at
                THEN
                    RAISE EXCEPTION 'versioned journey topic identity is immutable';
                END IF;
            END IF;
            RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_journey_topic_version()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            predecessor navigator.journey_topic_versions%ROWTYPE;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.verification_status = 'approved'
                    OR EXISTS (
                        SELECT 1 FROM navigator.journey_topic_releases
                        WHERE journey_topic_version_id = OLD.id
                    )
                THEN
                    RAISE EXCEPTION 'reviewed journey topic history is immutable';
                END IF;
                RETURN OLD;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM navigator.business_activities
                WHERE id = NEW.activity_id AND is_active
            ) THEN
                RAISE EXCEPTION 'journey topic requires an active supported activity';
            END IF;

            IF TG_OP = 'INSERT' THEN
                IF NEW.supersedes_journey_topic_version_id IS NULL THEN
                    IF NEW.version_number <> 1 THEN
                        RAISE EXCEPTION 'first journey topic version must be version 1';
                    END IF;
                ELSE
                    SELECT * INTO predecessor
                    FROM navigator.journey_topic_versions
                    WHERE id = NEW.supersedes_journey_topic_version_id
                    FOR UPDATE;
                    IF NOT FOUND
                        OR predecessor.journey_topic_id <> NEW.journey_topic_id
                        OR predecessor.activity_id <> NEW.activity_id
                        OR NEW.version_number <> predecessor.version_number + 1
                    THEN
                        RAISE EXCEPTION '%',
                            'journey topic supersession must be linear within topic and activity';
                    END IF;
                END IF;
                IF NEW.verification_status NOT IN (
                        'pending_source_verification', 'pending_review'
                    )
                    OR NEW.approval_review_event_id IS NOT NULL
                    OR NEW.last_verified_at IS NOT NULL
                    OR NEW.review_interval_days IS NOT NULL
                    OR NEW.next_review_at IS NOT NULL
                    OR NEW.is_current
                THEN
                    RAISE EXCEPTION 'journey topic versions begin in an unverified workflow state';
                END IF;
                RETURN NEW;
            END IF;

            IF NEW.id IS DISTINCT FROM OLD.id
                OR NEW.journey_topic_id IS DISTINCT FROM OLD.journey_topic_id
                OR NEW.activity_id IS DISTINCT FROM OLD.activity_id
                OR NEW.version_number IS DISTINCT FROM OLD.version_number
                OR NEW.supersedes_journey_topic_version_id IS DISTINCT FROM
                    OLD.supersedes_journey_topic_version_id
                OR NEW.created_at IS DISTINCT FROM OLD.created_at
            THEN
                RAISE EXCEPTION 'journey topic version identity is immutable';
            END IF;
            IF OLD.verification_status = 'approved' AND (
                pg_catalog.to_jsonb(NEW)
                    - 'verification_status' - 'approval_review_event_id'
                    - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                    - 'is_current' - 'notes' - 'updated_at'
            ) IS DISTINCT FROM (
                pg_catalog.to_jsonb(OLD)
                    - 'verification_status' - 'approval_review_event_id'
                    - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                    - 'is_current' - 'notes' - 'updated_at'
            ) THEN
                RAISE EXCEPTION 'approved journey topic meaning requires a new version';
            END IF;
            IF NEW.last_verified_at IS DISTINCT FROM OLD.last_verified_at
                OR NEW.review_interval_days IS DISTINCT FROM OLD.review_interval_days
                OR NEW.next_review_at IS DISTINCT FROM OLD.next_review_at
            THEN
                RAISE EXCEPTION 'journey verification dates are database derived';
            END IF;
            IF NEW.approval_review_event_id IS NOT DISTINCT FROM
                OLD.approval_review_event_id
                AND NEW.verification_status IS DISTINCT FROM OLD.verification_status
            THEN
                RAISE EXCEPTION 'journey status changes require a new exact-target review';
            END IF;
            IF NOT OLD.is_current AND NEW.is_current
                AND NEW.approval_review_event_id IS NOT DISTINCT FROM
                    OLD.approval_review_event_id
            THEN
                RAISE EXCEPTION 'restoring a journey topic requires a new review';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.apply_journey_topic_review()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            review_decision TEXT;
            review_time TIMESTAMPTZ;
            authorized_interval INTEGER;
            target_matches BOOLEAN;
            research_status_value TEXT;
            research_recommendation TEXT;
            old_review_time TIMESTAMPTZ;
        BEGIN
            IF NEW.approval_review_event_id IS NOT DISTINCT FROM
                OLD.approval_review_event_id
            THEN
                RETURN NEW;
            END IF;
            IF NEW.approval_review_event_id IS NULL THEN
                RAISE EXCEPTION 'journey review cannot be cleared';
            END IF;

            SELECT review.decision, review.reviewed_at,
                   review.authorized_review_interval_days,
                   research.journey_topic_version_id = NEW.id,
                   research.research_status, research.recommendation
            INTO review_decision, review_time, authorized_interval, target_matches,
                 research_status_value, research_recommendation
            FROM navigator.review_events AS review
            JOIN navigator.research_events AS research
              ON research.id = review.research_event_id
            WHERE review.id = NEW.approval_review_event_id;

            IF NOT FOUND OR target_matches IS DISTINCT FROM TRUE THEN
                RAISE EXCEPTION 'review event does not target this journey topic version';
            END IF;
            IF review_time > pg_catalog.clock_timestamp() THEN
                RAISE EXCEPTION 'future journey reviews are prohibited';
            END IF;
            IF OLD.approval_review_event_id IS NOT NULL THEN
                SELECT reviewed_at INTO old_review_time
                FROM navigator.review_events
                WHERE id = OLD.approval_review_event_id;
                IF review_time <= old_review_time THEN
                    RAISE EXCEPTION 'replacement journey review must be newer';
                END IF;
            END IF;

            IF NEW.verification_status = 'approved' THEN
                IF review_decision <> 'approved'
                    OR research_status_value <> 'completed'
                    OR research_recommendation <> 'approve'
                THEN
                    RAISE EXCEPTION 'approved journey status requires completed approving research';
                END IF;
                NEW.last_verified_at := review_time;
                NEW.review_interval_days := COALESCE(authorized_interval, 90);
                NEW.next_review_at := review_time
                    + pg_catalog.make_interval(days => COALESCE(authorized_interval, 90));
                NEW.is_current := true;
            ELSE
                IF (NEW.verification_status = 'rejected' AND review_decision <> 'rejected')
                    OR (NEW.verification_status = 'conflicting'
                        AND review_decision <> 'blocked_by_conflict')
                    OR (NEW.verification_status = 'stale'
                        AND review_decision <> 'marked_stale')
                    OR (NEW.verification_status = 'expired'
                        AND review_decision <> 'marked_expired')
                    OR (NEW.verification_status = 'superseded'
                        AND review_decision <> 'marked_superseded')
                    OR (NEW.verification_status = 'historical'
                        AND review_decision <> 'marked_historical')
                THEN
                    RAISE EXCEPTION 'journey status and review decision do not match';
                END IF;
                NEW.last_verified_at := NULL;
                NEW.review_interval_days := NULL;
                NEW.next_review_at := NULL;
                NEW.is_current := false;
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.guard_journey_topic_child()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            target_version_id UUID;
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION 'journey graph links are replaced, not rewritten';
            END IF;
            target_version_id := CASE WHEN TG_OP = 'DELETE'
                THEN (pg_catalog.to_jsonb(OLD)->>'journey_topic_version_id')::uuid
                ELSE (pg_catalog.to_jsonb(NEW)->>'journey_topic_version_id')::uuid
            END;
            PERFORM 1 FROM navigator.journey_topic_versions
            WHERE id = target_version_id FOR UPDATE;
            IF EXISTS (
                SELECT 1 FROM navigator.journey_topic_versions
                WHERE id = target_version_id AND verification_status = 'approved'
            ) THEN
                RAISE EXCEPTION 'approved journey topic graph is immutable; create a new version';
            END IF;
            RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_navigation_fact_separation()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            candidate_fact_id UUID;
        BEGIN
            candidate_fact_id := (pg_catalog.to_jsonb(NEW)->>'fact_definition_id')::uuid;
            IF TG_TABLE_NAME = 'journey_topic_fact_links' THEN
                IF EXISTS (
                    SELECT 1 FROM navigator.requirement_condition_facts
                    WHERE fact_definition_id = candidate_fact_id
                ) THEN
                    RAISE EXCEPTION 'a fact version cannot drive both navigation and applicability';
                END IF;
            ELSE
                IF EXISTS (
                    SELECT 1 FROM navigator.journey_topic_fact_links
                    WHERE fact_definition_id = candidate_fact_id
                ) THEN
                    RAISE EXCEPTION 'a fact version cannot drive both applicability and navigation';
                END IF;
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_journey_destination()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            fact_type TEXT;
            allowed JSONB;
            fact_status TEXT;
            fact_current BOOLEAN;
        BEGIN
            IF NEW.route_match_kind = 'equals' THEN
                SELECT data_type, allowed_values, verification_status, is_current
                INTO fact_type, allowed, fact_status, fact_current
                FROM navigator.fact_definitions
                WHERE id = NEW.route_fact_definition_id;
                IF NOT FOUND OR fact_status <> 'approved' OR NOT fact_current THEN
                    RAISE EXCEPTION 'destination routing requires a current approved fact';
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM navigator.journey_topic_fact_links
                    WHERE journey_topic_version_id = NEW.journey_topic_version_id
                      AND fact_definition_id = NEW.route_fact_definition_id
                ) THEN
                    RAISE EXCEPTION '%',
                        'destination routing fact must be linked to the same topic version';
                END IF;
                IF fact_type = 'boolean' AND jsonb_typeof(NEW.route_match_value) <> 'boolean' THEN
                    RAISE EXCEPTION 'Boolean route value must be a JSON Boolean';
                ELSIF fact_type = 'enum' AND (
                    jsonb_typeof(NEW.route_match_value) <> 'string'
                    OR NOT allowed @> pg_catalog.jsonb_build_array(NEW.route_match_value)
                ) THEN
                    RAISE EXCEPTION 'enum route value must be one governed allowed value';
                ELSIF fact_type NOT IN ('boolean', 'enum') THEN
                    RAISE EXCEPTION '%',
                        'destination equality routing supports Boolean or enum facts only';
                END IF;
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_journey_topic_graph()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            target_version_id UUID;
            topic_version navigator.journey_topic_versions%ROWTYPE;
        BEGIN
            IF TG_TABLE_NAME = 'journey_topic_versions' THEN
                target_version_id := CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END;
            ELSE
                target_version_id := CASE WHEN TG_OP = 'DELETE'
                    THEN (pg_catalog.to_jsonb(OLD)->>'journey_topic_version_id')::uuid
                    ELSE (pg_catalog.to_jsonb(NEW)->>'journey_topic_version_id')::uuid
                END;
            END IF;
            SELECT * INTO topic_version
            FROM navigator.journey_topic_versions
            WHERE id = target_version_id;
            IF NOT FOUND OR topic_version.verification_status <> 'approved' THEN
                RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
            END IF;
            IF topic_version.coverage_state = 'NOT_RESEARCHED' THEN
                RAISE EXCEPTION 'NOT_RESEARCHED journey topics cannot be approved';
            END IF;
            IF NOT EXISTS (
                SELECT 1
                FROM navigator.review_events AS review
                JOIN navigator.research_events AS research
                  ON research.id = review.research_event_id
                WHERE review.id = topic_version.approval_review_event_id
                  AND review.decision = 'approved'
                  AND review.reviewed_at <= pg_catalog.clock_timestamp()
                  AND research.journey_topic_version_id = target_version_id
                  AND research.research_status = 'completed'
                  AND research.recommendation = 'approve'
            ) THEN
                RAISE EXCEPTION 'approved journey topic requires an exact approving review';
            END IF;
            IF (
                SELECT count(*) FROM navigator.journey_topic_evidence
                WHERE journey_topic_version_id = target_version_id
                  AND evidence_role = 'primary'
            ) <> 1 THEN
                RAISE EXCEPTION 'approved journey topic requires exactly one primary source';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM navigator.journey_topic_evidence AS evidence
                WHERE evidence.journey_topic_version_id = target_version_id
                  AND evidence.evidence_role <> 'historical'
                  AND (
                      NOT navigator.source_version_is_eligible_for_current_use(
                          evidence.source_version_id
                      )
                      OR NOT EXISTS (
                          SELECT 1
                          FROM navigator.review_events AS review
                          JOIN navigator.research_event_evidence AS cited
                            ON cited.research_event_id = review.research_event_id
                          WHERE review.id = topic_version.approval_review_event_id
                            AND cited.source_version_id = evidence.source_version_id
                      )
                  )
            ) THEN
                RAISE EXCEPTION 'journey topic evidence is unreviewed, stale, or ineligible';
            END IF;
            IF topic_version.coverage_state = 'REQUIRES_OFFICIAL_CONFIRMATION'
                AND NOT EXISTS (
                    SELECT 1 FROM navigator.journey_topic_destinations
                    WHERE journey_topic_version_id = target_version_id
                )
            THEN
                RAISE EXCEPTION 'official confirmation state requires an official destination';
            END IF;
            IF topic_version.coverage_state = 'UNRESOLVED'
                AND topic_version.limitation_type = 'material_conflict'
                AND NOT EXISTS (
                    SELECT 1 FROM navigator.journey_topic_evidence
                    WHERE journey_topic_version_id = target_version_id
                      AND evidence_role = 'conflicting'
                )
            THEN
                RAISE EXCEPTION 'material conflict requires conflicting official evidence';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM navigator.journey_topic_requirement_links AS link
                WHERE link.journey_topic_version_id = target_version_id
                  AND NOT EXISTS (
                      SELECT 1
                      FROM navigator.requirement_activities AS activity_link
                      WHERE activity_link.requirement_version_id = link.requirement_version_id
                        AND activity_link.activity_id = topic_version.activity_id
                  )
            ) THEN
                RAISE EXCEPTION 'journey requirement links must match the topic activity';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM navigator.journey_topic_fact_links AS link
                JOIN navigator.fact_definitions AS fact
                  ON fact.id = link.fact_definition_id
                WHERE link.journey_topic_version_id = target_version_id
                  AND (fact.verification_status <> 'approved' OR NOT fact.is_current
                       OR fact.privacy_class <> 'non_personal_business'
                       OR EXISTS (
                           SELECT 1 FROM navigator.requirement_condition_facts
                           WHERE fact_definition_id = fact.id
                       ))
            ) THEN
                RAISE EXCEPTION 'journey facts must be current approved navigation-only facts';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM navigator.journey_topic_destinations AS destination
                JOIN navigator.journey_topic_evidence AS evidence
                  ON evidence.id = destination.journey_topic_evidence_id
                WHERE destination.journey_topic_version_id = target_version_id
                  AND (
                      evidence.journey_topic_version_id <> target_version_id
                      OR evidence.evidence_role = 'historical'
                      OR NOT navigator.source_version_is_eligible_for_current_use(
                          evidence.source_version_id
                      )
                      OR (
                          destination.route_match_kind = 'equals'
                          AND NOT EXISTS (
                              SELECT 1 FROM navigator.journey_topic_fact_links
                              WHERE journey_topic_version_id = target_version_id
                                AND fact_definition_id =
                                    destination.route_fact_definition_id
                          )
                      )
                  )
            ) THEN
                RAISE EXCEPTION 'journey destination graph is inconsistent or ineligible';
            END IF;
            RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.journey_topic_graph_sha256(candidate_version_id UUID)
        RETURNS TEXT
        LANGUAGE plpgsql
        STABLE
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            graph_payload JSONB;
        BEGIN
            SELECT pg_catalog.jsonb_build_object(
                'version', pg_catalog.jsonb_build_object(
                    'id', version.id,
                    'journey_topic_id', version.journey_topic_id,
                    'activity_id', version.activity_id,
                    'version_number', version.version_number,
                    'title_ar', version.title_ar,
                    'title_en', version.title_en,
                    'coverage_state', version.coverage_state,
                    'limitation_type', version.limitation_type,
                    'verified_summary_ar', version.verified_summary_ar,
                    'verified_summary_en', version.verified_summary_en,
                    'limitation_summary_ar', version.limitation_summary_ar,
                    'limitation_summary_en', version.limitation_summary_en,
                    'what_to_verify_ar', version.what_to_verify_ar,
                    'what_to_verify_en', version.what_to_verify_en,
                    'effective_from', version.effective_from,
                    'effective_until', version.effective_until,
                    'supersedes', version.supersedes_journey_topic_version_id
                ),
                'evidence', COALESCE((
                    SELECT pg_catalog.jsonb_agg(
                        pg_catalog.jsonb_build_object(
                            'id', evidence.id,
                            'source_version_id', evidence.source_version_id,
                            'role', evidence.evidence_role,
                            'official_excerpt_ar', evidence.official_excerpt_ar,
                            'official_excerpt_en', evidence.official_excerpt_en,
                            'locator', evidence.excerpt_locator
                        ) ORDER BY evidence.source_version_id
                    )
                    FROM navigator.journey_topic_evidence AS evidence
                    WHERE evidence.journey_topic_version_id = version.id
                ), '[]'::jsonb),
                'requirements', COALESCE((
                    SELECT pg_catalog.jsonb_agg(
                        pg_catalog.jsonb_build_object(
                            'requirement_version_id', link.requirement_version_id,
                            'role', link.link_role
                        ) ORDER BY link.requirement_version_id
                    )
                    FROM navigator.journey_topic_requirement_links AS link
                    WHERE link.journey_topic_version_id = version.id
                ), '[]'::jsonb),
                'facts', COALESCE((
                    SELECT pg_catalog.jsonb_agg(
                        pg_catalog.jsonb_build_object(
                            'fact_definition_id', link.fact_definition_id,
                            'role', link.input_role
                        ) ORDER BY link.fact_definition_id
                    )
                    FROM navigator.journey_topic_fact_links AS link
                    WHERE link.journey_topic_version_id = version.id
                ), '[]'::jsonb),
                'destinations', COALESCE((
                    SELECT pg_catalog.jsonb_agg(
                        pg_catalog.jsonb_build_object(
                            'id', destination.id,
                            'code', destination.code,
                            'evidence_id', destination.journey_topic_evidence_id,
                            'kind', destination.destination_kind,
                            'guidance_ar', destination.guidance_ar,
                            'guidance_en', destination.guidance_en,
                            'what_to_verify_ar', destination.what_to_verify_ar,
                            'what_to_verify_en', destination.what_to_verify_en,
                            'route_fact_id', destination.route_fact_definition_id,
                            'route_match_kind', destination.route_match_kind,
                            'route_match_value', destination.route_match_value,
                            'display_order', destination.display_order,
                            'is_primary', destination.is_primary
                        ) ORDER BY destination.display_order, destination.id
                    )
                    FROM navigator.journey_topic_destinations AS destination
                    WHERE destination.journey_topic_version_id = version.id
                ), '[]'::jsonb)
            ) INTO graph_payload
            FROM navigator.journey_topic_versions AS version
            WHERE version.id = candidate_version_id;

            IF graph_payload IS NULL THEN
                RETURN NULL;
            END IF;
            RETURN navigator.canonical_json_sha256(graph_payload);
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.journey_topic_version_is_eligible(
            candidate_version_id UUID
        )
        RETURNS BOOLEAN
        LANGUAGE sql
        STABLE
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
            SELECT EXISTS (
                SELECT 1
                FROM navigator.journey_topic_versions AS version
                JOIN navigator.business_activities AS activity
                  ON activity.id = version.activity_id AND activity.is_active
                JOIN navigator.review_events AS approval_review
                  ON approval_review.id = version.approval_review_event_id
                 AND approval_review.decision = 'approved'
                JOIN navigator.research_events AS approval_research
                  ON approval_research.id = approval_review.research_event_id
                 AND approval_research.journey_topic_version_id = version.id
                WHERE version.id = candidate_version_id
                  AND version.verification_status = 'approved'
                  AND version.is_current
                  AND version.coverage_state <> 'NOT_RESEARCHED'
                  AND version.last_verified_at = approval_review.reviewed_at
                  AND version.review_interval_days BETWEEN 30 AND 180
                  AND version.next_review_at = version.last_verified_at
                      + pg_catalog.make_interval(days => version.review_interval_days)
                  AND CURRENT_TIMESTAMP < version.next_review_at
                  AND approval_review.reviewed_at <= CURRENT_TIMESTAMP
                  AND approval_research.research_status = 'completed'
                  AND approval_research.recommendation = 'approve'
                  AND (version.effective_from IS NULL
                       OR version.effective_from <= CURRENT_DATE)
                  AND (version.effective_until IS NULL
                       OR CURRENT_DATE <= version.effective_until)
                  AND (
                      SELECT count(*) FROM navigator.journey_topic_evidence
                      WHERE journey_topic_version_id = version.id
                        AND evidence_role = 'primary'
                  ) = 1
                  AND NOT EXISTS (
                      SELECT 1
                      FROM navigator.journey_topic_evidence AS evidence
                      WHERE evidence.journey_topic_version_id = version.id
                        AND evidence.evidence_role <> 'historical'
                        AND (
                            NOT navigator.source_version_is_eligible_for_current_use(
                                evidence.source_version_id
                            )
                            OR NOT EXISTS (
                                SELECT 1
                                FROM navigator.research_event_evidence AS cited
                                WHERE cited.research_event_id = approval_research.id
                                  AND cited.source_version_id = evidence.source_version_id
                            )
                        )
                  )
                  AND NOT EXISTS (
                      SELECT 1
                      FROM navigator.journey_topic_fact_links AS link
                      JOIN navigator.fact_definitions AS fact
                        ON fact.id = link.fact_definition_id
                      WHERE link.journey_topic_version_id = version.id
                        AND (fact.verification_status <> 'approved' OR NOT fact.is_current
                             OR fact.privacy_class <> 'non_personal_business'
                             OR EXISTS (
                                 SELECT 1 FROM navigator.requirement_condition_facts
                                 WHERE fact_definition_id = fact.id
                             ))
                  )
                  AND NOT EXISTS (
                      SELECT 1
                      FROM navigator.journey_topic_destinations AS destination
                      JOIN navigator.journey_topic_evidence AS evidence
                        ON evidence.id = destination.journey_topic_evidence_id
                      WHERE destination.journey_topic_version_id = version.id
                        AND (evidence.evidence_role = 'historical'
                             OR NOT navigator.source_version_is_eligible_for_current_use(
                                 evidence.source_version_id
                             ))
                  )
                  AND (
                      version.coverage_state <> 'REQUIRES_OFFICIAL_CONFIRMATION'
                      OR EXISTS (
                          SELECT 1 FROM navigator.journey_topic_destinations
                          WHERE journey_topic_version_id = version.id
                      )
                  )
            )
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_requirement_actionability_version()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            predecessor navigator.requirement_actionability_versions%ROWTYPE;
            predecessor_requirement_id UUID;
            candidate_requirement_id UUID;
            calculated_hash TEXT;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.verification_status = 'approved'
                    OR EXISTS (
                        SELECT 1 FROM navigator.requirement_actionability_releases
                        WHERE requirement_actionability_version_id = OLD.id
                    )
                THEN
                    RAISE EXCEPTION 'reviewed actionability history is immutable';
                END IF;
                RETURN OLD;
            END IF;

            IF NEW.value_state = 'VERIFIED' THEN
                calculated_hash := navigator.canonical_json_sha256(NEW.value_payload);
                IF NEW.value_sha256 IS DISTINCT FROM calculated_hash THEN
                    RAISE EXCEPTION 'actionability payload hash does not match canonical JSON';
                END IF;
            END IF;

            IF TG_OP = 'INSERT' THEN
                IF NEW.supersedes_actionability_version_id IS NULL THEN
                    IF NEW.version_number <> 1 THEN
                        RAISE EXCEPTION 'first actionability version must be version 1';
                    END IF;
                ELSE
                    SELECT * INTO predecessor
                    FROM navigator.requirement_actionability_versions
                    WHERE id = NEW.supersedes_actionability_version_id
                    FOR UPDATE;
                    SELECT requirement_id INTO candidate_requirement_id
                    FROM navigator.requirement_versions
                    WHERE id = NEW.requirement_version_id;
                    SELECT requirement_id INTO predecessor_requirement_id
                    FROM navigator.requirement_versions
                    WHERE id = predecessor.requirement_version_id;
                    IF NOT FOUND
                        OR predecessor.code <> NEW.code
                        OR predecessor.detail_type <> NEW.detail_type
                        OR NEW.version_number <> predecessor.version_number + 1
                        OR candidate_requirement_id IS DISTINCT FROM predecessor_requirement_id
                    THEN
                        RAISE EXCEPTION '%',
                            'actionability supersession must be linear within one atomic detail';
                    END IF;
                END IF;
                IF NEW.verification_status NOT IN (
                        'pending_source_verification', 'pending_review'
                    )
                    OR NEW.approval_review_event_id IS NOT NULL
                    OR NEW.last_verified_at IS NOT NULL
                    OR NEW.review_interval_days IS NOT NULL
                    OR NEW.next_review_at IS NOT NULL
                    OR NEW.is_current
                THEN
                    RAISE EXCEPTION 'actionability versions begin in an unverified workflow state';
                END IF;
                RETURN NEW;
            END IF;

            IF NEW.id IS DISTINCT FROM OLD.id
                OR NEW.code IS DISTINCT FROM OLD.code
                OR NEW.version_number IS DISTINCT FROM OLD.version_number
                OR NEW.requirement_version_id IS DISTINCT FROM OLD.requirement_version_id
                OR NEW.supersedes_actionability_version_id IS DISTINCT FROM
                    OLD.supersedes_actionability_version_id
                OR NEW.created_at IS DISTINCT FROM OLD.created_at
            THEN
                RAISE EXCEPTION 'actionability version identity is immutable';
            END IF;
            IF OLD.verification_status = 'approved' AND (
                pg_catalog.to_jsonb(NEW)
                    - 'verification_status' - 'approval_review_event_id'
                    - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                    - 'is_current' - 'notes' - 'updated_at'
            ) IS DISTINCT FROM (
                pg_catalog.to_jsonb(OLD)
                    - 'verification_status' - 'approval_review_event_id'
                    - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                    - 'is_current' - 'notes' - 'updated_at'
            ) THEN
                RAISE EXCEPTION 'approved actionability meaning requires a new version';
            END IF;
            IF NEW.last_verified_at IS DISTINCT FROM OLD.last_verified_at
                OR NEW.review_interval_days IS DISTINCT FROM OLD.review_interval_days
                OR NEW.next_review_at IS DISTINCT FROM OLD.next_review_at
            THEN
                RAISE EXCEPTION 'actionability verification dates are database derived';
            END IF;
            IF NEW.approval_review_event_id IS NOT DISTINCT FROM
                OLD.approval_review_event_id
                AND NEW.verification_status IS DISTINCT FROM OLD.verification_status
            THEN
                RAISE EXCEPTION 'actionability status changes require a new exact-target review';
            END IF;
            IF NOT OLD.is_current AND NEW.is_current
                AND NEW.approval_review_event_id IS NOT DISTINCT FROM
                    OLD.approval_review_event_id
            THEN
                RAISE EXCEPTION 'restoring actionability requires a new review';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.apply_requirement_actionability_review()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            review_decision TEXT;
            review_time TIMESTAMPTZ;
            authorized_interval INTEGER;
            target_matches BOOLEAN;
            research_status_value TEXT;
            research_recommendation TEXT;
            old_review_time TIMESTAMPTZ;
            source_last_verified TIMESTAMPTZ;
        BEGIN
            IF NEW.approval_review_event_id IS NOT DISTINCT FROM
                OLD.approval_review_event_id
            THEN
                RETURN NEW;
            END IF;
            IF NEW.approval_review_event_id IS NULL THEN
                RAISE EXCEPTION 'actionability review cannot be cleared';
            END IF;

            SELECT review.decision, review.reviewed_at,
                   review.authorized_review_interval_days,
                   research.requirement_actionability_version_id = NEW.id,
                   research.research_status, research.recommendation
            INTO review_decision, review_time, authorized_interval, target_matches,
                 research_status_value, research_recommendation
            FROM navigator.review_events AS review
            JOIN navigator.research_events AS research
              ON research.id = review.research_event_id
            WHERE review.id = NEW.approval_review_event_id;

            IF NOT FOUND OR target_matches IS DISTINCT FROM TRUE THEN
                RAISE EXCEPTION 'review event does not target this actionability version';
            END IF;
            IF review_time > pg_catalog.clock_timestamp() THEN
                RAISE EXCEPTION 'future actionability reviews are prohibited';
            END IF;
            IF OLD.approval_review_event_id IS NOT NULL THEN
                SELECT reviewed_at INTO old_review_time
                FROM navigator.review_events
                WHERE id = OLD.approval_review_event_id;
                IF review_time <= old_review_time THEN
                    RAISE EXCEPTION 'replacement actionability review must be newer';
                END IF;
            END IF;

            IF NEW.verification_status = 'approved' THEN
                SELECT last_verified_at INTO source_last_verified
                FROM navigator.source_versions
                WHERE id = NEW.primary_source_version_id;
                IF review_decision <> 'approved'
                    OR research_status_value <> 'completed'
                    OR research_recommendation <> 'approve'
                    OR NOT navigator.source_version_is_eligible_for_current_use(
                        NEW.primary_source_version_id
                    )
                    OR NOT EXISTS (
                        SELECT 1
                        FROM navigator.review_events AS exact_review
                        JOIN navigator.research_event_evidence AS cited
                          ON cited.research_event_id = exact_review.research_event_id
                        WHERE exact_review.id = NEW.approval_review_event_id
                          AND cited.source_version_id = NEW.primary_source_version_id
                    )
                    OR review_time < source_last_verified
                    OR NOT EXISTS (
                        SELECT 1 FROM navigator.requirement_versions
                        WHERE id = NEW.requirement_version_id
                          AND verification_status = 'approved' AND is_current
                    )
                THEN
                    RAISE EXCEPTION '%',
                        'approved actionability requires exact current official evidence';
                END IF;
                NEW.last_verified_at := review_time;
                NEW.review_interval_days := COALESCE(authorized_interval, 90);
                NEW.next_review_at := review_time
                    + pg_catalog.make_interval(days => COALESCE(authorized_interval, 90));
                NEW.is_current := true;
            ELSE
                IF (NEW.verification_status = 'rejected' AND review_decision <> 'rejected')
                    OR (NEW.verification_status = 'conflicting'
                        AND review_decision <> 'blocked_by_conflict')
                    OR (NEW.verification_status = 'stale'
                        AND review_decision <> 'marked_stale')
                    OR (NEW.verification_status = 'expired'
                        AND review_decision <> 'marked_expired')
                    OR (NEW.verification_status = 'superseded'
                        AND review_decision <> 'marked_superseded')
                    OR (NEW.verification_status = 'historical'
                        AND review_decision <> 'marked_historical')
                THEN
                    RAISE EXCEPTION 'actionability status and review decision do not match';
                END IF;
                NEW.last_verified_at := NULL;
                NEW.review_interval_days := NULL;
                NEW.next_review_at := NULL;
                NEW.is_current := false;
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.requirement_actionability_version_is_eligible(
            candidate_version_id UUID
        )
        RETURNS BOOLEAN
        LANGUAGE sql
        STABLE
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
            SELECT EXISTS (
                SELECT 1
                FROM navigator.requirement_actionability_versions AS actionability
                JOIN navigator.review_events AS approval_review
                  ON approval_review.id = actionability.approval_review_event_id
                 AND approval_review.decision = 'approved'
                JOIN navigator.research_events AS approval_research
                  ON approval_research.id = approval_review.research_event_id
                 AND approval_research.requirement_actionability_version_id =
                     actionability.id
                WHERE actionability.id = candidate_version_id
                  AND actionability.value_state IN ('VERIFIED', 'NOT_APPLICABLE')
                  AND actionability.verification_status = 'approved'
                  AND actionability.is_current
                  AND actionability.last_verified_at = approval_review.reviewed_at
                  AND actionability.review_interval_days BETWEEN 30 AND 180
                  AND actionability.next_review_at = actionability.last_verified_at
                      + pg_catalog.make_interval(days => actionability.review_interval_days)
                  AND CURRENT_TIMESTAMP < actionability.next_review_at
                  AND approval_review.reviewed_at <= CURRENT_TIMESTAMP
                  AND approval_research.research_status = 'completed'
                  AND approval_research.recommendation = 'approve'
                  AND (actionability.effective_from IS NULL
                       OR actionability.effective_from <= CURRENT_DATE)
                  AND (actionability.effective_until IS NULL
                       OR CURRENT_DATE <= actionability.effective_until)
                  AND navigator.source_version_is_eligible_for_current_use(
                      actionability.primary_source_version_id
                  )
                  AND EXISTS (
                      SELECT 1 FROM navigator.research_event_evidence AS cited
                      WHERE cited.research_event_id = approval_research.id
                        AND cited.source_version_id =
                            actionability.primary_source_version_id
                  )
                  AND EXISTS (
                      SELECT 1 FROM navigator.published_requirement_versions AS published
                      WHERE published.requirement_version_id =
                          actionability.requirement_version_id
                  )
                  AND (
                      actionability.value_state <> 'VERIFIED'
                      OR actionability.value_sha256 =
                          navigator.canonical_json_sha256(actionability.value_payload)
                  )
            )
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_journey_topic_release_insert()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            next_number INTEGER;
            latest_withdrawal TIMESTAMPTZ;
            approval_time TIMESTAMPTZ;
            parent_approval_id UUID;
            parent_approval_time TIMESTAMPTZ;
        BEGIN
            PERFORM 1 FROM navigator.journey_topic_versions
            WHERE id = NEW.journey_topic_version_id FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'journey topic version does not exist';
            END IF;
            IF NEW.release_status <> 'released'
                OR NEW.withdrawn_at IS NOT NULL
                OR NEW.withdrawn_by_role IS NOT NULL
                OR NEW.withdrawal_reason IS NOT NULL
            THEN
                RAISE EXCEPTION 'new journey release cycles begin released';
            END IF;
            IF EXISTS (
                SELECT 1 FROM navigator.journey_topic_releases
                WHERE journey_topic_version_id = NEW.journey_topic_version_id
                  AND release_status = 'released'
            ) THEN
                RAISE EXCEPTION 'only one active journey release is allowed';
            END IF;
            SELECT COALESCE(max(release_number), 0) + 1, max(withdrawn_at)
            INTO next_number, latest_withdrawal
            FROM navigator.journey_topic_releases
            WHERE journey_topic_version_id = NEW.journey_topic_version_id;
            IF EXISTS (
                SELECT 1 FROM navigator.journey_topic_releases
                WHERE journey_topic_version_id = NEW.journey_topic_version_id
                  AND release_status <> 'withdrawn'
            ) THEN
                RAISE EXCEPTION 'previous journey releases must be withdrawn';
            END IF;

            SELECT version.approval_review_event_id, parent_review.reviewed_at
            INTO parent_approval_id, parent_approval_time
            FROM navigator.journey_topic_versions AS version
            JOIN navigator.review_events AS parent_review
              ON parent_review.id = version.approval_review_event_id
            WHERE version.id = NEW.journey_topic_version_id;
            SELECT review.reviewed_at INTO approval_time
            FROM navigator.review_events AS review
            JOIN navigator.research_events AS research
              ON research.id = review.research_event_id
            WHERE review.id = NEW.approval_review_event_id
              AND review.decision = 'approved'
              AND research.journey_topic_version_id = NEW.journey_topic_version_id
              AND research.research_status = 'completed'
              AND research.recommendation = 'approve';
            IF approval_time IS NULL
                OR NEW.approval_review_event_id = parent_approval_id
                OR approval_time <= parent_approval_time
                OR approval_time > pg_catalog.clock_timestamp()
            THEN
                RAISE EXCEPTION 'journey release requires a later distinct exact-target approval';
            END IF;
            IF latest_withdrawal IS NOT NULL AND approval_time <= latest_withdrawal THEN
                RAISE EXCEPTION 'journey rerelease requires review after withdrawal';
            END IF;
            IF NOT navigator.journey_topic_version_is_eligible(
                NEW.journey_topic_version_id
            ) THEN
                RAISE EXCEPTION 'journey topic is not eligible for release';
            END IF;
            IF NEW.topic_graph_sha256 IS DISTINCT FROM
                navigator.journey_topic_graph_sha256(NEW.journey_topic_version_id)
            THEN
                RAISE EXCEPTION 'journey release graph hash does not match controlled graph';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM navigator.journey_topic_evidence AS evidence
                WHERE evidence.journey_topic_version_id = NEW.journey_topic_version_id
                  AND evidence.evidence_role <> 'historical'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM navigator.review_events AS release_review
                      JOIN navigator.research_event_evidence AS cited
                        ON cited.research_event_id = release_review.research_event_id
                      WHERE release_review.id = NEW.approval_review_event_id
                        AND cited.source_version_id = evidence.source_version_id
                  )
            ) THEN
                RAISE EXCEPTION 'journey release approval must review the complete source graph';
            END IF;

            NEW.release_number := next_number;
            NEW.released_at := pg_catalog.clock_timestamp();
            NEW.created_at := NEW.released_at;
            NEW.updated_at := NEW.released_at;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_journey_topic_release_transition()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'journey release history is append preserving';
            END IF;
            PERFORM 1 FROM navigator.journey_topic_versions
            WHERE id = OLD.journey_topic_version_id FOR UPDATE;
            IF OLD.release_status <> 'released' OR NEW.release_status <> 'withdrawn' THEN
                RAISE EXCEPTION 'withdrawn journey releases cannot be reopened or rewritten';
            END IF;
            IF NEW.id IS DISTINCT FROM OLD.id
                OR NEW.journey_topic_version_id IS DISTINCT FROM OLD.journey_topic_version_id
                OR NEW.release_number IS DISTINCT FROM OLD.release_number
                OR NEW.approval_review_event_id IS DISTINCT FROM OLD.approval_review_event_id
                OR NEW.topic_graph_sha256 IS DISTINCT FROM OLD.topic_graph_sha256
                OR NEW.released_at IS DISTINCT FROM OLD.released_at
                OR NEW.created_at IS DISTINCT FROM OLD.created_at
            THEN
                RAISE EXCEPTION 'journey release cycle identity is immutable';
            END IF;
            IF NEW.withdrawn_at IS NOT NULL THEN
                RAISE EXCEPTION 'journey withdrawal timestamp is database derived';
            END IF;
            IF NEW.withdrawn_by_role IS NULL OR NEW.withdrawal_reason IS NULL
                OR btrim(NEW.withdrawal_reason) = ''
            THEN
                RAISE EXCEPTION 'journey withdrawal requires role and reason';
            END IF;
            NEW.withdrawn_at := pg_catalog.clock_timestamp();
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_actionability_release_insert()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            next_number INTEGER;
            latest_withdrawal TIMESTAMPTZ;
            approval_time TIMESTAMPTZ;
            parent_approval_id UUID;
            parent_approval_time TIMESTAMPTZ;
            primary_source UUID;
        BEGIN
            PERFORM 1 FROM navigator.requirement_actionability_versions
            WHERE id = NEW.requirement_actionability_version_id FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'actionability version does not exist';
            END IF;
            IF NEW.release_status <> 'released'
                OR NEW.withdrawn_at IS NOT NULL
                OR NEW.withdrawn_by_role IS NOT NULL
                OR NEW.withdrawal_reason IS NOT NULL
            THEN
                RAISE EXCEPTION 'new actionability release cycles begin released';
            END IF;
            IF EXISTS (
                SELECT 1 FROM navigator.requirement_actionability_releases
                WHERE requirement_actionability_version_id =
                      NEW.requirement_actionability_version_id
                  AND release_status = 'released'
            ) THEN
                RAISE EXCEPTION 'only one active actionability release is allowed';
            END IF;
            SELECT COALESCE(max(release_number), 0) + 1, max(withdrawn_at)
            INTO next_number, latest_withdrawal
            FROM navigator.requirement_actionability_releases
            WHERE requirement_actionability_version_id =
                  NEW.requirement_actionability_version_id;
            IF EXISTS (
                SELECT 1 FROM navigator.requirement_actionability_releases
                WHERE requirement_actionability_version_id =
                      NEW.requirement_actionability_version_id
                  AND release_status <> 'withdrawn'
            ) THEN
                RAISE EXCEPTION 'previous actionability releases must be withdrawn';
            END IF;

            SELECT actionability.approval_review_event_id,
                   parent_review.reviewed_at,
                   actionability.primary_source_version_id
            INTO parent_approval_id, parent_approval_time, primary_source
            FROM navigator.requirement_actionability_versions AS actionability
            JOIN navigator.review_events AS parent_review
              ON parent_review.id = actionability.approval_review_event_id
            WHERE actionability.id = NEW.requirement_actionability_version_id;
            SELECT review.reviewed_at INTO approval_time
            FROM navigator.review_events AS review
            JOIN navigator.research_events AS research
              ON research.id = review.research_event_id
            WHERE review.id = NEW.approval_review_event_id
              AND review.decision = 'approved'
              AND research.requirement_actionability_version_id =
                  NEW.requirement_actionability_version_id
              AND research.research_status = 'completed'
              AND research.recommendation = 'approve'
              AND EXISTS (
                  SELECT 1 FROM navigator.research_event_evidence AS cited
                  WHERE cited.research_event_id = research.id
                    AND cited.source_version_id = primary_source
              );
            IF approval_time IS NULL
                OR NEW.approval_review_event_id = parent_approval_id
                OR approval_time <= parent_approval_time
                OR approval_time > pg_catalog.clock_timestamp()
            THEN
                RAISE EXCEPTION '%',
                    'actionability release requires a later distinct exact-target approval';
            END IF;
            IF latest_withdrawal IS NOT NULL AND approval_time <= latest_withdrawal THEN
                RAISE EXCEPTION 'actionability rerelease requires review after withdrawal';
            END IF;
            IF NOT navigator.requirement_actionability_version_is_eligible(
                NEW.requirement_actionability_version_id
            ) THEN
                RAISE EXCEPTION 'actionability is not eligible for release';
            END IF;

            NEW.release_number := next_number;
            NEW.released_at := pg_catalog.clock_timestamp();
            NEW.created_at := NEW.released_at;
            NEW.updated_at := NEW.released_at;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_actionability_release_transition()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'actionability release history is append preserving';
            END IF;
            PERFORM 1 FROM navigator.requirement_actionability_versions
            WHERE id = OLD.requirement_actionability_version_id FOR UPDATE;
            IF OLD.release_status <> 'released' OR NEW.release_status <> 'withdrawn' THEN
                RAISE EXCEPTION 'withdrawn actionability releases cannot be reopened or rewritten';
            END IF;
            IF NEW.id IS DISTINCT FROM OLD.id
                OR NEW.requirement_actionability_version_id IS DISTINCT FROM
                    OLD.requirement_actionability_version_id
                OR NEW.release_number IS DISTINCT FROM OLD.release_number
                OR NEW.approval_review_event_id IS DISTINCT FROM OLD.approval_review_event_id
                OR NEW.released_at IS DISTINCT FROM OLD.released_at
                OR NEW.created_at IS DISTINCT FROM OLD.created_at
            THEN
                RAISE EXCEPTION 'actionability release cycle identity is immutable';
            END IF;
            IF NEW.withdrawn_at IS NOT NULL THEN
                RAISE EXCEPTION 'actionability withdrawal timestamp is database derived';
            END IF;
            IF NEW.withdrawn_by_role IS NULL OR NEW.withdrawal_reason IS NULL
                OR btrim(NEW.withdrawal_reason) = ''
            THEN
                RAISE EXCEPTION 'actionability withdrawal requires role and reason';
            END IF;
            NEW.withdrawn_at := pg_catalog.clock_timestamp();
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.guard_active_content_release_dependency()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            has_dependency BOOLEAN := false;
            old_status TEXT;
            new_status TEXT;
            identity_changed BOOLEAN;
        BEGIN
            CASE TG_TABLE_NAME
                WHEN 'journey_topic_versions' THEN
                    SELECT EXISTS (
                        SELECT 1 FROM navigator.journey_topic_releases
                        WHERE release_status = 'released'
                          AND journey_topic_version_id = OLD.id
                    ) INTO has_dependency;
                WHEN 'requirement_actionability_versions' THEN
                    SELECT EXISTS (
                        SELECT 1 FROM navigator.requirement_actionability_releases
                        WHERE release_status = 'released'
                          AND requirement_actionability_version_id = OLD.id
                    ) INTO has_dependency;
                WHEN 'fact_definitions' THEN
                    SELECT EXISTS (
                        SELECT 1
                        FROM navigator.journey_topic_releases AS release
                        WHERE release.release_status = 'released'
                          AND (
                              EXISTS (
                                  SELECT 1 FROM navigator.journey_topic_fact_links
                                  WHERE journey_topic_version_id =
                                        release.journey_topic_version_id
                                    AND fact_definition_id = OLD.id
                              ) OR EXISTS (
                                  SELECT 1 FROM navigator.journey_topic_destinations
                                  WHERE journey_topic_version_id =
                                        release.journey_topic_version_id
                                    AND route_fact_definition_id = OLD.id
                              )
                          )
                    ) INTO has_dependency;
                WHEN 'business_activities' THEN
                    SELECT EXISTS (
                        SELECT 1
                        FROM navigator.journey_topic_releases AS release
                        JOIN navigator.journey_topic_versions AS version
                          ON version.id = release.journey_topic_version_id
                        WHERE release.release_status = 'released'
                          AND version.activity_id = OLD.id
                    ) INTO has_dependency;
                WHEN 'source_versions' THEN
                    SELECT EXISTS (
                        SELECT 1
                        FROM navigator.journey_topic_releases AS release
                        JOIN navigator.journey_topic_evidence AS evidence
                          ON evidence.journey_topic_version_id =
                             release.journey_topic_version_id
                        WHERE release.release_status = 'released'
                          AND evidence.source_version_id = OLD.id
                        UNION ALL
                        SELECT 1
                        FROM navigator.requirement_actionability_releases AS release
                        JOIN navigator.requirement_actionability_versions AS actionability
                          ON actionability.id =
                             release.requirement_actionability_version_id
                        WHERE release.release_status = 'released'
                          AND actionability.primary_source_version_id = OLD.id
                    ) INTO has_dependency;
                WHEN 'sources' THEN
                    SELECT EXISTS (
                        SELECT 1 FROM navigator.source_versions AS source_version
                        WHERE source_version.source_id = OLD.id
                          AND (
                              EXISTS (
                                  SELECT 1
                                  FROM navigator.journey_topic_releases AS release
                                  JOIN navigator.journey_topic_evidence AS evidence
                                    ON evidence.journey_topic_version_id =
                                       release.journey_topic_version_id
                                  WHERE release.release_status = 'released'
                                    AND evidence.source_version_id = source_version.id
                              ) OR EXISTS (
                                  SELECT 1
                                  FROM navigator.requirement_actionability_releases AS release
                                  JOIN navigator.requirement_actionability_versions AS actionability
                                    ON actionability.id =
                                       release.requirement_actionability_version_id
                                  WHERE release.release_status = 'released'
                                    AND actionability.primary_source_version_id = source_version.id
                              )
                          )
                    ) INTO has_dependency;
                WHEN 'domains' THEN
                    SELECT EXISTS (
                        SELECT 1 FROM navigator.source_versions AS source_version
                        WHERE source_version.domain_id_at_review = OLD.id
                          AND (
                              EXISTS (
                                  SELECT 1
                                  FROM navigator.journey_topic_releases AS release
                                  JOIN navigator.journey_topic_evidence AS evidence
                                    ON evidence.journey_topic_version_id =
                                       release.journey_topic_version_id
                                  WHERE release.release_status = 'released'
                                    AND evidence.source_version_id = source_version.id
                              ) OR EXISTS (
                                  SELECT 1
                                  FROM navigator.requirement_actionability_releases AS release
                                  JOIN navigator.requirement_actionability_versions AS actionability
                                    ON actionability.id =
                                       release.requirement_actionability_version_id
                                  WHERE release.release_status = 'released'
                                    AND actionability.primary_source_version_id = source_version.id
                              )
                          )
                    ) INTO has_dependency;
                WHEN 'platforms' THEN
                    SELECT EXISTS (
                        SELECT 1 FROM navigator.source_versions AS source_version
                        WHERE source_version.platform_id_at_review = OLD.id
                          AND (
                              EXISTS (
                                  SELECT 1
                                  FROM navigator.journey_topic_releases AS release
                                  JOIN navigator.journey_topic_evidence AS evidence
                                    ON evidence.journey_topic_version_id =
                                       release.journey_topic_version_id
                                  WHERE release.release_status = 'released'
                                    AND evidence.source_version_id = source_version.id
                              ) OR EXISTS (
                                  SELECT 1
                                  FROM navigator.requirement_actionability_releases AS release
                                  JOIN navigator.requirement_actionability_versions AS actionability
                                    ON actionability.id =
                                       release.requirement_actionability_version_id
                                  WHERE release.release_status = 'released'
                                    AND actionability.primary_source_version_id = source_version.id
                              )
                          )
                    ) INTO has_dependency;
                WHEN 'government_entities' THEN
                    SELECT EXISTS (
                        SELECT 1
                        FROM navigator.requirement_actionability_releases AS release
                        JOIN navigator.requirement_actionability_versions AS actionability
                          ON actionability.id =
                             release.requirement_actionability_version_id
                        JOIN navigator.requirement_versions AS requirement_version
                          ON requirement_version.id = actionability.requirement_version_id
                        WHERE release.release_status = 'released'
                          AND requirement_version.responsible_entity_id = OLD.id
                        UNION ALL
                        SELECT 1
                        FROM navigator.source_versions AS source_version
                        JOIN navigator.sources AS stable_source
                          ON stable_source.id = source_version.source_id
                        JOIN navigator.domains AS source_domain
                          ON source_domain.id = source_version.domain_id_at_review
                        LEFT JOIN navigator.platforms AS source_platform
                          ON source_platform.id = source_version.platform_id_at_review
                        WHERE (
                            stable_source.responsible_entity_id = OLD.id
                            OR source_domain.responsible_entity_id = OLD.id
                            OR source_platform.responsible_entity_id = OLD.id
                        ) AND (
                            EXISTS (
                                SELECT 1
                                FROM navigator.journey_topic_releases AS release
                                JOIN navigator.journey_topic_evidence AS evidence
                                  ON evidence.journey_topic_version_id =
                                     release.journey_topic_version_id
                                WHERE release.release_status = 'released'
                                  AND evidence.source_version_id = source_version.id
                            ) OR EXISTS (
                                SELECT 1
                                FROM navigator.requirement_actionability_releases AS release
                                JOIN navigator.requirement_actionability_versions AS actionability
                                  ON actionability.id =
                                     release.requirement_actionability_version_id
                                WHERE release.release_status = 'released'
                                  AND actionability.primary_source_version_id = source_version.id
                            )
                        )
                    ) INTO has_dependency;
            END CASE;

            IF NOT has_dependency THEN
                RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
            END IF;
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'active content release protects dependency history';
            END IF;
            old_status := COALESCE(
                pg_catalog.to_jsonb(OLD)->>'verification_status',
                pg_catalog.to_jsonb(OLD)->>'review_status'
            );
            new_status := COALESCE(
                pg_catalog.to_jsonb(NEW)->>'verification_status',
                pg_catalog.to_jsonb(NEW)->>'review_status'
            );
            IF (old_status <> 'approved' AND new_status = 'approved')
                OR (TG_TABLE_NAME IN (
                        'source_versions', 'fact_definitions',
                        'journey_topic_versions', 'requirement_actionability_versions'
                    )
                    AND NOT COALESCE(
                        (pg_catalog.to_jsonb(OLD)->>'is_current')::boolean, false
                    )
                    AND COALESCE(
                        (pg_catalog.to_jsonb(NEW)->>'is_current')::boolean, false
                    ))
            THEN
                RAISE EXCEPTION 'active content release dependency cannot be restored';
            END IF;
            IF TG_TABLE_NAME = 'business_activities' THEN
                IF NOT OLD.is_active AND NEW.is_active THEN
                    RAISE EXCEPTION 'active content release dependency cannot be restored';
                END IF;
                identity_changed := (
                    pg_catalog.to_jsonb(NEW) - 'is_active' - 'updated_at'
                ) IS DISTINCT FROM (
                    pg_catalog.to_jsonb(OLD) - 'is_active' - 'updated_at'
                );
            ELSE
                identity_changed := (
                    pg_catalog.to_jsonb(NEW)
                        - 'verification_status' - 'review_status'
                        - 'verification_review_event_id' - 'approval_review_event_id'
                        - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                        - 'is_current' - 'notes' - 'updated_at'
                ) IS DISTINCT FROM (
                    pg_catalog.to_jsonb(OLD)
                        - 'verification_status' - 'review_status'
                        - 'verification_review_event_id' - 'approval_review_event_id'
                        - 'last_verified_at' - 'review_interval_days' - 'next_review_at'
                        - 'is_current' - 'notes' - 'updated_at'
                );
            END IF;
            IF identity_changed THEN
                RAISE EXCEPTION 'active content release protects dependency identity';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE VIEW navigator.released_journey_topic_versions AS
        SELECT
            release.id AS release_id,
            release.release_number,
            release.released_at,
            release.topic_graph_sha256,
            topic.id AS journey_topic_id,
            topic.code AS journey_topic_code,
            version.id AS journey_topic_version_id,
            version.version_number,
            activity.id AS activity_id,
            activity.code AS activity_code,
            version.title_ar,
            version.title_en,
            version.coverage_state,
            version.limitation_type,
            version.verified_summary_ar,
            version.verified_summary_en,
            version.limitation_summary_ar,
            version.limitation_summary_en,
            version.what_to_verify_ar,
            version.what_to_verify_en,
            version.last_verified_at,
            version.next_review_at
        FROM navigator.journey_topic_releases AS release
        JOIN navigator.journey_topic_versions AS version
          ON version.id = release.journey_topic_version_id
        JOIN navigator.journey_topics AS topic
          ON topic.id = version.journey_topic_id
        JOIN navigator.business_activities AS activity
          ON activity.id = version.activity_id
        JOIN navigator.review_events AS release_review
          ON release_review.id = release.approval_review_event_id
         AND release_review.decision = 'approved'
        JOIN navigator.research_events AS release_research
          ON release_research.id = release_review.research_event_id
         AND release_research.journey_topic_version_id = version.id
        WHERE release.release_status = 'released'
          AND release.approval_review_event_id <> version.approval_review_event_id
          AND release_review.reviewed_at > version.last_verified_at
          AND release_review.reviewed_at <= CURRENT_TIMESTAMP
          AND release_research.research_status = 'completed'
          AND release_research.recommendation = 'approve'
          AND release.topic_graph_sha256 =
              navigator.journey_topic_graph_sha256(version.id)
          AND navigator.journey_topic_version_is_eligible(version.id)
        """
    )

    execute(
        """
        CREATE VIEW navigator.released_requirement_actionability_versions AS
        SELECT
            release.id AS release_id,
            release.release_number,
            release.released_at,
            actionability.id AS requirement_actionability_version_id,
            actionability.code,
            actionability.version_number,
            actionability.requirement_version_id,
            actionability.detail_type,
            actionability.value_state,
            actionability.value_schema_version,
            actionability.value_payload,
            actionability.value_sha256,
            actionability.primary_source_version_id,
            actionability.official_excerpt_ar,
            actionability.official_excerpt_en,
            actionability.excerpt_locator,
            actionability.display_order,
            actionability.last_verified_at,
            actionability.next_review_at,
            source.resolved_url AS official_url,
            stable_source.official_title_ar AS official_source_title_ar,
            stable_source.official_title_en AS official_source_title_en,
            stable_source.responsible_entity_id
        FROM navigator.requirement_actionability_releases AS release
        JOIN navigator.requirement_actionability_versions AS actionability
          ON actionability.id = release.requirement_actionability_version_id
        JOIN navigator.source_versions AS source
          ON source.id = actionability.primary_source_version_id
        JOIN navigator.sources AS stable_source
          ON stable_source.id = source.source_id
        JOIN navigator.review_events AS release_review
          ON release_review.id = release.approval_review_event_id
         AND release_review.decision = 'approved'
        JOIN navigator.research_events AS release_research
          ON release_research.id = release_review.research_event_id
         AND release_research.requirement_actionability_version_id = actionability.id
        WHERE release.release_status = 'released'
          AND release.approval_review_event_id <> actionability.approval_review_event_id
          AND release_review.reviewed_at > actionability.last_verified_at
          AND release_review.reviewed_at <= CURRENT_TIMESTAMP
          AND release_research.research_status = 'completed'
          AND release_research.recommendation = 'approve'
          AND EXISTS (
              SELECT 1 FROM navigator.research_event_evidence AS cited
              WHERE cited.research_event_id = release_research.id
                AND cited.source_version_id = actionability.primary_source_version_id
          )
          AND navigator.requirement_actionability_version_is_eligible(actionability.id)
        """
    )

    execute(
        """
        CREATE TRIGGER trg_10_guard_journey_topic_identity
        BEFORE UPDATE OR DELETE ON navigator.journey_topics
        FOR EACH ROW EXECUTE FUNCTION navigator.guard_journey_topic_identity()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_10_validate_journey_topic_version
        BEFORE INSERT OR UPDATE OR DELETE ON navigator.journey_topic_versions
        FOR EACH ROW EXECUTE FUNCTION navigator.validate_journey_topic_version()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_20_apply_journey_topic_review
        BEFORE UPDATE ON navigator.journey_topic_versions
        FOR EACH ROW EXECUTE FUNCTION navigator.apply_journey_topic_review()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_90_set_updated_at
        BEFORE UPDATE ON navigator.journey_topic_versions
        FOR EACH ROW EXECUTE FUNCTION navigator.set_updated_at_on_change()
        """
    )

    for table_name in (
        "journey_topic_evidence",
        "journey_topic_requirement_links",
        "journey_topic_fact_links",
        "journey_topic_destinations",
    ):
        execute(
            f"CREATE TRIGGER trg_10_guard_journey_topic_child "
            f"BEFORE INSERT OR UPDATE OR DELETE ON navigator.{table_name} "
            "FOR EACH ROW EXECUTE FUNCTION navigator.guard_journey_topic_child()"
        )
    execute(
        """
        CREATE TRIGGER trg_05_validate_navigation_fact_separation
        BEFORE INSERT OR UPDATE ON navigator.journey_topic_fact_links
        FOR EACH ROW EXECUTE FUNCTION navigator.validate_navigation_fact_separation()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_05_validate_navigation_fact_separation
        BEFORE INSERT OR UPDATE ON navigator.requirement_condition_facts
        FOR EACH ROW EXECUTE FUNCTION navigator.validate_navigation_fact_separation()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_05_validate_journey_destination
        BEFORE INSERT OR UPDATE ON navigator.journey_topic_destinations
        FOR EACH ROW EXECUTE FUNCTION navigator.validate_journey_destination()
        """
    )

    for table_name in (
        "journey_topic_versions",
        "journey_topic_evidence",
        "journey_topic_requirement_links",
        "journey_topic_fact_links",
        "journey_topic_destinations",
    ):
        execute(
            f"CREATE CONSTRAINT TRIGGER trg_80_validate_journey_topic_graph "
            f"AFTER INSERT OR UPDATE OR DELETE ON navigator.{table_name} "
            "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
            "EXECUTE FUNCTION navigator.validate_journey_topic_graph()"
        )

    execute(
        """
        CREATE TRIGGER trg_10_validate_journey_topic_release_insert
        BEFORE INSERT ON navigator.journey_topic_releases
        FOR EACH ROW EXECUTE FUNCTION navigator.validate_journey_topic_release_insert()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_10_validate_journey_topic_release_transition
        BEFORE UPDATE OR DELETE ON navigator.journey_topic_releases
        FOR EACH ROW EXECUTE FUNCTION navigator.validate_journey_topic_release_transition()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_90_set_updated_at
        BEFORE UPDATE ON navigator.journey_topic_releases
        FOR EACH ROW EXECUTE FUNCTION navigator.set_updated_at_on_change()
        """
    )

    execute(
        """
        CREATE TRIGGER trg_10_validate_requirement_actionability_version
        BEFORE INSERT OR UPDATE OR DELETE
        ON navigator.requirement_actionability_versions
        FOR EACH ROW
        EXECUTE FUNCTION navigator.validate_requirement_actionability_version()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_20_apply_requirement_actionability_review
        BEFORE UPDATE ON navigator.requirement_actionability_versions
        FOR EACH ROW EXECUTE FUNCTION navigator.apply_requirement_actionability_review()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_90_set_updated_at
        BEFORE UPDATE ON navigator.requirement_actionability_versions
        FOR EACH ROW EXECUTE FUNCTION navigator.set_updated_at_on_change()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_10_validate_actionability_release_insert
        BEFORE INSERT ON navigator.requirement_actionability_releases
        FOR EACH ROW EXECUTE FUNCTION navigator.validate_actionability_release_insert()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_10_validate_actionability_release_transition
        BEFORE UPDATE OR DELETE ON navigator.requirement_actionability_releases
        FOR EACH ROW EXECUTE FUNCTION navigator.validate_actionability_release_transition()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_90_set_updated_at
        BEFORE UPDATE ON navigator.requirement_actionability_releases
        FOR EACH ROW EXECUTE FUNCTION navigator.set_updated_at_on_change()
        """
    )

    for table_name in (
        "business_activities",
        "fact_definitions",
        "government_entities",
        "journey_topic_versions",
        "platforms",
        "requirement_actionability_versions",
        "domains",
        "sources",
        "source_versions",
    ):
        execute(
            f"CREATE TRIGGER trg_06_guard_active_content_release_dependency "
            f"BEFORE UPDATE OR DELETE ON navigator.{table_name} "
            "FOR EACH ROW EXECUTE FUNCTION "
            "navigator.guard_active_content_release_dependency()"
        )


def downgrade() -> None:
    """Remove only an entirely empty journey and actionability structure."""
    execute = op.execute

    execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM navigator.journey_topics)
                OR EXISTS (SELECT 1 FROM navigator.journey_topic_versions)
                OR EXISTS (SELECT 1 FROM navigator.journey_topic_evidence)
                OR EXISTS (SELECT 1 FROM navigator.journey_topic_requirement_links)
                OR EXISTS (SELECT 1 FROM navigator.journey_topic_fact_links)
                OR EXISTS (SELECT 1 FROM navigator.journey_topic_destinations)
                OR EXISTS (SELECT 1 FROM navigator.journey_topic_releases)
                OR EXISTS (SELECT 1 FROM navigator.requirement_actionability_versions)
                OR EXISTS (SELECT 1 FROM navigator.requirement_actionability_releases)
                OR EXISTS (
                    SELECT 1 FROM navigator.research_events
                    WHERE journey_topic_version_id IS NOT NULL
                       OR requirement_actionability_version_id IS NOT NULL
                )
            THEN
                RAISE EXCEPTION
                    '0005 downgrade requires all new tables and research targets to be empty';
            END IF;
        END
        $$
        """
    )

    execute("DROP VIEW navigator.released_requirement_actionability_versions")
    execute("DROP VIEW navigator.released_journey_topic_versions")

    for table_name in (
        "business_activities",
        "fact_definitions",
        "government_entities",
        "journey_topic_versions",
        "platforms",
        "requirement_actionability_versions",
        "domains",
        "sources",
        "source_versions",
    ):
        execute(
            f"DROP TRIGGER trg_06_guard_active_content_release_dependency ON navigator.{table_name}"
        )

    execute("DROP TRIGGER trg_90_set_updated_at ON navigator.requirement_actionability_releases")
    execute(
        "DROP TRIGGER trg_10_validate_actionability_release_transition "
        "ON navigator.requirement_actionability_releases"
    )
    execute(
        "DROP TRIGGER trg_10_validate_actionability_release_insert "
        "ON navigator.requirement_actionability_releases"
    )
    execute("DROP TRIGGER trg_90_set_updated_at ON navigator.requirement_actionability_versions")
    execute(
        "DROP TRIGGER trg_20_apply_requirement_actionability_review "
        "ON navigator.requirement_actionability_versions"
    )
    execute(
        "DROP TRIGGER trg_10_validate_requirement_actionability_version "
        "ON navigator.requirement_actionability_versions"
    )
    execute("DROP TRIGGER trg_90_set_updated_at ON navigator.journey_topic_releases")
    execute(
        "DROP TRIGGER trg_10_validate_journey_topic_release_transition "
        "ON navigator.journey_topic_releases"
    )
    execute(
        "DROP TRIGGER trg_10_validate_journey_topic_release_insert "
        "ON navigator.journey_topic_releases"
    )

    for table_name in (
        "journey_topic_destinations",
        "journey_topic_fact_links",
        "journey_topic_requirement_links",
        "journey_topic_evidence",
        "journey_topic_versions",
    ):
        execute(f"DROP TRIGGER trg_80_validate_journey_topic_graph ON navigator.{table_name}")
    execute(
        "DROP TRIGGER trg_05_validate_journey_destination ON navigator.journey_topic_destinations"
    )
    execute(
        "DROP TRIGGER trg_05_validate_navigation_fact_separation "
        "ON navigator.requirement_condition_facts"
    )
    execute(
        "DROP TRIGGER trg_05_validate_navigation_fact_separation "
        "ON navigator.journey_topic_fact_links"
    )
    for table_name in (
        "journey_topic_destinations",
        "journey_topic_fact_links",
        "journey_topic_requirement_links",
        "journey_topic_evidence",
    ):
        execute(f"DROP TRIGGER trg_10_guard_journey_topic_child ON navigator.{table_name}")
    execute("DROP TRIGGER trg_90_set_updated_at ON navigator.journey_topic_versions")
    execute("DROP TRIGGER trg_20_apply_journey_topic_review ON navigator.journey_topic_versions")
    execute(
        "DROP TRIGGER trg_10_validate_journey_topic_version ON navigator.journey_topic_versions"
    )
    execute("DROP TRIGGER trg_10_guard_journey_topic_identity ON navigator.journey_topics")

    for signature in (
        "navigator.guard_active_content_release_dependency()",
        "navigator.validate_actionability_release_transition()",
        "navigator.validate_actionability_release_insert()",
        "navigator.requirement_actionability_version_is_eligible(UUID)",
        "navigator.apply_requirement_actionability_review()",
        "navigator.validate_requirement_actionability_version()",
        "navigator.validate_journey_topic_release_transition()",
        "navigator.validate_journey_topic_release_insert()",
        "navigator.journey_topic_version_is_eligible(UUID)",
        "navigator.journey_topic_graph_sha256(UUID)",
        "navigator.canonical_json_sha256(JSONB)",
        "navigator.canonical_json_text(JSONB)",
        "navigator.validate_journey_topic_graph()",
        "navigator.validate_journey_destination()",
        "navigator.validate_navigation_fact_separation()",
        "navigator.guard_journey_topic_child()",
        "navigator.apply_journey_topic_review()",
        "navigator.validate_journey_topic_version()",
        "navigator.guard_journey_topic_identity()",
        "navigator.source_version_is_eligible_for_current_use(UUID)",
    ):
        execute(f"DROP FUNCTION {signature}")

    execute("DROP INDEX navigator.ix_research_events_requirement_actionability_version_id")
    execute("DROP INDEX navigator.ix_research_events_journey_topic_version_id")
    execute(
        """
        ALTER TABLE navigator.research_events
            DROP CONSTRAINT ck_research_events_exactly_one_target,
            DROP CONSTRAINT fk_research_events_requirement_actionability_version,
            DROP CONSTRAINT fk_research_events_journey_topic_version,
            DROP COLUMN requirement_actionability_version_id,
            DROP COLUMN journey_topic_version_id,
            ADD CONSTRAINT ck_research_events_exactly_one_target CHECK (
                num_nonnulls(
                    government_entity_id, platform_id, domain_id, source_id,
                    source_version_id, requirement_version_id, requirement_source_id
                ) = 1
            )
        """
    )

    for table_name in (
        "requirement_actionability_releases",
        "requirement_actionability_versions",
        "journey_topic_releases",
        "journey_topic_destinations",
        "journey_topic_fact_links",
        "journey_topic_requirement_links",
        "journey_topic_evidence",
        "journey_topic_versions",
        "journey_topics",
    ):
        execute(f"DROP TABLE navigator.{table_name}")
