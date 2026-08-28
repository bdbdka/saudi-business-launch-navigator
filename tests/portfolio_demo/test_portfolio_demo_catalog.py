"""Synthetic-demo content, deterministic behavior, and data-leak guards."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from saudi_business_launch_navigator.checklist.models import (
    ApplicabilityStatus,
    BusinessProfile,
    CoverageNotice,
    NavigationProfile,
    OwnershipInvestorRoute,
    PlannedLegalForm,
)
from saudi_business_launch_navigator.checklist.repository import StaticGovernedCatalogRepository
from saudi_business_launch_navigator.checklist.service import ChecklistService
from saudi_business_launch_navigator.portfolio_demo.catalog import (
    DEMO_MIGRATION_REVISION,
    DEMO_NAMESPACE,
    build_demo_catalog,
    dataset_fingerprint,
    demo_uuid,
    expanded_catalog_fingerprint,
    graph_sha256,
    load_portfolio_demo_spec,
)

ACTIVITIES = ("coffee_shop", "restaurant", "cloud_kitchen")


def _service() -> ChecklistService:
    spec = load_portfolio_demo_spec()
    catalogs = {
        code: build_demo_catalog(
            spec,
            activity_code=code,
            database_timestamp=datetime(2026, 8, 27, tzinfo=UTC),
            migration_revision=DEMO_MIGRATION_REVISION,
        )
        for code in ACTIVITIES
    }
    return ChecklistService(
        StaticGovernedCatalogRepository(catalogs),
        CoverageNotice(
            message_ar=spec.warning_ar,
            message_en=spec.warning_en,
            unresolved_topics=("synthetic_sample_data",),
            source_artifact_id=spec.dataset_code,
            source_artifact_fingerprint=dataset_fingerprint(spec),
        ),
    )


def test_demo_seed_identity_and_fingerprints_are_stable() -> None:
    spec = load_portfolio_demo_spec()

    assert str(DEMO_NAMESPACE) == "d9a3ad65-ce9d-53db-b4c4-235f01abe001"
    assert spec.database_identity == UUID("143e0ec8-ff17-5955-8e89-aab9932a2577")
    assert graph_sha256(spec) == "0a320574410660879c4c621c416214d032c15975a672fa8e8c1557c91fe06a49"
    assert dataset_fingerprint(spec) == (
        "96d772db6d67892e775ca4e480192bc181399e1dfebb5a810ee4aea7c51b1181"
    )
    assert expanded_catalog_fingerprint(spec) == (
        "4d37afebe49cf5ab19b2110ab2cc28fef708da23137f345e87fafdeca24533c6"
    )
    assert demo_uuid("database/portfolio-demo-v1") == spec.database_identity


def test_working_directory_cannot_shadow_the_reviewed_demo_seed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shadow = tmp_path / "public_demo"
    shadow.mkdir()
    (shadow / "PORTFOLIO_DEMO_CATALOG.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    load_portfolio_demo_spec.cache_clear()
    try:
        spec = load_portfolio_demo_spec()
    finally:
        load_portfolio_demo_spec.cache_clear()
    assert graph_sha256(spec) == "0a320574410660879c4c621c416214d032c15975a672fa8e8c1557c91fe06a49"


def test_demo_seed_is_visibly_synthetic_and_contains_no_private_or_government_evidence() -> None:
    spec = load_portfolio_demo_spec()
    serialized = spec.model_dump_json()

    assert spec.classification == "PORTFOLIO_DEMO_CATALOG"
    assert spec.source.url.startswith("https://example.invalid/")
    assert spec.source.code.startswith("demo_")
    assert spec.authority.code.startswith("demo_")
    assert all(requirement.code.startswith("demo_") for requirement in spec.requirements)
    assert "gov.sa" not in serialized.lower()
    assert "مادة" not in serialized
    assert "Article" not in serialized

    uuid_pattern = re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
        re.IGNORECASE,
    )
    expanded = tuple(
        build_demo_catalog(
            spec,
            activity_code=code,
            database_timestamp=datetime(2026, 8, 27, tzinfo=UTC),
            migration_revision=DEMO_MIGRATION_REVISION,
        )
        for code in ACTIVITIES
    )
    generated_ids = set(uuid_pattern.findall(repr(expanded)))
    assert generated_ids
    assert all(UUID(value).version == 5 for value in generated_ids)


@pytest.mark.asyncio
async def test_demo_questionnaire_is_exactly_7_8_7_and_every_fact_changes_a_result() -> None:
    service = _service()
    expected = {"coffee_shop": 7, "restaurant": 8, "cloud_kitchen": 7}

    for activity_code, count in expected.items():
        questionnaire = await service.build_questionnaire(activity_code)
        assert len(questionnaire.questions) == count
        assert [question.purpose.value for question in questionnaire.questions[:3]] == [
            "NAVIGATION",
            "NAVIGATION",
            "NAVIGATION",
        ]
        applicability = questionnaire.questions[3:]
        for question in applicability:
            true_result = await service.evaluate_business_profile(
                BusinessProfile(activity_code=activity_code, facts={question.fact_code: True})
            )
            false_result = await service.evaluate_business_profile(
                BusinessProfile(activity_code=activity_code, facts={question.fact_code: False})
            )
            assert any(
                item.applicability_status is ApplicabilityStatus.APPLIES
                and question.fact_code in {trace.fact_code for trace in item.evaluated_facts}
                for item in true_result.applies
            )
            assert any(
                item.applicability_status is ApplicabilityStatus.DOES_NOT_APPLY
                and question.fact_code in {trace.fact_code for trace in item.evaluated_facts}
                for item in false_result.does_not_apply
            )


@pytest.mark.asyncio
async def test_demo_unknown_journey_and_actionability_use_real_deterministic_service() -> None:
    service = _service()
    unknown = await service.evaluate_business_profile(
        BusinessProfile(activity_code="restaurant", facts={})
    )
    assert len(unknown.needs_information) == 5
    assert len(unknown.missing_navigation_information) == 3
    assert len(unknown.journey_guidance) == 6
    assert unknown.regulatory_snapshot.catalog_mode.value == "PORTFOLIO_DEMO"
    assert unknown.regulatory_snapshot.publication_count == 0

    complete = await service.evaluate_business_profile(
        BusinessProfile(
            activity_code="restaurant",
            facts={
                "has_employees": True,
                "has_food_establishment_workers": True,
                "offers_home_delivery": False,
                "uses_public_sidewalk_for_customer_service": False,
                "zatca_confirmed_mandatory_vat_registration_applies": False,
            },
        ),
        NavigationProfile(
            ownership_investor_route=(OwnershipInvestorRoute.SAUDI_PERSON_OR_SAUDI_OWNED_ENTITY),
            planned_legal_form=PlannedLegalForm.LIMITED_LIABILITY_COMPANY,
            has_selected_business_premises=True,
        ),
    )
    assert len(complete.applies) == 3
    assert len(complete.does_not_apply) == 3
    assert not complete.needs_information
    assert not complete.missing_navigation_information
    assert all(topic.routing_status.value == "ROUTED" for topic in complete.journey_guidance)
    unconditional = next(
        item for item in complete.applies if item.requirement_code == "demo_launch_orientation"
    )
    assert [item.detail_type for item in unconditional.actionability] == [
        "official_start",
        "document",
        "sequence",
    ]
