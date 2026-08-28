"""Deterministic post-AI validation and conservative language-level guards."""

from __future__ import annotations

import re
from collections import defaultdict

from saudi_business_launch_navigator.checklist.models import (
    BusinessChecklistResult,
    BusinessProfile,
    ChecklistItem,
    CoverageNotice,
)
from saudi_business_launch_navigator.interpretation.exceptions import (
    AIErrorCode,
    AIOutputValidationError,
    SensitiveInputError,
)
from saudi_business_launch_navigator.interpretation.models import (
    AuthoritativeItemExplanation,
    ChecklistExplanation,
    ClarificationTarget,
    CoverageLimitation,
    ExplanationCandidate,
    FactCandidate,
    GovernedFactCode,
    InteractionLanguage,
    InterpretationCandidate,
    SupportedActivity,
    ValidatedFact,
    ValidatedInterpretation,
)

_ARABIC_CHARACTER = re.compile(r"[\u0600-\u06ff]")
_LATIN_CHARACTER = re.compile(r"[A-Za-z]")
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE = re.compile(r"(?<!\d)(?:\+?966|00966|05)\s*[- ]?\d(?:[- ]?\d){7,8}(?!\d)")
_IDENTIFIER = re.compile(
    r"(?:national\s+id|iqama|هوية|الإقامة|اقامة)\D{0,20}\d{8,12}",
    re.IGNORECASE,
)
_ADDRESS = re.compile(
    r"(?:home\s+address|personal\s+address|عنوان\s+(?:المنزل|السكن))\s*[:\uff1a]",
    re.IGNORECASE,
)

_UNCERTAINTY = (
    "not sure",
    "don't know",
    "do not know",
    "unknown",
    "maybe",
    "might",
    "غير متأكد",
    "لا أعرف",
    "ما أعرف",
    "ربما",
    "يمكن",
)
_NEGATION = (
    "no ",
    "don't have",
    "do not have",
    "without",
    "zero ",
    "not reached",
    "not met",
    "hasn't been reached",
    "have not been met",
    "لا يوجد",
    "ليس لدي",
    "ما عندي",
    "بدون",
    "لم أبلغ",
    "لم يتم بلوغ",
    "لم تتحقق",
)
_EMPLOYEE_TERMS = (
    "employee",
    "employees",
    "worker",
    "workers",
    "staff",
    "employ",
    "موظف",
    "موظفين",
    "موظفون",
    "عامل",
    "عمال",
)
_FOOD_CONTEXT = (
    "food",
    "restaurant",
    "coffee shop",
    "cafe",
    "café",
    "kitchen",
    "public health",
    "غذاء",
    "غذائية",
    "مطعم",
    "مقهى",
    "كوفي",
    "مطبخ",
    "صحة عامة",
)
_POSSESSION = (
    "i have",
    "we have",
    "my business has",
    "my establishment has",
    "i employ",
    "لدينا",
    "لدي",
    "عندي",
    "في المنشأة",
)
_POSITIVE_NUMBER_WORDS = (
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "واحد",
    "اثنين",
    "ثلاث",
    "أربع",
    "اربع",
    "خمس",
    "ست",
    "سبع",
    "ثمان",
    "تسع",
    "عشر",
)
_DELIVERY_TERMS = ("home delivery", "delivery", "توصيل", "التوصيل")
_DELIVERY_POSITIVE = (
    "offer",
    "provide",
    "we deliver",
    "will have",
    "سأقدم",
    "سنقدم",
    "سنوفّر",
    "سنوفر",
    "نقدم",
    "لدينا",
)
_SIDEWALK_TERMS = ("public sidewalk", "sidewalk", "الرصيف العام", "الرصيف")
_SIDEWALK_SERVICE_TERMS = (
    "customer service",
    "customers",
    "seating",
    "tables",
    "خدمة العملاء",
    "للعملاء",
    "جلسات",
    "طاولات",
)
_USE_POSITIVE = ("use", "will use", "سنستخدم", "سأستخدم", "نستخدم", "سيستخدم")
_FUTURE_NEGATION = (
    "no ",
    "not ",
    "won't",
    "will not",
    "لن ",
    "لا ",
    "بدون",
)

_ACTIVITY_TERMS: dict[SupportedActivity, tuple[str, ...]] = {
    SupportedActivity.COFFEE_SHOP: ("coffee shop", "cafe", "café", "كوفي", "مقهى"),
    SupportedActivity.RESTAURANT: ("restaurant", "مطعم"),
    SupportedActivity.CLOUD_KITCHEN: (
        "cloud kitchen",
        "ghost kitchen",
        "مطبخ سحابي",
    ),
}

_UNRESOLVED_TERMS: dict[str, tuple[str, ...]] = {
    "civil_defense": ("civil defense", "salamah", "سلامة", "الدفاع المدني"),
    "sfda": ("sfda", "food and drug authority", "هيئة الغذاء والدواء"),
    "commercial_registration_legal_form_ownership": (
        "legal form",
        "ownership form",
        "الشكل القانوني",
        "الملكية",
    ),
    "zakat": ("zakat", "زكاة", "الزكاة"),
    "e_invoicing": ("e-invoicing", "electronic invoicing", "الفوترة الإلكترونية"),
    "site_dependent_detailed_rules": (
        "site requirements",
        "building requirements",
        "اشتراطات الموقع",
        "اشتراطات المبنى",
    ),
    "legal_supersession": (
        "legal supersession",
        "superseded regulation",
        "النسخ القانوني",
        "لائحة ملغاة",
    ),
}

_FORBIDDEN_EXPLANATION = (
    "fee",
    "cost",
    "sar",
    "riyal",
    "deadline",
    "within ",
    " days",
    "upload document",
    "required document",
    "fully compliant",
    "guaranteed approval",
    "complete coverage",
    "no other requirements",
    "رسوم",
    "تكلفة",
    "ريال",
    "موعد نهائي",
    "خلال ",
    " يوم",
    "ارفع المستند",
    "المستندات المطلوبة",
    "امتثال كامل",
    "ضمان الموافقة",
    "تغطية كاملة",
    "لا توجد متطلبات أخرى",
)


def reject_sensitive_input(user_text: str) -> None:
    """Reject obvious unnecessary PII before any external AI call."""

    if any(pattern.search(user_text) for pattern in (_EMAIL, _PHONE, _IDENTIFIER, _ADDRESS)):
        raise SensitiveInputError(
            AIErrorCode.SENSITIVE_INPUT,
            "Remove personal identifiers and submit only non-personal business facts.",
        )


def detect_language(user_text: str) -> InteractionLanguage:
    """Choose Arabic or English deterministically from character counts."""

    arabic_count = len(_ARABIC_CHARACTER.findall(user_text))
    latin_count = len(_LATIN_CHARACTER.findall(user_text))
    return (
        InteractionLanguage.ARABIC
        if arabic_count > 0 and arabic_count >= latin_count
        else InteractionLanguage.ENGLISH
    )


def validate_interpretation(
    *,
    user_text: str,
    candidate: InterpretationCandidate,
    language_override: InteractionLanguage | None = None,
    existing_profile: BusinessProfile | None = None,
) -> ValidatedInterpretation:
    """Accept only grounded activity/fact candidates with no regulatory inference."""

    normalized_input = _normalize(user_text)
    language = language_override or detect_language(user_text)
    targets = set(candidate.clarification_targets)
    unsupported: set[str] = {
        value
        for value in candidate.unsupported_or_unmapped_statements
        if _is_grounded_fragment(normalized_input, value)
    }

    activity = _validate_activity(candidate, normalized_input)
    if existing_profile is not None:
        existing_activity = SupportedActivity(existing_profile.activity_code)
        if activity is not None and activity is not existing_activity:
            targets.add(ClarificationTarget.ACTIVITY_CODE)
            activity = existing_activity
        elif activity is None:
            activity = existing_activity
    if activity is None:
        targets.add(ClarificationTarget.ACTIVITY_CODE)

    candidates_by_code: dict[GovernedFactCode, list[FactCandidate]] = defaultdict(list)
    for fact in candidate.fact_candidates:
        candidates_by_code[fact.code].append(fact)

    validated_facts: list[ValidatedFact] = []
    for code in GovernedFactCode:
        proposed = candidates_by_code.get(code, [])
        if not proposed:
            continue
        grounded: list[ValidatedFact] = []
        unresolved = False
        for fact in proposed:
            if not _is_grounded_fragment(normalized_input, fact.evidence_text):
                unresolved = True
                continue
            if fact.value is None:
                unresolved = True
                unsupported.add(fact.evidence_text)
                continue
            signal = _direct_fact_signal(code, fact.evidence_text)
            if signal is None or signal is not fact.value:
                unresolved = True
                unsupported.add(fact.evidence_text)
                continue
            grounded.append(
                ValidatedFact(
                    code=code,
                    value=fact.value,
                    evidence_text=fact.evidence_text,
                    mapping_basis=fact.mapping_basis,
                )
            )

        distinct_values = {fact.value for fact in grounded}
        existing_value = (
            existing_profile.facts.get(code.value) if existing_profile is not None else None
        )
        contradicts_existing = (
            bool(grounded)
            and existing_value is not None
            and grounded[0].value is not existing_value
        )
        if len(distinct_values) > 1 or contradicts_existing:
            unresolved = True
            grounded = []
        if unresolved:
            targets.add(ClarificationTarget(code.value))
        if grounded:
            validated_facts.append(grounded[0])

    return ValidatedInterpretation(
        language=language,
        activity_code=activity,
        facts=tuple(sorted(validated_facts, key=lambda value: value.code.value)),
        clarification_needed=bool(targets),
        clarification_targets=tuple(sorted(targets, key=str)),
        unsupported_or_unmapped_statements=tuple(sorted(unsupported)),
    )


def merge_profile(
    interpretation: ValidatedInterpretation,
    existing_profile: BusinessProfile | None,
) -> BusinessProfile:
    """Merge only non-contradictory validated facts into an in-memory profile."""

    if interpretation.activity_code is None:
        raise AIOutputValidationError(
            AIErrorCode.INVALID_OUTPUT,
            "A supported activity must be clarified before checklist evaluation.",
        )
    facts = dict(existing_profile.facts) if existing_profile is not None else {}
    for fact in interpretation.facts:
        facts[fact.code.value] = fact.value
    return BusinessProfile(activity_code=interpretation.activity_code.value, facts=facts)


def validate_explanation(
    *,
    candidate: ExplanationCandidate,
    checklist: BusinessChecklistResult,
    language: InteractionLanguage,
) -> ChecklistExplanation:
    """Bind prose by index while authoritative checklist fields remain unchanged."""

    if candidate.language is not language:
        raise AIOutputValidationError(
            AIErrorCode.INVALID_OUTPUT,
            "AI explanation language does not match the requested language.",
        )
    authoritative_items = _ordered_checklist_items(checklist)
    by_index = {item.item_index: item for item in candidate.items}
    expected_indexes = set(range(len(authoritative_items)))
    if len(by_index) != len(candidate.items) or set(by_index) != expected_indexes:
        raise AIOutputValidationError(
            AIErrorCode.INVALID_OUTPUT,
            "AI explanation items do not match the authoritative checklist.",
        )
    for item in candidate.items:
        _validate_safe_prose(item.summary)
        _validate_safe_prose(item.why_status)
    _validate_safe_prose(candidate.coverage_summary)
    coverage_normalized = _normalize(candidate.coverage_summary)
    required_markers = (
        ("partial", "unresolved", "verified only", "not complete")
        if language is InteractionLanguage.ENGLISH
        else ("جزئي", "جزئية", "غير محسوم", "غير مكتمل", "المتحقق منها فقط")
    )
    if not any(marker in coverage_normalized for marker in required_markers):
        raise AIOutputValidationError(
            AIErrorCode.INVALID_OUTPUT,
            "AI explanation omitted the partial-coverage limitation.",
        )

    questions = {question.fact_code: question for question in checklist.questions_needed}
    return ChecklistExplanation(
        language=language,
        items=tuple(
            AuthoritativeItemExplanation(
                item=item,
                summary=by_index[index].summary,
                why_status=by_index[index].why_status,
                next_question=(
                    questions.get(item.missing_fact_codes[0])
                    if len(item.missing_fact_codes) == 1
                    else None
                ),
            )
            for index, item in enumerate(authoritative_items)
        ),
        authoritative_coverage=checklist.coverage_notice,
        ai_coverage_summary=candidate.coverage_summary,
    )


def coverage_limitation_for(
    user_text: str,
    coverage: CoverageNotice,
) -> CoverageLimitation | None:
    """Return a deterministic limitation for explicitly unresolved topics."""

    normalized = _normalize(user_text)
    unresolved = tuple(
        sorted(
            topic
            for topic in coverage.unresolved_topics
            if any(term in normalized for term in _UNRESOLVED_TERMS.get(topic, ()))
        )
    )
    if not unresolved:
        return None
    return CoverageLimitation(
        unresolved_topics=unresolved,
        message_ar=(
            "لا تدعم البيانات المحكومة حالياً تحديداً تنظيمياً متحققاً لهذه المسألة. "
            "لا يعني ذلك أنها غير مطلوبة."
        ),
        message_en=(
            "The current governed dataset does not support a verified determination for this "
            "topic. This does not mean it is not required."
        ),
    )


def _validate_activity(
    candidate: InterpretationCandidate,
    normalized_input: str,
) -> SupportedActivity | None:
    if candidate.activity_candidate is None or candidate.activity_evidence is None:
        return None
    if not _is_grounded_fragment(normalized_input, candidate.activity_evidence):
        return None
    evidence = _normalize(candidate.activity_evidence)
    if any(term in evidence for term in _ACTIVITY_TERMS[candidate.activity_candidate]):
        return candidate.activity_candidate
    return None


def _direct_fact_signal(code: GovernedFactCode, evidence_text: str) -> bool | None:
    evidence = _normalize(evidence_text)
    if any(value in evidence for value in _UNCERTAINTY):
        return None
    if code is GovernedFactCode.HAS_EMPLOYEES:
        return _worker_signal(evidence, require_food_context=False)
    if code is GovernedFactCode.HAS_FOOD_ESTABLISHMENT_WORKERS:
        return _worker_signal(evidence, require_food_context=True)
    if code is GovernedFactCode.GOSI_COVERAGE_CONDITIONS_MET:
        gosi = any(
            value in evidence for value in ("gosi", "social insurance", "التأمينات الاجتماعية")
        )
        conditions = any(value in evidence for value in ("coverage conditions", "شروط الخضوع"))
        if not (gosi and conditions):
            return None
        if any(value in evidence for value in _NEGATION):
            return False
        if any(value in evidence for value in ("met", "confirmed", "تحققت", "تم التأكد")):
            return True
    if code is GovernedFactCode.OFFERS_HOME_DELIVERY:
        if not any(value in evidence for value in _DELIVERY_TERMS):
            return None
        if any(value in evidence for value in _FUTURE_NEGATION):
            return False
        if any(value in evidence for value in _DELIVERY_POSITIVE):
            return True
        return None
    if code is GovernedFactCode.USES_PUBLIC_SIDEWALK_FOR_CUSTOMER_SERVICE:
        has_sidewalk = any(value in evidence for value in _SIDEWALK_TERMS)
        has_customer_service = any(value in evidence for value in _SIDEWALK_SERVICE_TERMS)
        if not (has_sidewalk and has_customer_service):
            return None
        if any(value in evidence for value in _FUTURE_NEGATION):
            return False
        if any(value in evidence for value in _USE_POSITIVE):
            return True
    return None


def _worker_signal(evidence: str, *, require_food_context: bool) -> bool | None:
    if not any(value in evidence for value in _EMPLOYEE_TERMS):
        return None
    if require_food_context and not any(value in evidence for value in _FOOD_CONTEXT):
        return None
    if any(value in evidence for value in _NEGATION):
        return False
    positive_number = bool(re.search(r"\b[1-9]\d*\b", evidence)) or any(
        value in evidence for value in _POSITIVE_NUMBER_WORDS
    )
    if positive_number or any(value in evidence for value in _POSSESSION):
        return True
    return None


def _validate_safe_prose(value: str) -> None:
    normalized = _normalize(value)
    if re.search(r"\d|[\u0660-\u0669]", normalized) or any(
        term in normalized for term in _FORBIDDEN_EXPLANATION
    ):
        raise AIOutputValidationError(
            AIErrorCode.INVALID_OUTPUT,
            "AI explanation contained unsupported regulatory detail.",
        )


def _ordered_checklist_items(checklist: BusinessChecklistResult) -> tuple[ChecklistItem, ...]:
    return (*checklist.applies, *checklist.does_not_apply, *checklist.needs_information)


def _is_grounded_fragment(normalized_input: str, fragment: str) -> bool:
    return _normalize(fragment) in normalized_input


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


__all__ = [
    "coverage_limitation_for",
    "detect_language",
    "merge_profile",
    "reject_sensitive_input",
    "validate_explanation",
    "validate_interpretation",
]
