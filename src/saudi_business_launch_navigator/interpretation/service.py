"""Bounded interpretation, deterministic execution, and explanation."""

from __future__ import annotations

from saudi_business_launch_navigator.checklist.models import (
    BusinessChecklistResult,
    BusinessProfile,
    ChecklistItem,
    CoverageNotice,
)
from saudi_business_launch_navigator.checklist.questionnaire import QUESTION_TEXT
from saudi_business_launch_navigator.checklist.service import ChecklistService
from saudi_business_launch_navigator.interpretation.exceptions import InterpretationError
from saudi_business_launch_navigator.interpretation.models import (
    AIErrorInfo,
    ChecklistExplanation,
    ClarificationPrompt,
    ClarificationTarget,
    CoverageLimitation,
    ExplanationContext,
    ExplanationContextItem,
    InteractionLanguage,
    InterpretationRequest,
    InterpretationResult,
    ValidatedInterpretation,
)
from saudi_business_launch_navigator.interpretation.ports import AIExplainer, AIInterpreter
from saudi_business_launch_navigator.interpretation.validation import (
    coverage_limitation_for,
    merge_profile,
    reject_sensitive_input,
    validate_explanation,
    validate_interpretation,
)

_ACTIVITY_CLARIFICATION = ClarificationPrompt(
    target=ClarificationTarget.ACTIVITY_CODE,
    question_ar="هل نشاطك مقهى أم مطعم أم مطبخ سحابي؟",
    question_en="Is your activity a coffee shop, restaurant, or cloud kitchen?",
)


class BoundedInterpreterService:
    """Run the provider, then independently validate every candidate."""

    def __init__(self, interpreter: AIInterpreter) -> None:
        self._interpreter = interpreter

    async def interpret(
        self,
        request: InterpretationRequest,
        existing_profile: BusinessProfile | None = None,
    ) -> ValidatedInterpretation:
        reject_sensitive_input(request.user_text)
        candidate = await self._interpreter.interpret(request.user_text)
        return validate_interpretation(
            user_text=request.user_text,
            candidate=candidate,
            language_override=request.language_override,
            existing_profile=existing_profile,
        )


class BoundedExplanationService:
    """Generate prose from a compact checklist projection and bind it back safely."""

    def __init__(self, explainer: AIExplainer) -> None:
        self._explainer = explainer

    async def explain(
        self,
        checklist: BusinessChecklistResult,
        language: InteractionLanguage,
    ) -> ChecklistExplanation:
        context = _explanation_context(checklist, language)
        candidate = await self._explainer.explain(context)
        return validate_explanation(candidate=candidate, checklist=checklist, language=language)


class InterpretationService:
    """Orchestrate AI around—never inside—the deterministic checklist engine."""

    def __init__(
        self,
        *,
        interpreter: BoundedInterpreterService,
        explainer: BoundedExplanationService,
        checklist_service: ChecklistService,
        coverage_notice: CoverageNotice,
    ) -> None:
        self._interpreter = interpreter
        self._explainer = explainer
        self._checklist_service = checklist_service
        self._coverage_notice = coverage_notice

    async def process(
        self,
        request: InterpretationRequest,
        existing_profile: BusinessProfile | None = None,
    ) -> InterpretationResult:
        limitation = coverage_limitation_for(request.user_text, self._coverage_notice)
        try:
            interpretation = await self._interpreter.interpret(request, existing_profile)
        except InterpretationError as exc:
            return _failed_result(exc, coverage_limitation=limitation)

        if interpretation.activity_code is None:
            return InterpretationResult(
                interpretation=interpretation,
                profile=existing_profile,
                checklist=None,
                explanation=None,
                clarifications=(_ACTIVITY_CLARIFICATION,),
                coverage_limitation=limitation,
                ai_error=None,
            )

        profile = merge_profile(interpretation, existing_profile)
        checklist = await self._checklist_service.evaluate_business_profile(profile)
        clarifications = _clarifications(interpretation, checklist)
        try:
            explanation = await self._explainer.explain(checklist, interpretation.language)
            error = None
        except InterpretationError as exc:
            explanation = None
            error = AIErrorInfo(code=exc.code, message=str(exc))

        return InterpretationResult(
            interpretation=interpretation,
            profile=profile,
            checklist=checklist,
            explanation=explanation,
            clarifications=clarifications,
            coverage_limitation=limitation,
            ai_error=error,
        )


def _failed_result(
    exc: InterpretationError,
    *,
    coverage_limitation: CoverageLimitation | None,
) -> InterpretationResult:
    return InterpretationResult(
        interpretation=None,
        profile=None,
        checklist=None,
        explanation=None,
        clarifications=(),
        coverage_limitation=coverage_limitation,
        ai_error=AIErrorInfo(code=exc.code, message=str(exc)),
    )


def _clarifications(
    interpretation: ValidatedInterpretation,
    checklist: BusinessChecklistResult,
) -> tuple[ClarificationPrompt, ...]:
    questions = {question.fact_code: question for question in checklist.questions_needed}
    prompts: dict[ClarificationTarget, ClarificationPrompt] = {}
    for target in interpretation.clarification_targets:
        if target is ClarificationTarget.ACTIVITY_CODE:
            prompts[target] = _ACTIVITY_CLARIFICATION
            continue
        question = questions.get(target.value)
        if question is not None:
            prompts[target] = ClarificationPrompt(
                target=target,
                question_ar=question.question_ar,
                question_en=question.question_en,
            )
        else:
            authored = QUESTION_TEXT[target.value]
            prompts[target] = ClarificationPrompt(
                target=target,
                question_ar=authored.question_ar,
                question_en=authored.question_en,
            )
    for question in checklist.questions_needed:
        target = ClarificationTarget(question.fact_code)
        prompts[target] = ClarificationPrompt(
            target=target,
            question_ar=question.question_ar,
            question_en=question.question_en,
        )
    return tuple(prompts[target] for target in sorted(prompts, key=str))


def _explanation_context(
    checklist: BusinessChecklistResult,
    language: InteractionLanguage,
) -> ExplanationContext:
    items = (*checklist.applies, *checklist.does_not_apply, *checklist.needs_information)
    return ExplanationContext(
        language=language,
        items=tuple(_context_item(index, item, language) for index, item in enumerate(items)),
        coverage_status=checklist.coverage_notice.coverage_status.value,
        coverage_message=(
            checklist.coverage_notice.message_ar
            if language is InteractionLanguage.ARABIC
            else checklist.coverage_notice.message_en
        ),
        unresolved_topics=checklist.coverage_notice.unresolved_topics,
    )


def _context_item(
    index: int,
    item: ChecklistItem,
    language: InteractionLanguage,
) -> ExplanationContextItem:
    if language is InteractionLanguage.ARABIC:
        title = item.project_arabic_title
        description = item.project_arabic_description
        authority = item.authority.name_ar
    else:
        title = item.project_english_title or item.project_arabic_title
        description = item.project_english_description or item.project_arabic_description
        authority = item.authority.name_en or item.authority.name_ar
    return ExplanationContextItem(
        item_index=index,
        applicability_status=item.applicability_status,
        reason_code=item.reason_code.value,
        project_title=title,
        project_description=description,
        authority_name=authority,
        missing_fact_codes=item.missing_fact_codes,
        source_codes=tuple(source.source_code for source in item.sources),
    )


__all__ = [
    "BoundedExplanationService",
    "BoundedInterpreterService",
    "InterpretationService",
]
