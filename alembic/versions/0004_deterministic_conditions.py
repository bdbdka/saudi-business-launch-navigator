"""Add governed facts and version-level deterministic conditions.

Revision ID: 0004_deterministic_conditions
Revises: 0003_publication_eligibility
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004_deterministic_conditions"
down_revision: str | None = "0003_publication_eligibility"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PUBLICATION_ELIGIBILITY_SQL = """
CREATE OR REPLACE FUNCTION navigator.publication_is_eligible(candidate_publication_id UUID)
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
          AND navigator.requirement_conditions_are_eligible(
              publication.requirement_version_id
          )
          AND (
              SELECT count(*)
              FROM navigator.requirement_publication_sources AS snapshot_count
              WHERE snapshot_count.publication_id = publication.id
          ) = (
              SELECT count(*)
              FROM navigator.requirement_sources AS live_count
              WHERE live_count.requirement_version_id = publication.requirement_version_id
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
                    OR live.requirement_version_id IS DISTINCT FROM
                        publication.requirement_version_id
                    OR live.relationship_status <> 'active'
                    OR snapshot.source_role_at_publication IS DISTINCT FROM live.source_role
                    OR snapshot.official_excerpt_ar_at_publication IS DISTINCT FROM
                        live.official_excerpt_ar
                    OR snapshot.official_excerpt_en_at_publication IS DISTINCT FROM
                        live.official_excerpt_en
                    OR snapshot.excerpt_locator_at_publication IS DISTINCT FROM
                        live.excerpt_locator
                )
          )
    )
$$
"""


PUBLICATION_ELIGIBILITY_WITHOUT_CONDITIONS_SQL = PUBLICATION_ELIGIBILITY_SQL.replace(
    "          AND navigator.requirement_conditions_are_eligible(\n"
    "              publication.requirement_version_id\n"
    "          )\n",
    "",
)


def upgrade() -> None:
    execute = op.execute
    execute(
        """
        CREATE TABLE navigator.fact_definitions (
            id UUID PRIMARY KEY,
            code TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            meaning_ar TEXT NOT NULL,
            explanation_en TEXT,
            data_type TEXT NOT NULL,
            allowed_values JSONB,
            unit TEXT,
            privacy_class TEXT DEFAULT 'non_personal_business' NOT NULL,
            validation_metadata JSONB DEFAULT '{}'::jsonb NOT NULL,
            source_version_id UUID NOT NULL,
            official_excerpt_ar TEXT NOT NULL,
            evidence_locator TEXT NOT NULL,
            verification_status TEXT DEFAULT 'pending_source_verification' NOT NULL,
            approval_review_event_id UUID,
            is_current BOOLEAN DEFAULT false NOT NULL,
            supersedes_fact_definition_id UUID,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT uq_fact_definitions_code_version UNIQUE (code, version_number),
            CONSTRAINT uq_fact_definitions_supersedes_fact_definition
                UNIQUE (supersedes_fact_definition_id),
            CONSTRAINT ck_fact_definitions_code_format
                CHECK (code ~ '^[a-z][a-z0-9_]*$'),
            CONSTRAINT ck_fact_definitions_positive_version_number CHECK (version_number > 0),
            CONSTRAINT ck_fact_definitions_data_type
                CHECK (data_type IN ('boolean', 'integer', 'decimal', 'enum')),
            CONSTRAINT ck_fact_definitions_privacy_class
                CHECK (privacy_class = 'non_personal_business'),
            CONSTRAINT ck_fact_definitions_verification_status CHECK (
                verification_status IN (
                    'pending_source_verification', 'pending_review', 'approved', 'rejected',
                    'conflicting', 'stale', 'superseded', 'historical'
                )
            ),
            CONSTRAINT ck_fact_definitions_meaning_ar_nonblank
                CHECK (btrim(meaning_ar) <> ''),
            CONSTRAINT ck_fact_definitions_enum_values_match_type CHECK (
                (data_type = 'enum' AND jsonb_typeof(allowed_values) = 'array'
                    AND jsonb_array_length(allowed_values) > 0)
                OR (data_type <> 'enum' AND allowed_values IS NULL)
            ),
            CONSTRAINT ck_fact_definitions_approved_has_governance_evidence CHECK (
                verification_status <> 'approved'
                OR (approval_review_event_id IS NOT NULL
                    AND btrim(official_excerpt_ar) <> ''
                    AND btrim(evidence_locator) <> '')
            ),
            CONSTRAINT ck_fact_definitions_not_self_superseding
                CHECK (supersedes_fact_definition_id IS DISTINCT FROM id),
            CONSTRAINT fk_fact_definitions_source_version
                FOREIGN KEY (source_version_id)
                REFERENCES navigator.source_versions (id) ON DELETE RESTRICT,
            CONSTRAINT fk_fact_definitions_approval_review
                FOREIGN KEY (approval_review_event_id)
                REFERENCES navigator.review_events (id) ON DELETE RESTRICT,
            CONSTRAINT fk_fact_definitions_supersedes
                FOREIGN KEY (supersedes_fact_definition_id)
                REFERENCES navigator.fact_definitions (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE UNIQUE INDEX uq_fact_definitions_one_current "
        "ON navigator.fact_definitions (code) WHERE is_current"
    )
    execute(
        "CREATE INDEX ix_fact_definitions_source_version_id "
        "ON navigator.fact_definitions (source_version_id)"
    )
    execute(
        "CREATE INDEX ix_fact_definitions_approval_review_event_id "
        "ON navigator.fact_definitions (approval_review_event_id)"
    )
    execute(
        "CREATE INDEX ix_fact_definitions_verification_status "
        "ON navigator.fact_definitions (verification_status)"
    )

    execute(
        """
        CREATE TABLE navigator.requirement_condition_sets (
            id UUID PRIMARY KEY,
            requirement_version_id UUID NOT NULL,
            dsl_schema_version INTEGER DEFAULT 1 NOT NULL,
            expression JSONB NOT NULL,
            expression_sha256 TEXT NOT NULL,
            verification_status TEXT DEFAULT 'pending_source_verification' NOT NULL,
            approval_review_event_id UUID,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT uq_requirement_condition_sets_requirement_version
                UNIQUE (requirement_version_id),
            CONSTRAINT ck_requirement_condition_sets_dsl_schema_version
                CHECK (dsl_schema_version = 1),
            CONSTRAINT ck_requirement_condition_sets_expression_object
                CHECK (jsonb_typeof(expression) = 'object'),
            CONSTRAINT ck_requirement_condition_sets_expression_sha256
                CHECK (expression_sha256 ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_requirement_condition_sets_verification_status CHECK (
                verification_status IN (
                    'pending_source_verification', 'pending_review', 'approved', 'rejected',
                    'conflicting', 'stale', 'superseded', 'historical'
                )
            ),
            CONSTRAINT ck_requirement_condition_sets_approved_has_review CHECK (
                verification_status <> 'approved' OR approval_review_event_id IS NOT NULL
            ),
            CONSTRAINT fk_requirement_condition_sets_requirement_version
                FOREIGN KEY (requirement_version_id)
                REFERENCES navigator.requirement_versions (id) ON DELETE RESTRICT,
            CONSTRAINT fk_requirement_condition_sets_approval_review
                FOREIGN KEY (approval_review_event_id)
                REFERENCES navigator.review_events (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE INDEX ix_requirement_condition_sets_verification_status "
        "ON navigator.requirement_condition_sets (verification_status)"
    )
    execute(
        "CREATE INDEX ix_requirement_condition_sets_approval_review_event_id "
        "ON navigator.requirement_condition_sets (approval_review_event_id)"
    )

    execute(
        """
        CREATE TABLE navigator.requirement_condition_facts (
            condition_set_id UUID NOT NULL,
            fact_definition_id UUID NOT NULL,
            created_at TIMESTAMPTZ DEFAULT clock_timestamp() NOT NULL,
            CONSTRAINT pk_requirement_condition_facts
                PRIMARY KEY (condition_set_id, fact_definition_id),
            CONSTRAINT fk_requirement_condition_facts_condition_set
                FOREIGN KEY (condition_set_id)
                REFERENCES navigator.requirement_condition_sets (id) ON DELETE RESTRICT,
            CONSTRAINT fk_requirement_condition_facts_fact_definition
                FOREIGN KEY (fact_definition_id)
                REFERENCES navigator.fact_definitions (id) ON DELETE RESTRICT
        )
        """
    )
    execute(
        "CREATE INDEX ix_requirement_condition_facts_fact_definition_id "
        "ON navigator.requirement_condition_facts (fact_definition_id)"
    )

    execute(
        """
        CREATE FUNCTION navigator.condition_expression_is_valid(candidate JSONB)
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        IMMUTABLE
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            operator_name TEXT;
            child JSONB;
            key_count INTEGER;
        BEGIN
            IF jsonb_typeof(candidate) <> 'object' THEN
                RETURN false;
            END IF;
            operator_name := candidate ->> 'op';
            SELECT count(*) INTO key_count FROM jsonb_object_keys(candidate);
            IF operator_name = 'eq' THEN
                RETURN key_count = 3
                    AND candidate ? 'fact'
                    AND candidate ? 'value'
                    AND (candidate ->> 'fact') ~ '^[a-z][a-z0-9_]*$'
                    AND jsonb_typeof(candidate -> 'value') IN (
                        'boolean', 'number', 'string'
                    );
            ELSIF operator_name IN ('and', 'or') THEN
                IF key_count <> 2 OR jsonb_typeof(candidate -> 'args') <> 'array'
                    OR jsonb_array_length(candidate -> 'args') < 2 THEN
                    RETURN false;
                END IF;
                FOR child IN SELECT value FROM jsonb_array_elements(candidate -> 'args') LOOP
                    IF NOT navigator.condition_expression_is_valid(child) THEN
                        RETURN false;
                    END IF;
                END LOOP;
                RETURN true;
            ELSIF operator_name = 'not' THEN
                RETURN key_count = 2
                    AND candidate ? 'arg'
                    AND navigator.condition_expression_is_valid(candidate -> 'arg');
            END IF;
            RETURN false;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.condition_expression_fact_codes(candidate JSONB)
        RETURNS SETOF TEXT
        LANGUAGE plpgsql
        IMMUTABLE
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            child JSONB;
            operator_name TEXT;
        BEGIN
            operator_name := candidate ->> 'op';
            IF operator_name = 'eq' THEN
                RETURN NEXT candidate ->> 'fact';
            ELSIF operator_name IN ('and', 'or') THEN
                FOR child IN SELECT value FROM jsonb_array_elements(candidate -> 'args') LOOP
                    RETURN QUERY SELECT * FROM navigator.condition_expression_fact_codes(child);
                END LOOP;
            ELSIF operator_name = 'not' THEN
                RETURN QUERY SELECT *
                    FROM navigator.condition_expression_fact_codes(candidate -> 'arg');
            END IF;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_fact_definition_governance()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.verification_status = 'approved' THEN
                    RAISE EXCEPTION 'approved fact-definition history is immutable';
                END IF;
                RETURN OLD;
            END IF;
            IF NEW.verification_status = 'approved' AND NOT EXISTS (
                SELECT 1
                FROM navigator.review_events AS review
                JOIN navigator.research_events AS research
                  ON research.id = review.research_event_id
                WHERE review.id = NEW.approval_review_event_id
                  AND review.decision = 'approved'
                  AND research.research_status = 'completed'
                  AND research.recommendation = 'approve'
                  AND research.source_version_id = NEW.source_version_id
                  AND EXISTS (
                      SELECT 1 FROM navigator.research_event_evidence AS evidence
                      WHERE evidence.research_event_id = research.id
                        AND evidence.source_version_id = NEW.source_version_id
                  )
            ) THEN
                RAISE EXCEPTION 'approved fact requires reviewed official evidence';
            END IF;
            IF TG_OP = 'UPDATE' AND OLD.verification_status = 'approved'
                AND (
                    pg_catalog.to_jsonb(NEW)
                        - 'verification_status' - 'is_current' - 'updated_at'
                ) IS DISTINCT FROM (
                    pg_catalog.to_jsonb(OLD)
                        - 'verification_status' - 'is_current' - 'updated_at'
                )
            THEN
                RAISE EXCEPTION 'approved fact meaning is immutable; create a new version';
            END IF;
            IF TG_OP = 'UPDATE' AND OLD.verification_status <> 'approved'
                AND NEW.verification_status = 'approved'
                AND NOT NEW.is_current
            THEN
                RAISE EXCEPTION 'an approved fact definition must be current';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_condition_set_graph()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        DECLARE
            target_id UUID;
            condition_row navigator.requirement_condition_sets%ROWTYPE;
        BEGIN
            IF TG_TABLE_NAME = 'requirement_condition_sets' THEN
                IF TG_OP = 'DELETE' THEN
                    target_id := OLD.id;
                ELSE
                    target_id := NEW.id;
                END IF;
            ELSE
                IF TG_OP = 'DELETE' THEN
                    target_id := OLD.condition_set_id;
                ELSE
                    target_id := NEW.condition_set_id;
                END IF;
            END IF;
            SELECT * INTO condition_row
            FROM navigator.requirement_condition_sets
            WHERE id = target_id;
            IF NOT FOUND THEN
                RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
            END IF;
            IF NOT navigator.condition_expression_is_valid(condition_row.expression) THEN
                RAISE EXCEPTION 'condition expression is outside the restricted DSL';
            END IF;
            IF EXISTS (
                (SELECT DISTINCT fact_code
                 FROM navigator.condition_expression_fact_codes(condition_row.expression)
                      AS codes(fact_code))
                EXCEPT
                (SELECT fact.code
                 FROM navigator.requirement_condition_facts AS link
                 JOIN navigator.fact_definitions AS fact ON fact.id = link.fact_definition_id
                 WHERE link.condition_set_id = target_id)
            ) OR EXISTS (
                (SELECT fact.code
                 FROM navigator.requirement_condition_facts AS link
                 JOIN navigator.fact_definitions AS fact ON fact.id = link.fact_definition_id
                 WHERE link.condition_set_id = target_id)
                EXCEPT
                (SELECT DISTINCT fact_code
                 FROM navigator.condition_expression_fact_codes(condition_row.expression)
                      AS codes(fact_code))
            ) THEN
                RAISE EXCEPTION 'condition fact links differ from expression fact codes';
            END IF;
            IF condition_row.verification_status = 'approved' THEN
                IF NOT EXISTS (
                    SELECT 1
                    FROM navigator.review_events AS review
                    JOIN navigator.research_events AS research
                      ON research.id = review.research_event_id
                    WHERE review.id = condition_row.approval_review_event_id
                      AND review.decision = 'approved'
                      AND research.research_status = 'completed'
                      AND research.recommendation = 'approve'
                      AND research.requirement_version_id =
                          condition_row.requirement_version_id
                      AND EXISTS (
                          SELECT 1 FROM navigator.research_event_evidence AS evidence
                          WHERE evidence.research_event_id = research.id
                      )
                ) THEN
                    RAISE EXCEPTION 'approved condition requires requirement-version review';
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM navigator.requirement_condition_facts
                    WHERE condition_set_id = target_id
                ) OR EXISTS (
                    SELECT 1
                    FROM navigator.requirement_condition_facts AS link
                    JOIN navigator.fact_definitions AS fact ON fact.id = link.fact_definition_id
                    WHERE link.condition_set_id = target_id
                      AND (fact.verification_status <> 'approved' OR NOT fact.is_current)
                ) THEN
                    RAISE EXCEPTION 'approved condition requires current approved facts';
                END IF;
            END IF;
            RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.guard_governed_condition_history()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        BEGIN
            IF TG_OP = 'DELETE' AND OLD.verification_status = 'approved' THEN
                RAISE EXCEPTION 'approved condition-set history is immutable';
            END IF;
            IF TG_OP = 'UPDATE' AND OLD.verification_status = 'approved' THEN
                RAISE EXCEPTION 'approved condition sets are immutable; version the requirement';
            END IF;
            RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.requirement_conditions_are_eligible(
            candidate_requirement_version_id UUID
        )
        RETURNS BOOLEAN
        LANGUAGE sql
        STABLE
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
            SELECT CASE
                WHEN NOT EXISTS (
                    SELECT 1 FROM navigator.requirement_condition_sets
                    WHERE requirement_version_id = candidate_requirement_version_id
                ) THEN true
                ELSE EXISTS (
                    SELECT 1
                    FROM navigator.requirement_condition_sets AS condition_set
                    WHERE condition_set.requirement_version_id =
                          candidate_requirement_version_id
                      AND condition_set.verification_status = 'approved'
                      AND navigator.condition_expression_is_valid(condition_set.expression)
                      AND EXISTS (
                          SELECT 1 FROM navigator.requirement_condition_facts AS link
                          WHERE link.condition_set_id = condition_set.id
                      )
                      AND NOT EXISTS (
                          SELECT 1
                          FROM navigator.requirement_condition_facts AS link
                          JOIN navigator.fact_definitions AS fact
                            ON fact.id = link.fact_definition_id
                          WHERE link.condition_set_id = condition_set.id
                            AND (fact.verification_status <> 'approved' OR NOT fact.is_current)
                      )
                )
            END
        $$
        """
    )

    execute(
        """
        CREATE FUNCTION navigator.validate_publication_condition()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog
        AS $$
        BEGIN
            IF NOT navigator.requirement_conditions_are_eligible(
                NEW.requirement_version_id
            ) THEN
                RAISE EXCEPTION 'publication condition is not eligible';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )

    execute(
        "CREATE TRIGGER trg_10_validate_fact_definition_governance "
        "BEFORE INSERT OR UPDATE OR DELETE ON navigator.fact_definitions "
        "FOR EACH ROW EXECUTE FUNCTION navigator.validate_fact_definition_governance()"
    )
    execute(
        "CREATE TRIGGER trg_90_set_updated_at "
        "BEFORE UPDATE ON navigator.fact_definitions "
        "FOR EACH ROW EXECUTE FUNCTION navigator.set_updated_at_on_change()"
    )
    execute(
        "CREATE TRIGGER trg_10_guard_governed_condition_history "
        "BEFORE UPDATE OR DELETE ON navigator.requirement_condition_sets "
        "FOR EACH ROW EXECUTE FUNCTION navigator.guard_governed_condition_history()"
    )
    execute(
        "CREATE CONSTRAINT TRIGGER trg_80_validate_condition_set_graph "
        "AFTER INSERT OR UPDATE OR DELETE ON navigator.requirement_condition_sets "
        "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
        "EXECUTE FUNCTION navigator.validate_condition_set_graph()"
    )
    execute(
        "CREATE CONSTRAINT TRIGGER trg_80_validate_condition_fact_graph "
        "AFTER INSERT OR UPDATE OR DELETE ON navigator.requirement_condition_facts "
        "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
        "EXECUTE FUNCTION navigator.validate_condition_set_graph()"
    )
    execute(
        "CREATE TRIGGER trg_05_validate_publication_condition "
        "BEFORE INSERT ON navigator.requirement_publications "
        "FOR EACH ROW EXECUTE FUNCTION navigator.validate_publication_condition()"
    )
    execute(PUBLICATION_ELIGIBILITY_SQL)


def downgrade() -> None:
    execute = op.execute
    execute(PUBLICATION_ELIGIBILITY_WITHOUT_CONDITIONS_SQL)
    execute(
        "DROP TRIGGER trg_05_validate_publication_condition ON navigator.requirement_publications"
    )
    execute("DROP FUNCTION navigator.validate_publication_condition()")
    execute("DROP FUNCTION navigator.requirement_conditions_are_eligible(UUID)")
    execute(
        "DROP TRIGGER trg_80_validate_condition_fact_graph ON navigator.requirement_condition_facts"
    )
    execute(
        "DROP TRIGGER trg_80_validate_condition_set_graph ON navigator.requirement_condition_sets"
    )
    execute(
        "DROP TRIGGER trg_10_guard_governed_condition_history "
        "ON navigator.requirement_condition_sets"
    )
    execute("DROP TRIGGER trg_90_set_updated_at ON navigator.fact_definitions")
    execute("DROP TRIGGER trg_10_validate_fact_definition_governance ON navigator.fact_definitions")
    execute("DROP FUNCTION navigator.guard_governed_condition_history()")
    execute("DROP FUNCTION navigator.validate_condition_set_graph()")
    execute("DROP FUNCTION navigator.validate_fact_definition_governance()")
    execute("DROP FUNCTION navigator.condition_expression_fact_codes(JSONB)")
    execute("DROP FUNCTION navigator.condition_expression_is_valid(JSONB)")
    execute("DROP TABLE navigator.requirement_condition_facts")
    execute("DROP TABLE navigator.requirement_condition_sets")
    execute("DROP TABLE navigator.fact_definitions")
