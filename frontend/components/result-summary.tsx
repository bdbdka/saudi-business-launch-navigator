"use client";

import { useIsPortfolioDemo } from "@/components/catalog-mode-context";
import type { ChecklistResult } from "@/lib/api/types";
import { formatNumber, type Dictionary, type Locale } from "@/lib/i18n";

export function ResultSummary({
  result,
  completedCount,
  locale,
  copy,
  onEdit,
}: {
  result: ChecklistResult;
  completedCount: number;
  locale: Locale;
  copy: Dictionary;
  onEdit: () => void;
}) {
  const isDemo = useIsPortfolioDemo();
  const totalApplicable = result.applies.length;
  const remaining = Math.max(0, totalApplicable - completedCount);
  const unresolved = result.needs_information.length > 0;
  const requestedAnswerCount = result.questions_needed.length;
  const progressPercent = totalApplicable > 0 ? (completedCount / totalApplicable) * 100 : 0;
  const values = {
    total: formatNumber(totalApplicable, locale),
    completed: formatNumber(completedCount, locale),
    remaining: formatNumber(remaining, locale),
    count: formatNumber(requestedAnswerCount, locale),
  };
  const progressText = interpolate(copy.results.progressValueTemplate, values);

  return (
    <div className="result-introduction" aria-label={copy.results.summary}>
      <h3>{copy.results.introTitle}</h3>
      <p>
        {isDemo
          ? (locale === "ar"
              ? "راجع المهام النموذجية وأكمل أي إجابة ناقصة لفهم تجربة المنتج."
              : "Review the sample tasks and complete missing answers to explore the product flow.")
          : copy.results.introBody}
      </p>

      <div className={`checklist-determination${unresolved ? " unresolved" : ""}`}>
        {unresolved ? (
          <>
            <strong>{copy.results.checklistNeedsInformation}</strong>
            <p>{interpolate(copy.results.checklistNeedsInformationTemplate, values)}</p>
            <button className="button secondary small" type="button" onClick={onEdit}>
              {copy.results.edit}
            </button>
          </>
        ) : (
          <p>
            {isDemo
              ? (locale === "ar"
                  ? "حُددت قائمة العرض من البيانات النموذجية وإجاباتك الحالية."
                  : "This demo checklist was determined from sample data and your current answers.")
              : copy.results.checklistDetermined}
          </p>
        )}
      </div>

      <div className="checklist-progress-summary">
        <h3>{copy.results.projectChecklistTitle}</h3>
        <p className="applicable-total">{interpolate(copy.results.requirementsApplyTemplate, values)}</p>
        <div className="personal-progress-counts" aria-live="polite">
          <strong>{interpolate(copy.results.progressCompletedTemplate, values)}</strong>
          <span>{interpolate(copy.results.progressRemainingTemplate, values)}</span>
        </div>
        {totalApplicable > 0 && (
          <div
            className="personal-progress-track"
            role="progressbar"
            aria-label={copy.results.progressBarLabel}
            aria-valuemin={0}
            aria-valuemax={totalApplicable}
            aria-valuenow={completedCount}
            aria-valuetext={progressText}
          >
            <span style={{ width: `${progressPercent}%` }} />
          </div>
        )}
        <p className="personal-progress-disclaimer">{copy.results.personalProgressDisclaimer}</p>
      </div>
    </div>
  );
}

function interpolate(template: string, values: Record<string, string>): string {
  return Object.entries(values).reduce(
    (text, [key, value]) => text.replace(`{${key}}`, value),
    template,
  );
}
