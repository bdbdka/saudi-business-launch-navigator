"""Create publication cycles, immutable evidence snapshots, and eligibility.

Revision ID: 0003_publication_eligibility
Revises: 0002_requirement_evidence
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_publication_eligibility"
down_revision: str | None = "0002_requirement_evidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def execute(sql: str) -> None:
    """Execute one explicitly schema-qualified PostgreSQL statement."""
    op.execute(sa.text(sql))


def upgrade() -> None:
    """Create append-preserving publication history and fail-closed eligibility."""
    execute(
        """
        CREATE TABLE navigator.requirement_publications (
            id UUID NOT NULL,
            requirement_version_id UUID NOT NULL,
            publication_number INTEGER NOT NULL,
            primary_requirement_source_id UUID NOT NULL,
            approval_review_event_id UUID NOT NULL,
            publication_status TEXT DEFAULT 'published' NOT NULL,
            published_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            withdrawn_at TIMESTAMPTZ,
            withdrawn_by_role TEXT,
            withdrawal_reason TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_requirement_publications PRIMARY KEY (id),
            CONSTRAINT uq_requirement_publications_publication_number
                UNIQUE (requirement_version_id, publication_number),
            CONSTRAINT uq_requirement_publications_approval_review_event
                UNIQUE (approval_review_event_id),
            CONSTRAINT ck_requirement_publications_positive_publication_number
                CHECK (publication_number > 0),
            CONSTRAINT ck_requirement_publications_publication_status
                CHECK (publication_status IN ('published', 'withdrawn')),
            CONSTRAINT ck_requirement_publications_withdrawal_state CHECK (
                (
                    publication_status = 'published'
                    AND withdrawn_at IS NULL
                    AND withdrawn_by_role IS NULL
                    AND withdrawal_reason IS NULL
                )
                OR
                (
                    publication_status = 'withdrawn'
                    AND withdrawn_at IS NOT NULL
                    AND withdrawn_at >= published_at
                    AND withdrawn_by_role IS NOT NULL
                    AND withdrawn_by_role ~ '^[a-z][a-z0-9_]*$'
                    AND withdrawal_reason IS NOT NULL
                    AND btrim(withdrawal_reason) <> ''
                )
            ),
            CONSTRAINT fk_requirement_publications_requirement_version
                FOREIGN KEY (requirement_version_id)
                REFERENCES navigator.requirement_versions (id) ON DELETE RESTRICT,
            CONSTRAINT fk_requirement_publications_primary_source
                FOREIGN KEY (primary_requirement_source_id)
                REFERENCES navigator.requirement_sources (id) ON DELETE RESTRICT,
            CONSTRAINT fk_requirement_publications_approval_review
                FOREIGN KEY (approval_review_event_id)
                REFERENCES navigator.review_events (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE UNIQUE INDEX uq_requirement_publications_one_active "
        "ON navigator.requirement_publications (requirement_version_id) "
        "WHERE publication_status = 'published'"
    )
    execute(
        "CREATE INDEX ix_requirement_publications_primary_source "
        "ON navigator.requirement_publications (primary_requirement_source_id)"
    )
    execute(
        "CREATE INDEX ix_requirement_publications_status "
        "ON navigator.requirement_publications (publication_status)"
    )

    execute(
        """
        CREATE TABLE navigator.requirement_publication_sources (
            publication_id UUID NOT NULL,
            requirement_source_id UUID NOT NULL,
            source_role_at_publication TEXT NOT NULL,
            official_excerpt_ar_at_publication TEXT,
            official_excerpt_en_at_publication TEXT,
            excerpt_locator_at_publication TEXT,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_requirement_publication_sources
                PRIMARY KEY (publication_id, requirement_source_id),
            CONSTRAINT ck_requirement_publication_sources_source_role CHECK (
                source_role_at_publication IN (
                    'primary', 'supporting', 'clarifying', 'conflicting',
                    'superseding', 'historical'
                )
            ),
            CONSTRAINT ck_requirement_publication_sources_relied_evidence_complete CHECK (
                source_role_at_publication = 'historical'
                OR (
                    official_excerpt_ar_at_publication IS NOT NULL
                    AND btrim(official_excerpt_ar_at_publication) <> ''
                    AND excerpt_locator_at_publication IS NOT NULL
                    AND btrim(excerpt_locator_at_publication) <> ''
                )
            ),
            CONSTRAINT fk_publication_sources_publication
                FOREIGN KEY (publication_id)
                REFERENCES navigator.requirement_publications (id) ON DELETE RESTRICT,
            CONSTRAINT fk_publication_sources_requirement_source
                FOREIGN KEY (requirement_source_id)
                REFERENCES navigator.requirement_sources (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE UNIQUE INDEX uq_publication_sources_one_primary "
        "ON navigator.requirement_publication_sources (publication_id) "
        "WHERE source_role_at_publication = 'primary'"
    )
    execute(
        "CREATE INDEX ix_requirement_publication_sources_requirement_source_id "
        "ON navigator.requirement_publication_sources (requirement_source_id)"
    )

    execute(
        """
        CREATE FUNCTION navigator.is_approved_and_fresh(
            status_value TEXT,
            review_event_id UUID,
            last_verified TIMESTAMPTZ,
            interval_days INTEGER,
            next_review TIMESTAMPTZ,
            target_kind TEXT,
            target_id UUID
        )
        RETURNS BOOLEAN
        LANGUAGE sql
        STABLE
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
            SELECT COALESCE(
                status_value = 'approved'
                AND review_event_id IS NOT NULL
                AND last_verified IS NOT NULL
                AND interval_days BETWEEN 30 AND 180
                AND next_review =
                    last_verified + pg_catalog.make_interval(days => interval_days)
                AND CURRENT_TIMESTAMP < next_review
                AND EXISTS (
                    SELECT 1
                    FROM navigator.review_events AS verification_review
                    JOIN navigator.research_events AS verification_research
                      ON verification_research.id =
                         verification_review.research_event_id
                    WHERE verification_review.id = review_event_id
                      AND verification_review.decision = 'approved'
                      AND (
                          CASE target_kind
                              WHEN 'government_entity'
                                  THEN verification_research.government_entity_id
                                      = target_id
                              WHEN 'platform'
                                  THEN verification_research.platform_id = target_id
                              WHEN 'domain'
                                  THEN verification_research.domain_id = target_id
                              WHEN 'source'
                                  THEN verification_research.source_id = target_id
                              WHEN 'source_version'
                                  THEN verification_research.source_version_id = target_id
                              ELSE false
                          END
                      ) IS TRUE
                ),
                false
            )
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.requirement_candidate_is_eligible(
            candidate_requirement_version_id UUID,
            candidate_primary_source_id UUID,
            candidate_approval_review_id UUID
        )
        RETURNS BOOLEAN
        LANGUAGE sql
        STABLE
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
            SELECT EXISTS (
                SELECT 1
                FROM navigator.requirement_versions AS rv
                JOIN navigator.government_entities AS requirement_entity
                  ON requirement_entity.id = rv.responsible_entity_id
                JOIN navigator.review_events AS approval_review
                  ON approval_review.id = candidate_approval_review_id
                 AND approval_review.decision = 'approved'
                JOIN navigator.research_events AS approval_research
                  ON approval_research.id = approval_review.research_event_id
                 AND approval_research.requirement_version_id = rv.id
                JOIN navigator.requirement_sources AS primary_link
                  ON primary_link.id = candidate_primary_source_id
                 AND primary_link.requirement_version_id = rv.id
                 AND primary_link.source_role = 'primary'
                 AND primary_link.relationship_status = 'active'
                WHERE rv.id = candidate_requirement_version_id
                  AND rv.verification_status = 'approved'
                  AND rv.is_current
                  AND (rv.effective_from IS NULL
                       OR rv.effective_from <= CURRENT_DATE)
                  AND (rv.effective_until IS NULL
                       OR CURRENT_DATE <= rv.effective_until)
                  AND approval_review.reviewed_at <= CURRENT_TIMESTAMP
                  AND approval_research.research_status = 'completed'
                  AND approval_research.recommendation = 'approve'
                  AND EXISTS (
                      SELECT 1
                      FROM navigator.research_event_evidence AS approval_evidence
                      WHERE approval_evidence.research_event_id =
                            approval_research.id
                  )
                  AND (requirement_entity.valid_from IS NULL
                       OR requirement_entity.valid_from <= CURRENT_DATE)
                  AND (requirement_entity.valid_until IS NULL
                       OR CURRENT_DATE <= requirement_entity.valid_until)
                  AND navigator.is_approved_and_fresh(
                        requirement_entity.verification_status,
                        requirement_entity.verification_review_event_id,
                        requirement_entity.last_verified_at,
                        requirement_entity.review_interval_days,
                        requirement_entity.next_review_at,
                        'government_entity',
                        requirement_entity.id
                  )
                  AND EXISTS (
                      SELECT 1
                      FROM navigator.requirement_activities AS ra
                      JOIN navigator.business_activities AS activity
                        ON activity.id = ra.activity_id
                       AND activity.is_active
                      WHERE ra.requirement_version_id = rv.id
                  )
                  AND NOT EXISTS (
                      SELECT 1
                      FROM navigator.requirement_activities AS ra
                      JOIN navigator.business_activities AS activity
                        ON activity.id = ra.activity_id
                      WHERE ra.requirement_version_id = rv.id
                        AND NOT activity.is_active
                  )
                  AND (
                      SELECT count(*)
                      FROM navigator.requirement_sources AS counted_primary
                      WHERE counted_primary.requirement_version_id = rv.id
                        AND counted_primary.relationship_status = 'active'
                        AND counted_primary.source_role = 'primary'
                  ) = 1
                  AND NOT EXISTS (
                      SELECT 1
                      FROM navigator.requirement_sources AS conflicting_link
                      WHERE conflicting_link.requirement_version_id = rv.id
                        AND conflicting_link.relationship_status = 'active'
                        AND conflicting_link.source_role = 'conflicting'
                  )
                  AND NOT EXISTS (
                      SELECT 1
                      FROM navigator.requirement_sources AS evidence_link
                      LEFT JOIN navigator.review_events AS evidence_review
                        ON evidence_review.id = evidence_link.role_review_event_id
                      LEFT JOIN navigator.research_events AS evidence_research
                        ON evidence_research.id = evidence_review.research_event_id
                      LEFT JOIN navigator.source_versions AS source_version
                        ON source_version.id = evidence_link.source_version_id
                      LEFT JOIN navigator.sources AS stable_source
                        ON stable_source.id = source_version.source_id
                      LEFT JOIN navigator.domains AS source_domain
                        ON source_domain.id = source_version.domain_id_at_review
                      LEFT JOIN navigator.government_entities AS source_entity
                        ON source_entity.id = stable_source.responsible_entity_id
                      LEFT JOIN navigator.government_entities AS domain_entity
                        ON domain_entity.id = source_domain.responsible_entity_id
                      LEFT JOIN navigator.platforms AS source_platform
                        ON source_platform.id = source_domain.platform_id
                      LEFT JOIN navigator.government_entities AS platform_entity
                        ON platform_entity.id = source_platform.responsible_entity_id
                      WHERE evidence_link.requirement_version_id = rv.id
                        AND evidence_link.relationship_status = 'active'
                        AND (
                            evidence_review.id IS NULL
                            OR evidence_review.decision <> 'approved'
                            OR evidence_review.reviewed_at > approval_review.reviewed_at
                            OR evidence_research.requirement_source_id
                                IS DISTINCT FROM evidence_link.id
                            OR evidence_research.research_status <> 'completed'
                            OR evidence_research.recommendation <> 'approve'
                            OR NOT EXISTS (
                                SELECT 1
                                FROM navigator.research_event_evidence
                                    AS cited_evidence
                                WHERE cited_evidence.research_event_id =
                                      evidence_research.id
                                  AND cited_evidence.source_version_id =
                                      evidence_link.source_version_id
                            )
                            OR (
                                evidence_link.source_role <> 'historical'
                                AND (
                                    evidence_link.official_excerpt_ar IS NULL
                                    OR btrim(evidence_link.official_excerpt_ar) = ''
                                    OR evidence_link.excerpt_locator IS NULL
                                    OR btrim(evidence_link.excerpt_locator) = ''
                                    OR source_version.id IS NULL
                                    OR NOT source_version.is_current
                                    OR NOT navigator.is_approved_and_fresh(
                                        source_version.review_status,
                                        source_version.verification_review_event_id,
                                        source_version.last_verified_at,
                                        source_version.review_interval_days,
                                        source_version.next_review_at,
                                        'source_version',
                                        source_version.id
                                    )
                                    OR (source_version.effective_from IS NOT NULL
                                        AND source_version.effective_from > CURRENT_DATE)
                                    OR (source_version.effective_until IS NOT NULL
                                        AND CURRENT_DATE > source_version.effective_until)
                                    OR stable_source.id IS NULL
                                    OR NOT navigator.is_approved_and_fresh(
                                        stable_source.verification_status,
                                        stable_source.verification_review_event_id,
                                        stable_source.last_verified_at,
                                        stable_source.review_interval_days,
                                        stable_source.next_review_at,
                                        'source',
                                        stable_source.id
                                    )
                                    OR source_entity.id IS NULL
                                    OR NOT navigator.is_approved_and_fresh(
                                        source_entity.verification_status,
                                        source_entity.verification_review_event_id,
                                        source_entity.last_verified_at,
                                        source_entity.review_interval_days,
                                        source_entity.next_review_at,
                                        'government_entity',
                                        source_entity.id
                                    )
                                    OR (source_entity.valid_from IS NOT NULL
                                        AND source_entity.valid_from > CURRENT_DATE)
                                    OR (source_entity.valid_until IS NOT NULL
                                        AND CURRENT_DATE > source_entity.valid_until)
                                    OR source_domain.id IS NULL
                                    OR NOT navigator.is_approved_and_fresh(
                                        source_domain.verification_status,
                                        source_domain.verification_review_event_id,
                                        source_domain.last_verified_at,
                                        source_domain.review_interval_days,
                                        source_domain.next_review_at,
                                        'domain',
                                        source_domain.id
                                    )
                                    OR domain_entity.id IS NULL
                                    OR NOT navigator.is_approved_and_fresh(
                                        domain_entity.verification_status,
                                        domain_entity.verification_review_event_id,
                                        domain_entity.last_verified_at,
                                        domain_entity.review_interval_days,
                                        domain_entity.next_review_at,
                                        'government_entity',
                                        domain_entity.id
                                    )
                                    OR (domain_entity.valid_from IS NOT NULL
                                        AND domain_entity.valid_from > CURRENT_DATE)
                                    OR (domain_entity.valid_until IS NOT NULL
                                        AND CURRENT_DATE > domain_entity.valid_until)
                                    OR source_version.domain_id_at_review
                                        IS DISTINCT FROM stable_source.domain_id
                                    OR source_version.responsible_entity_id_at_review
                                        IS DISTINCT FROM stable_source.responsible_entity_id
                                    OR source_version.platform_id_at_review
                                        IS DISTINCT FROM source_domain.platform_id
                                    OR navigator.url_host(source_version.reviewed_url)
                                        IS DISTINCT FROM stable_source.canonical_host
                                    OR source_version.reviewed_url
                                        IS DISTINCT FROM stable_source.canonical_url
                                    OR navigator.url_host(source_version.resolved_url)
                                        IS DISTINCT FROM source_domain.domain_name
                                    OR (
                                        source_domain.platform_id IS NOT NULL
                                        AND (
                                            source_platform.id IS NULL
                                            OR NOT navigator.is_approved_and_fresh(
                                                source_platform.verification_status,
                                                source_platform.verification_review_event_id,
                                                source_platform.last_verified_at,
                                                source_platform.review_interval_days,
                                                source_platform.next_review_at,
                                                'platform',
                                                source_platform.id
                                            )
                                            OR (source_platform.valid_from IS NOT NULL
                                                AND source_platform.valid_from > CURRENT_DATE)
                                            OR (source_platform.valid_until IS NOT NULL
                                                AND CURRENT_DATE >
                                                    source_platform.valid_until)
                                            OR platform_entity.id IS NULL
                                            OR NOT navigator.is_approved_and_fresh(
                                                platform_entity.verification_status,
                                                platform_entity.verification_review_event_id,
                                                platform_entity.last_verified_at,
                                                platform_entity.review_interval_days,
                                                platform_entity.next_review_at,
                                                'government_entity',
                                                platform_entity.id
                                            )
                                            OR (platform_entity.valid_from IS NOT NULL
                                                AND platform_entity.valid_from > CURRENT_DATE)
                                            OR (platform_entity.valid_until IS NOT NULL
                                                AND CURRENT_DATE >
                                                    platform_entity.valid_until)
                                        )
                                    )
                                )
                            )
                        )
                  )
            )
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.guard_published_requirement_version()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF EXISTS (
                    SELECT 1
                    FROM navigator.requirement_publications
                    WHERE requirement_version_id = OLD.id
                ) THEN
                    RAISE EXCEPTION 'published requirement history is immutable';
                END IF;
                RETURN OLD;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM navigator.requirement_publications
                WHERE requirement_version_id = OLD.id
                  AND publication_status = 'published'
            ) AND (
                (OLD.verification_status <> 'approved'
                    AND NEW.verification_status = 'approved')
                OR (NOT OLD.is_current AND NEW.is_current)
            ) THEN
                RAISE EXCEPTION 'an active publication cannot be restored in place';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM navigator.requirement_publications
                WHERE requirement_version_id = OLD.id
            ) AND (
                pg_catalog.to_jsonb(NEW)
                    - 'verification_status' - 'is_current' - 'notes' - 'updated_at'
            ) IS DISTINCT FROM (
                pg_catalog.to_jsonb(OLD)
                    - 'verification_status' - 'is_current' - 'notes' - 'updated_at'
            ) THEN
                RAISE EXCEPTION 'published regulatory meaning requires a new version';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE OR REPLACE FUNCTION navigator.lock_requirement_activity_parent()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            target_requirement_version UUID;
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION 'activity links are replaced, not rewritten';
            END IF;
            target_requirement_version :=
                CASE WHEN TG_OP = 'DELETE'
                    THEN OLD.requirement_version_id
                    ELSE NEW.requirement_version_id
                END;
            PERFORM 1
            FROM navigator.requirement_versions
            WHERE id = target_requirement_version
            FOR UPDATE;
            IF EXISTS (
                SELECT 1
                FROM navigator.requirement_publications
                WHERE requirement_version_id = target_requirement_version
            ) THEN
                RAISE EXCEPTION 'published activity applicability is immutable';
            END IF;
            RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END
        $$
        """
    )

    execute(
        """
        CREATE OR REPLACE FUNCTION navigator.validate_requirement_source()
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
                IF EXISTS (
                    SELECT 1 FROM navigator.requirement_publications
                    WHERE requirement_version_id = target_requirement_version
                      AND publication_status = 'published'
                ) THEN
                    RAISE EXCEPTION 'active publication protects its evidence';
                END IF;
                RETURN OLD;
            END IF;

            IF TG_OP = 'INSERT' THEN
                IF EXISTS (
                    SELECT 1 FROM navigator.requirement_publications
                    WHERE requirement_version_id = target_requirement_version
                      AND publication_status = 'published'
                ) THEN
                    RAISE EXCEPTION 'active publication evidence is fixed';
                END IF;
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

            IF governed_change AND EXISTS (
                SELECT 1 FROM navigator.requirement_publications
                WHERE requirement_version_id = target_requirement_version
                  AND publication_status = 'published'
            ) THEN
                RAISE EXCEPTION 'active publication protects its evidence';
            END IF;
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
        CREATE FUNCTION navigator.validate_publication_insert()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            next_number INTEGER;
            latest_withdrawal TIMESTAMPTZ;
            approval_time TIMESTAMPTZ;
        BEGIN
            PERFORM 1
            FROM navigator.requirement_versions
            WHERE id = NEW.requirement_version_id
            FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'requirement version does not exist';
            END IF;

            IF NEW.publication_status <> 'published'
                OR NEW.withdrawn_at IS NOT NULL
                OR NEW.withdrawn_by_role IS NOT NULL
                OR NEW.withdrawal_reason IS NOT NULL
            THEN
                RAISE EXCEPTION 'new publication cycles begin published';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM navigator.requirement_publications
                WHERE requirement_version_id = NEW.requirement_version_id
                  AND publication_status = 'published'
            ) THEN
                RAISE EXCEPTION 'only one active publication is allowed';
            END IF;

            SELECT COALESCE(max(publication_number), 0) + 1,
                   max(withdrawn_at)
            INTO next_number, latest_withdrawal
            FROM navigator.requirement_publications
            WHERE requirement_version_id = NEW.requirement_version_id;

            IF EXISTS (
                SELECT 1
                FROM navigator.requirement_publications
                WHERE requirement_version_id = NEW.requirement_version_id
                  AND publication_status <> 'withdrawn'
            ) THEN
                RAISE EXCEPTION 'previous publication cycles must be withdrawn';
            END IF;

            SELECT reviewed_at
            INTO approval_time
            FROM navigator.review_events
            WHERE id = NEW.approval_review_event_id;
            IF approval_time IS NULL THEN
                RAISE EXCEPTION 'publication requires a review event';
            END IF;
            IF approval_time > pg_catalog.clock_timestamp() THEN
                RAISE EXCEPTION 'future publication approvals are prohibited';
            END IF;
            IF latest_withdrawal IS NOT NULL AND approval_time <= latest_withdrawal THEN
                RAISE EXCEPTION 'republication requires review after withdrawal';
            END IF;
            IF NOT navigator.requirement_candidate_is_eligible(
                NEW.requirement_version_id,
                NEW.primary_requirement_source_id,
                NEW.approval_review_event_id
            ) THEN
                RAISE EXCEPTION 'publication evidence is not eligible';
            END IF;

            NEW.publication_number := next_number;
            NEW.published_at := pg_catalog.clock_timestamp();
            NEW.created_at := NEW.published_at;
            NEW.updated_at := NEW.published_at;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.snapshot_publication_sources()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            inserted_count INTEGER;
            primary_count INTEGER;
        BEGIN
            INSERT INTO navigator.requirement_publication_sources (
                publication_id,
                requirement_source_id,
                source_role_at_publication,
                official_excerpt_ar_at_publication,
                official_excerpt_en_at_publication,
                excerpt_locator_at_publication
            )
            SELECT
                NEW.id,
                evidence.id,
                evidence.source_role,
                evidence.official_excerpt_ar,
                evidence.official_excerpt_en,
                evidence.excerpt_locator
            FROM navigator.requirement_sources AS evidence
            WHERE evidence.requirement_version_id = NEW.requirement_version_id
              AND evidence.relationship_status = 'active'
            ORDER BY evidence.id;

            GET DIAGNOSTICS inserted_count = ROW_COUNT;
            SELECT count(*)
            INTO primary_count
            FROM navigator.requirement_publication_sources
            WHERE publication_id = NEW.id
              AND source_role_at_publication = 'primary'
              AND requirement_source_id = NEW.primary_requirement_source_id;

            IF inserted_count = 0 OR primary_count <> 1 THEN
                RAISE EXCEPTION 'publication evidence snapshot is incomplete';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_publication_source_snapshot()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM navigator.requirement_publications AS publication
                JOIN navigator.requirement_sources AS evidence
                  ON evidence.id = NEW.requirement_source_id
                 AND evidence.requirement_version_id =
                     publication.requirement_version_id
                 AND evidence.relationship_status = 'active'
                WHERE publication.id = NEW.publication_id
                  AND publication.publication_status = 'published'
                  AND NEW.source_role_at_publication
                      IS NOT DISTINCT FROM evidence.source_role
                  AND NEW.official_excerpt_ar_at_publication
                      IS NOT DISTINCT FROM evidence.official_excerpt_ar
                  AND NEW.official_excerpt_en_at_publication
                      IS NOT DISTINCT FROM evidence.official_excerpt_en
                  AND NEW.excerpt_locator_at_publication
                      IS NOT DISTINCT FROM evidence.excerpt_locator
            ) THEN
                RAISE EXCEPTION 'publication source snapshot must match active evidence';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_publication_transition()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'publication history is append preserving';
            END IF;
            PERFORM 1
            FROM navigator.requirement_versions
            WHERE id = OLD.requirement_version_id
            FOR UPDATE;

            IF OLD.publication_status <> 'published'
                OR NEW.publication_status <> 'withdrawn'
            THEN
                RAISE EXCEPTION 'withdrawn publications cannot be reopened or rewritten';
            END IF;
            IF NEW.id IS DISTINCT FROM OLD.id
                OR NEW.requirement_version_id IS DISTINCT FROM OLD.requirement_version_id
                OR NEW.publication_number IS DISTINCT FROM OLD.publication_number
                OR NEW.primary_requirement_source_id
                    IS DISTINCT FROM OLD.primary_requirement_source_id
                OR NEW.approval_review_event_id
                    IS DISTINCT FROM OLD.approval_review_event_id
                OR NEW.published_at IS DISTINCT FROM OLD.published_at
                OR NEW.created_at IS DISTINCT FROM OLD.created_at
            THEN
                RAISE EXCEPTION 'publication cycle identity is immutable';
            END IF;
            IF NEW.withdrawn_at IS NOT NULL THEN
                RAISE EXCEPTION 'withdrawal timestamp is database derived';
            END IF;
            IF NEW.withdrawn_by_role IS NULL
                OR NEW.withdrawal_reason IS NULL
                OR btrim(NEW.withdrawal_reason) = ''
            THEN
                RAISE EXCEPTION 'withdrawal requires role and reason';
            END IF;
            NEW.withdrawn_at := pg_catalog.clock_timestamp();
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.guard_active_publication_dependency()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            has_dependency BOOLEAN := false;
            identity_changed BOOLEAN := false;
            old_status TEXT;
            new_status TEXT;
        BEGIN
            CASE TG_TABLE_NAME
                WHEN 'government_entities' THEN
                    SELECT EXISTS (
                        SELECT 1
                        FROM navigator.requirement_publications AS p
                        JOIN navigator.requirement_versions AS rv
                          ON rv.id = p.requirement_version_id
                        WHERE p.publication_status = 'published'
                          AND (
                              rv.responsible_entity_id = OLD.id
                              OR EXISTS (
                                  SELECT 1
                                  FROM navigator.requirement_publication_sources AS ps
                                  JOIN navigator.requirement_sources AS rs
                                    ON rs.id = ps.requirement_source_id
                                  JOIN navigator.source_versions AS sv
                                    ON sv.id = rs.source_version_id
                                  JOIN navigator.sources AS s ON s.id = sv.source_id
                                  JOIN navigator.domains AS d
                                    ON d.id = sv.domain_id_at_review
                                  LEFT JOIN navigator.platforms AS platform
                                    ON platform.id = d.platform_id
                                  WHERE ps.publication_id = p.id
                                    AND (
                                        s.responsible_entity_id = OLD.id
                                        OR d.responsible_entity_id = OLD.id
                                        OR platform.responsible_entity_id = OLD.id
                                    )
                              )
                          )
                    ) INTO has_dependency;
                WHEN 'platforms' THEN
                    SELECT EXISTS (
                        SELECT 1
                        FROM navigator.requirement_publications AS p
                        JOIN navigator.requirement_publication_sources AS ps
                          ON ps.publication_id = p.id
                        JOIN navigator.requirement_sources AS rs
                          ON rs.id = ps.requirement_source_id
                        JOIN navigator.source_versions AS sv
                          ON sv.id = rs.source_version_id
                        WHERE p.publication_status = 'published'
                          AND sv.platform_id_at_review = OLD.id
                    ) INTO has_dependency;
                WHEN 'domains' THEN
                    SELECT EXISTS (
                        SELECT 1
                        FROM navigator.requirement_publications AS p
                        JOIN navigator.requirement_publication_sources AS ps
                          ON ps.publication_id = p.id
                        JOIN navigator.requirement_sources AS rs
                          ON rs.id = ps.requirement_source_id
                        JOIN navigator.source_versions AS sv
                          ON sv.id = rs.source_version_id
                        WHERE p.publication_status = 'published'
                          AND sv.domain_id_at_review = OLD.id
                    ) INTO has_dependency;
                WHEN 'sources' THEN
                    SELECT EXISTS (
                        SELECT 1
                        FROM navigator.requirement_publications AS p
                        JOIN navigator.requirement_publication_sources AS ps
                          ON ps.publication_id = p.id
                        JOIN navigator.requirement_sources AS rs
                          ON rs.id = ps.requirement_source_id
                        JOIN navigator.source_versions AS sv
                          ON sv.id = rs.source_version_id
                        WHERE p.publication_status = 'published'
                          AND sv.source_id = OLD.id
                    ) INTO has_dependency;
                WHEN 'source_versions' THEN
                    SELECT EXISTS (
                        SELECT 1
                        FROM navigator.requirement_publications AS p
                        JOIN navigator.requirement_publication_sources AS ps
                          ON ps.publication_id = p.id
                        JOIN navigator.requirement_sources AS rs
                          ON rs.id = ps.requirement_source_id
                        WHERE p.publication_status = 'published'
                          AND rs.source_version_id = OLD.id
                    ) INTO has_dependency;
            END CASE;

            IF NOT has_dependency THEN
                RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
            END IF;
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'active publication protects dependency history';
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
                OR (
                    TG_TABLE_NAME = 'source_versions'
                    AND NOT COALESCE(
                        (pg_catalog.to_jsonb(OLD)->>'is_current')::boolean,
                        false
                    )
                    AND COALESCE(
                        (pg_catalog.to_jsonb(NEW)->>'is_current')::boolean,
                        false
                    )
                )
            THEN
                RAISE EXCEPTION 'an active publication dependency cannot be restored';
            END IF;

            identity_changed := (
                pg_catalog.to_jsonb(NEW)
                    - 'verification_status' - 'review_status'
                    - 'verification_review_event_id' - 'last_verified_at'
                    - 'review_interval_days' - 'next_review_at'
                    - 'is_current' - 'notes' - 'updated_at'
            ) IS DISTINCT FROM (
                pg_catalog.to_jsonb(OLD)
                    - 'verification_status' - 'review_status'
                    - 'verification_review_event_id' - 'last_verified_at'
                    - 'review_interval_days' - 'next_review_at'
                    - 'is_current' - 'notes' - 'updated_at'
            );
            IF identity_changed THEN
                RAISE EXCEPTION 'active publication protects dependency identity';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.publication_is_eligible(candidate_publication_id UUID)
        RETURNS BOOLEAN
        LANGUAGE sql
        STABLE
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
            SELECT EXISTS (
                SELECT 1
                FROM navigator.requirement_publications AS publication
                WHERE publication.id = candidate_publication_id
                  AND publication.publication_status = 'published'
                  AND navigator.requirement_candidate_is_eligible(
                      publication.requirement_version_id,
                      publication.primary_requirement_source_id,
                      publication.approval_review_event_id
                  )
                  AND (
                      SELECT count(*)
                      FROM navigator.requirement_publication_sources AS snapshot_count
                      WHERE snapshot_count.publication_id = publication.id
                  ) = (
                      SELECT count(*)
                      FROM navigator.requirement_sources AS live_count
                      WHERE live_count.requirement_version_id =
                            publication.requirement_version_id
                        AND live_count.relationship_status = 'active'
                  )
                  AND (
                      SELECT count(*)
                      FROM navigator.requirement_publication_sources AS snapshot_primary
                      WHERE snapshot_primary.publication_id = publication.id
                        AND snapshot_primary.source_role_at_publication = 'primary'
                        AND snapshot_primary.requirement_source_id =
                            publication.primary_requirement_source_id
                  ) = 1
                  AND NOT EXISTS (
                      SELECT 1
                      FROM navigator.requirement_publication_sources AS snapshot
                      LEFT JOIN navigator.requirement_sources AS live
                        ON live.id = snapshot.requirement_source_id
                      WHERE snapshot.publication_id = publication.id
                        AND (
                            live.id IS NULL
                            OR live.requirement_version_id
                                IS DISTINCT FROM publication.requirement_version_id
                            OR live.relationship_status <> 'active'
                            OR snapshot.source_role_at_publication
                                IS DISTINCT FROM live.source_role
                            OR snapshot.official_excerpt_ar_at_publication
                                IS DISTINCT FROM live.official_excerpt_ar
                            OR snapshot.official_excerpt_en_at_publication
                                IS DISTINCT FROM live.official_excerpt_en
                            OR snapshot.excerpt_locator_at_publication
                                IS DISTINCT FROM live.excerpt_locator
                        )
                  )
            )
        $$
        """
    )

    execute(
        """
        CREATE VIEW navigator.published_requirement_versions AS
        SELECT
            publication.id AS publication_id,
            publication.publication_number,
            publication.published_at,
            requirement.id AS requirement_id,
            requirement.code AS requirement_code,
            version.id AS requirement_version_id,
            version.version_number,
            version.scope_type,
            version.responsible_entity_id,
            version.canonical_title_ar,
            version.canonical_description_ar,
            version.canonical_title_en,
            version.canonical_description_en,
            version.simplified_explanation_ar,
            version.simplified_explanation_en,
            version.effective_from,
            version.effective_until,
            publication.primary_requirement_source_id,
            primary_snapshot.official_excerpt_ar_at_publication
                AS official_evidence_ar,
            primary_snapshot.official_excerpt_en_at_publication
                AS official_evidence_en,
            primary_snapshot.excerpt_locator_at_publication
                AS official_evidence_locator
        FROM navigator.requirement_publications AS publication
        JOIN navigator.requirement_versions AS version
          ON version.id = publication.requirement_version_id
        JOIN navigator.requirements AS requirement
          ON requirement.id = version.requirement_id
        JOIN navigator.requirement_publication_sources AS primary_snapshot
          ON primary_snapshot.publication_id = publication.id
         AND primary_snapshot.requirement_source_id =
             publication.primary_requirement_source_id
         AND primary_snapshot.source_role_at_publication = 'primary'
        WHERE navigator.publication_is_eligible(publication.id)
        """
    )

    execute(
        """
        CREATE TRIGGER trg_10_guard_published_requirement_version
        BEFORE UPDATE OR DELETE ON navigator.requirement_versions
        FOR EACH ROW EXECUTE FUNCTION navigator.guard_published_requirement_version()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_10_validate_publication_insert
        BEFORE INSERT ON navigator.requirement_publications
        FOR EACH ROW EXECUTE FUNCTION navigator.validate_publication_insert()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_20_snapshot_publication_sources
        AFTER INSERT ON navigator.requirement_publications
        FOR EACH ROW EXECUTE FUNCTION navigator.snapshot_publication_sources()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_10_validate_publication_transition
        BEFORE UPDATE OR DELETE ON navigator.requirement_publications
        FOR EACH ROW EXECUTE FUNCTION navigator.validate_publication_transition()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_90_set_updated_at
        BEFORE UPDATE ON navigator.requirement_publications
        FOR EACH ROW EXECUTE FUNCTION navigator.set_updated_at_on_change()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_05_validate_publication_source_insert
        BEFORE INSERT ON navigator.requirement_publication_sources
        FOR EACH ROW
        EXECUTE FUNCTION navigator.validate_publication_source_snapshot()
        """
    )
    execute(
        """
        CREATE TRIGGER trg_10_append_only
        BEFORE UPDATE OR DELETE ON navigator.requirement_publication_sources
        FOR EACH ROW EXECUTE FUNCTION navigator.guard_append_only()
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
            CREATE TRIGGER trg_05_guard_active_publication_dependency
            BEFORE UPDATE OR DELETE ON navigator.{table_name}
            FOR EACH ROW
            EXECUTE FUNCTION navigator.guard_active_publication_dependency()
            """
        )


def downgrade() -> None:
    """Remove publication controls while preserving earlier schema migrations."""
    for table_name in (
        "government_entities",
        "platforms",
        "domains",
        "sources",
        "source_versions",
    ):
        execute(
            f"DROP TRIGGER trg_05_guard_active_publication_dependency ON navigator.{table_name}"
        )
    execute("DROP TRIGGER trg_10_append_only ON navigator.requirement_publication_sources")
    execute(
        "DROP TRIGGER trg_05_validate_publication_source_insert "
        "ON navigator.requirement_publication_sources"
    )
    execute("DROP TRIGGER trg_90_set_updated_at ON navigator.requirement_publications")
    execute(
        "DROP TRIGGER trg_10_validate_publication_transition ON navigator.requirement_publications"
    )
    execute(
        "DROP TRIGGER trg_20_snapshot_publication_sources ON navigator.requirement_publications"
    )
    execute("DROP TRIGGER trg_10_validate_publication_insert ON navigator.requirement_publications")
    execute(
        "DROP TRIGGER trg_10_guard_published_requirement_version ON navigator.requirement_versions"
    )
    execute("DROP VIEW navigator.published_requirement_versions")
    execute("DROP FUNCTION navigator.publication_is_eligible(UUID)")
    execute("DROP FUNCTION navigator.guard_active_publication_dependency()")
    execute("DROP FUNCTION navigator.validate_publication_transition()")
    execute("DROP FUNCTION navigator.validate_publication_source_snapshot()")
    execute("DROP FUNCTION navigator.snapshot_publication_sources()")
    execute("DROP FUNCTION navigator.validate_publication_insert()")
    execute("DROP FUNCTION navigator.guard_published_requirement_version()")
    execute("DROP FUNCTION navigator.requirement_candidate_is_eligible(UUID, UUID, UUID)")
    execute(
        "DROP FUNCTION navigator.is_approved_and_fresh("
        "TEXT, UUID, TIMESTAMPTZ, INTEGER, TIMESTAMPTZ, TEXT, UUID)"
    )
    execute("DROP TABLE navigator.requirement_publication_sources")
    execute("DROP TABLE navigator.requirement_publications")

    execute(
        """
        CREATE OR REPLACE FUNCTION navigator.lock_requirement_activity_parent()
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
        CREATE OR REPLACE FUNCTION navigator.validate_requirement_source()
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
