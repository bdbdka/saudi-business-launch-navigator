"""Import every table model so Alembic receives complete metadata."""

from saudi_business_launch_navigator.db.models.actionability import (
    RequirementActionabilityRelease,
    RequirementActionabilityVersion,
)
from saudi_business_launch_navigator.db.models.conditions import (
    FactDefinition,
    RequirementConditionFact,
    RequirementConditionSet,
)
from saudi_business_launch_navigator.db.models.governance import (
    Domain,
    GovernmentEntity,
    Platform,
    ResearchEvent,
    ResearchEventEvidence,
    ReviewEvent,
    Source,
    SourceVersion,
)
from saudi_business_launch_navigator.db.models.journey import (
    JourneyTopic,
    JourneyTopicDestination,
    JourneyTopicEvidence,
    JourneyTopicFactLink,
    JourneyTopicRelease,
    JourneyTopicRequirementLink,
    JourneyTopicVersion,
)
from saudi_business_launch_navigator.db.models.reference import (
    BusinessActivity,
    SupportedLocation,
)
from saudi_business_launch_navigator.db.models.requirements import (
    Requirement,
    RequirementActivity,
    RequirementPublication,
    RequirementPublicationSource,
    RequirementSource,
    RequirementVersion,
)

__all__ = [
    "BusinessActivity",
    "Domain",
    "FactDefinition",
    "GovernmentEntity",
    "JourneyTopic",
    "JourneyTopicDestination",
    "JourneyTopicEvidence",
    "JourneyTopicFactLink",
    "JourneyTopicRelease",
    "JourneyTopicRequirementLink",
    "JourneyTopicVersion",
    "Platform",
    "Requirement",
    "RequirementActionabilityRelease",
    "RequirementActionabilityVersion",
    "RequirementActivity",
    "RequirementConditionFact",
    "RequirementConditionSet",
    "RequirementPublication",
    "RequirementPublicationSource",
    "RequirementSource",
    "RequirementVersion",
    "ResearchEvent",
    "ResearchEventEvidence",
    "ReviewEvent",
    "Source",
    "SourceVersion",
    "SupportedLocation",
]
