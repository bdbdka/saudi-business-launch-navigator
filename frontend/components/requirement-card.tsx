"use client";

import { ActionabilityDetails } from "@/components/actionability-details";
import { useCatalogPresentation } from "@/components/catalog-mode-context";
import { OfficialLink } from "@/components/official-link";
import { ProgressCheckbox } from "@/components/progress-checkbox";
import type { ChecklistItem, QuestionFactCode, SourceTrace } from "@/lib/api/types";
import type { Dictionary, Locale } from "@/lib/i18n";

type RequirementVariant = "applicable" | "missing" | "secondary";

export function RequirementCard({
  item,
  locale,
  copy,
  variant,
  completed = false,
  onCompletionChange,
  onAnswerMissing,
}: {
  item: ChecklistItem;
  locale: Locale;
  copy: Dictionary;
  variant: RequirementVariant;
  completed?: boolean;
  onCompletionChange?: (completed: boolean) => void;
  onAnswerMissing: (factCode: QuestionFactCode) => void;
}) {
  const { policy } = useCatalogPresentation();
  const title = locale === "ar"
    ? item.project_arabic_title
    : item.project_english_title ?? item.project_arabic_title;
  const description = locale === "ar"
    ? item.project_arabic_description
    : item.project_english_description ?? item.project_arabic_description;
  const authority = locale === "ar"
    ? item.authority.name_ar
    : item.authority.name_en ?? item.authority.name_ar;
  const primary = item.sources.find((source) => source.source_role === "primary") ?? item.sources[0];
  const reasons = copy.reasonLabels as Record<string, string>;

  return (
    <article className={`requirement-item ${variant}${completed ? " user-completed" : ""}`}>
      <h4>{title}</h4>
      <p className="requirement-description">{description}</p>

      {variant === "missing" && item.evaluated_facts
        .filter((fact) => item.missing_fact_codes.includes(fact.fact_code))
        .map((fact) => (
          <div className="missing-action" key={fact.fact_code}>
            <p>{locale === "ar" ? fact.question_ar : fact.question_en}</p>
            <button className="button secondary small" type="button" onClick={() => onAnswerMissing(fact.fact_code)}>
              {copy.results.answerNow}
            </button>
          </div>
        ))}

      {variant === "applicable" && item.applicability_status === "APPLIES" && (
        <ActionabilityDetails items={item.actionability} locale={locale} copy={copy} />
      )}

      {primary && policy.isGovernedCatalog && (
        <div className="official-source-block">
          {policy.showAuthorityRows && (
            <p className="authority-line">
              <strong>{copy.results.authority}:</strong> {authority}
            </p>
          )}
          <OfficialLink
            url={primary.canonical_url}
            label={copy.results.officialSource}
            opensNewWindow={copy.results.opensNewWindow}
            unavailableLabel={copy.results.sourceUnavailable}
          />
        </div>
      )}

      {(item.evaluated_facts.length > 0
        || (policy.showSourceMetadata && (primary || item.sources.length > 1))) && (
        <details className="requirement-details">
          <summary>{copy.results.moreDetails}</summary>
          <div className="requirement-details-content">
            <p className="requirement-reason">
              <strong>{copy.results.why}</strong>{" "}
              {humanReason(
                item,
                locale,
                copy,
                reasons,
                policy.isPortfolioDemo
                  ? policy.text.unconditionalItem
                  : copy.results.unconditional,
                policy.isPortfolioDemo,
              )}
            </p>
            {item.evaluated_facts.length > 0 && (
              <div>
                <strong>
                  {policy.isPortfolioDemo ? policy.text.answersUsed : copy.results.answersUsed}
                </strong>
                <ul className="fact-trace-list">
                  {item.evaluated_facts.map((fact) => (
                    <li key={fact.fact_code}>
                      <span>{locale === "ar" ? fact.question_ar : fact.question_en}</span>
                      <strong>{answerLabel(fact, locale)}</strong>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {primary && policy.showSourceMetadata && (
              <dl className="source-metadata">
                <div><dt>{copy.results.sourceTitle}</dt><dd>{sourceTitle(primary, locale)}</dd></div>
                <div><dt>{copy.results.reviewed}</dt><dd>{formatVerifiedDate(primary, locale)}</dd></div>
              </dl>
            )}

            {policy.showSourceMetadata && item.sources.length > 1 && (
              <ul className="additional-source-list" aria-label={copy.results.additionalSources}>
                {item.sources.slice(1).map((source) => (
                  <li key={source.requirement_source_id}>
                    <span>{sourceTitle(source, locale)}</span>
                    <OfficialLink
                      url={source.canonical_url}
                      label={copy.results.officialSource}
                      opensNewWindow={copy.results.opensNewWindow}
                      unavailableLabel={copy.results.sourceUnavailable}
                    />
                  </li>
                ))}
              </ul>
            )}
          </div>
        </details>
      )}

      {variant === "applicable" && onCompletionChange && (
        <ProgressCheckbox checked={completed} copy={copy} onChange={onCompletionChange} />
      )}
    </article>
  );
}

function humanReason(
  item: ChecklistItem,
  locale: Locale,
  copy: Dictionary,
  reasons: Record<string, string>,
  unconditionalFallback: string,
  isPortfolioDemo: boolean,
): string {
  if (item.evaluated_facts.length === 1) {
    const fact = item.evaluated_facts[0];
    const question = locale === "ar" ? fact.question_ar : fact.question_en;
    if (
      (item.reason_code === "CONDITION_TRUE" && fact.supplied_value === true)
      || (item.reason_code === "CONDITION_FALSE" && fact.supplied_value === false)
    ) {
      return `${copy.results.answerUsed}: «${answerLabel(fact, locale)}» — ${question}`;
    }
  }
  if (isPortfolioDemo && item.reason_code === "UNCONDITIONAL_CURRENT_REQUIREMENT") {
    return unconditionalFallback;
  }
  return reasons[item.reason_code] ?? unconditionalFallback;
}

function sourceTitle(source: SourceTrace, locale: Locale): string {
  if (locale === "ar") return source.official_title_ar ?? source.official_title_en ?? source.canonical_host;
  return source.official_title_en ?? source.official_title_ar ?? source.canonical_host;
}

function formatVerifiedDate(source: SourceTrace, locale: Locale): string {
  const value = source.source_version_last_verified_at ?? source.source_last_verified_at;
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(locale === "ar" ? "ar-SA" : "en-GB", { dateStyle: "medium" }).format(date);
}

function answerLabel(fact: ChecklistItem["evaluated_facts"][number], locale: Locale): string {
  if (fact.supplied_value === true) {
    return locale === "ar" ? fact.answer_labels.true_ar : fact.answer_labels.true_en;
  }
  if (fact.supplied_value === false) {
    return locale === "ar" ? fact.answer_labels.false_ar : fact.answer_labels.false_en;
  }
  return locale === "ar" ? fact.answer_labels.unknown_ar : fact.answer_labels.unknown_en;
}
