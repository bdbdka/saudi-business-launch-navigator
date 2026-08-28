"""Controlled database vocabularies mirrored by named PostgreSQL checks."""

from enum import StrEnum


class EntityType(StrEnum):
    GOVERNMENT_MINISTRY = "government_ministry"
    GOVERNMENT_AUTHORITY = "government_authority"
    GOVERNMENT_CENTER = "government_center"
    GOVERNMENT_ORGANIZATION = "government_organization"
    HISTORICAL_ENTITY = "historical_entity"


class PlatformType(StrEnum):
    GOVERNMENT_PLATFORM = "government_platform"
    OFFICIAL_LEGAL_PORTAL = "official_legal_portal"
    OFFICIAL_DATASET_PORTAL = "official_dataset_portal"


class DomainCategory(StrEnum):
    GOVERNMENT_AGENCY_DOMAIN = "government_agency_domain"
    VERIFIED_GOVERNMENT_PLATFORM = "verified_government_platform"
    OFFICIAL_SUBDOMAIN = "official_subdomain"
    PENDING_VERIFICATION = "pending_verification"
    REJECTED = "rejected"


class GovernanceStatus(StrEnum):
    DISCOVERED = "discovered"
    RESEARCH_IN_PROGRESS = "research_in_progress"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_ADDITIONAL_REVIEW = "requires_additional_review"
    BLOCKED_BY_CONFLICT = "blocked_by_conflict"
    STALE = "stale"
    EXPIRED = "expired"
    INACCESSIBLE = "inaccessible"
    SUPERSEDED = "superseded"
    HISTORICAL = "historical"


class SourceType(StrEnum):
    ENTITY_HOMEPAGE = "entity_homepage"
    ENTITY_ABOUT_PAGE = "entity_about_page"
    ENTITY_POLICY_PAGE = "entity_policy_page"
    ENTITY_NEWS_RELEASE = "entity_news_release"
    OFFICIAL_NEWS_RELEASE = "official_news_release"
    OFFICIAL_GAZETTE_DECISION = "official_gazette_decision"
    OFFICIAL_GAZETTE_REGULATION = "official_gazette_regulation"
    OFFICIAL_GUIDE = "official_guide"
    OFFICIAL_BULLETIN = "official_bulletin"
    OFFICIAL_DATASET = "official_dataset"
    PLATFORM_ABOUT_PAGE = "platform_about_page"
    OFFICIAL_LEGAL_PORTAL = "official_legal_portal"
    GOVERNANCE_DOCUMENT_PAGE = "governance_document_page"
    OFFICIAL_SERVICE_PAGE = "official_service_page"


class ResearchStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    REQUIRES_ADDITIONAL_RESEARCH = "requires_additional_research"


class ResearchRecommendation(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUIRES_ADDITIONAL_REVIEW = "requires_additional_review"
    BLOCKED_BY_CONFLICT = "blocked_by_conflict"


class ReviewDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED_FOR_RESEARCH = "returned_for_research"
    REQUIRES_ADDITIONAL_REVIEW = "requires_additional_review"
    BLOCKED_BY_CONFLICT = "blocked_by_conflict"
    MARKED_STALE = "marked_stale"
    MARKED_INACCESSIBLE = "marked_inaccessible"
    MARKED_SUPERSEDED = "marked_superseded"
    MARKED_HISTORICAL = "marked_historical"
    MARKED_EXPIRED = "marked_expired"


class ResearchEvidenceRole(StrEnum):
    PRIMARY = "primary"
    SUPPORTING = "supporting"
    CONFLICTING = "conflicting"
    HISTORICAL = "historical"
    CONTEXT = "context"


class RequirementScope(StrEnum):
    NATIONAL = "national"
    ACTIVITY_SPECIFIC = "activity_specific"
    SITE_DEPENDENT = "site_dependent"


class RequirementVerificationStatus(StrEnum):
    PENDING_SOURCE_VERIFICATION = "pending_source_verification"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONFLICTING = "conflicting"
    STALE = "stale"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    HISTORICAL = "historical"


class SourceRole(StrEnum):
    PRIMARY = "primary"
    SUPPORTING = "supporting"
    CLARIFYING = "clarifying"
    CONFLICTING = "conflicting"
    SUPERSEDING = "superseding"
    HISTORICAL = "historical"


class RelationshipStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPERSEDED = "superseded"


class PublicationStatus(StrEnum):
    PUBLISHED = "published"
    WITHDRAWN = "withdrawn"


class LocationType(StrEnum):
    CITY = "city"


class FactDataType(StrEnum):
    BOOLEAN = "boolean"
    INTEGER = "integer"
    DECIMAL = "decimal"
    ENUM = "enum"


class FactPrivacyClass(StrEnum):
    NON_PERSONAL_BUSINESS = "non_personal_business"


class ConditionVerificationStatus(StrEnum):
    PENDING_SOURCE_VERIFICATION = "pending_source_verification"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONFLICTING = "conflicting"
    STALE = "stale"
    SUPERSEDED = "superseded"
    HISTORICAL = "historical"


class JourneyCoverageState(StrEnum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    REQUIRES_OFFICIAL_CONFIRMATION = "REQUIRES_OFFICIAL_CONFIRMATION"
    UNRESOLVED = "UNRESOLVED"
    NOT_RESEARCHED = "NOT_RESEARCHED"


class JourneyLimitationType(StrEnum):
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    MATERIAL_CONFLICT = "material_conflict"
    UNRESOLVED_SUPERSESSION = "unresolved_supersession"
    CASE_CONFIRMATION = "case_confirmation"


class JourneyEvidenceRole(StrEnum):
    PRIMARY = "primary"
    SUPPORTING = "supporting"
    CLARIFYING = "clarifying"
    CONFLICTING = "conflicting"
    HISTORICAL = "historical"


class JourneyRequirementLinkRole(StrEnum):
    COVERED_BY = "covered_by"
    PARTIALLY_COVERED_BY = "partially_covered_by"
    RELATED = "related"


class JourneyFactInputRole(StrEnum):
    NAVIGATION = "navigation"
    CONFIRMATION = "confirmation"


class JourneyDestinationKind(StrEnum):
    AUTHORITY = "authority"
    PLATFORM = "platform"
    SERVICE = "service"
    PAGE = "page"


class JourneyRouteMatchKind(StrEnum):
    ALWAYS = "always"
    EQUALS = "equals"


class ContentReleaseStatus(StrEnum):
    RELEASED = "released"
    WITHDRAWN = "withdrawn"


class ActionabilityDetailType(StrEnum):
    OFFICIAL_START = "official_start"
    PREREQUISITE = "prerequisite"
    DOCUMENT = "document"
    FEE = "fee"
    PROCESSING_TIME = "processing_time"
    SEQUENCE = "sequence"
    VALIDITY = "validity"


class ActionabilityValueState(StrEnum):
    VERIFIED = "VERIFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


def enum_sql(enum_type: type[StrEnum]) -> str:
    """Return safely quoted enum values for a static check-constraint expression."""
    return ", ".join(f"'{member.value}'" for member in enum_type)
