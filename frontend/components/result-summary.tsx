"use client";

import { useCatalogPresentation } from "@/components/catalog-mode-context";
import type { ChecklistResult } from "@/lib/api/types";
import { formatNumber, type Dictionary, type Locale } from "@/lib/i18n";
import { resultProductCopy } from "@/lib/product-guidance";

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
  const { policy } = useCatalogPresentation();
  const isDemo = policy.isPortfolioDemo;
  const productCopy = resultProductCopy(locale);
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
      <h3>{isDemo ? productCopy.introTitle : copy.results.introTitle}</h3>
      <p>
        {isDemo
          ? productCopy.introBody
          : copy.results.introBody}
      </p>

      {unresolved && (
        <div className="checklist-determination unresolved">
          <strong>{copy.results.checklistNeedsInformation}</strong>
          <p>{interpolate(copy.results.checklistNeedsInformationTemplate, values)}</p>
          <button className="button secondary small" type="button" onClick={onEdit}>
            {copy.results.edit}
          </button>
        </div>
      )}
      {!unresolved && !isDemo && (
        <div className="checklist-determination">
          <p>{copy.results.checklistDetermined}</p>
        </div>
      )}

      <div className="checklist-progress-summary">
        <h3>
          {isDemo ? productCopy.progressTitle : copy.results.projectChecklistTitle}
        </h3>
        <p className="applicable-total">
          {interpolate(
            isDemo ? productCopy.applicableItemsTemplate : copy.results.requirementsApplyTemplate,
            values,
          )}
        </p>
        <div className="personal-progress-counts" aria-live="polite">
          <strong>{interpolate(copy.results.progressCompletedTemplate, values)}</strong>
          <span>{interpolate(copy.results.progressRemainingTemplate, values)}</span>
        </div>
        {totalApplicable > 0 && (
          <div
            className="personal-progress-track"
            role="progressbar"
            aria-label={isDemo ? productCopy.progressBarLabel : copy.results.progressBarLabel}
            aria-valuemin={0}
            aria-valuemax={totalApplicable}
            aria-valuenow={completedCount}
            aria-valuetext={progressText}
          >
            <span style={{ width: `${progressPercent}%` }} />
          </div>
        )}
        <p className="personal-progress-disclaimer">
          {isDemo ? productCopy.progressDisclaimer : copy.results.personalProgressDisclaimer}
        </p>
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
