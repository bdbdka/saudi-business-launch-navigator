import { useEffect, useRef, useState } from "react";

import { ActivityOfficialReference } from "@/components/activity-official-reference";
import { useCatalogPresentation } from "@/components/catalog-mode-context";
import { CoverageNotice } from "@/components/coverage-notice";
import { FinalOutcome } from "@/components/final-outcome";
import { JourneyGuidanceList } from "@/components/journey-guidance";
import { RequirementCard } from "@/components/requirement-card";
import { ResultSummary } from "@/components/result-summary";
import type { ChecklistResult, QuestionFactCode } from "@/lib/api/types";
import { formatNumber, type Dictionary, type Locale } from "@/lib/i18n";
import { demoRequirementOrder, resultProductCopy } from "@/lib/product-guidance";

export function ChecklistResults({
  result,
  locale,
  copy,
  aiExplanation,
  onAnswerMissing,
  onEdit,
  onRestart,
}: {
  result: ChecklistResult;
  locale: Locale;
  copy: Dictionary;
  aiExplanation: string[];
  onAnswerMissing: (factCode: QuestionFactCode) => void;
  onEdit: () => void;
  onRestart: () => void;
}) {
  const { policy } = useCatalogPresentation();
  const isDemo = policy.isPortfolioDemo;
  const productCopy = resultProductCopy(locale);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const [completed, setCompleted] = useState<Set<string>>(new Set());

  useEffect(() => {
    titleRef.current?.focus();
  }, [result]);

  const activityName = locale === "ar" ? result.activity.name_ar : result.activity.name_en;
  const completedCount = result.applies.reduce(
    (count, item) => count + Number(completed.has(item.requirement_version_id)),
    0,
  );
  const presentItems = <Item extends { requirement_code: string }>(items: Item[]): Item[] => (
    isDemo
      ? [...items].sort(
          (left, right) => demoRequirementOrder(left.requirement_code) - demoRequirementOrder(right.requirement_code),
        )
      : items
  );
  const applies = presentItems(result.applies);
  const needsInformation = presentItems(result.needs_information);
  const doesNotApply = presentItems(result.does_not_apply);
  const setRequirementCompleted = (id: string, value: boolean) => {
    setCompleted((current) => {
      const next = new Set(current);
      if (value) next.add(id);
      else next.delete(id);
      return next;
    });
  };

  return (
    <section className="results-panel" aria-labelledby="results-title">
      <div className="results-heading">
        <div>
          <p className="stage-label">{copy.workflow.checklist}</p>
          <p className="activity-context">{activityName}</p>
          <h1 id="results-title" ref={titleRef} tabIndex={-1}>{copy.results.title}</h1>
        </div>
        <div className="results-actions">
          <button className="text-button edit-answers" type="button" onClick={onEdit}>{copy.results.edit}</button>
          <button className="text-button start-over" type="button" onClick={onRestart}>{copy.results.restart}</button>
        </div>
      </div>

      {isDemo && (
        <p className="demo-result-scope-note" data-testid="demo-result-scope-note">
          {policy.text.resultScopeNote}
        </p>
      )}
      <ResultSummary
        result={result}
        completedCount={completedCount}
        locale={locale}
        copy={copy}
        onEdit={onEdit}
      />

      <section className="result-group" aria-labelledby="required-title">
        <div className="bucket-heading">
          <h3 id="required-title">{isDemo ? productCopy.appliesTitle : copy.results.required}</h3>
          <p>
            {isDemo
              ? productCopy.appliesBody
              : copy.results.requiredBody}
          </p>
        </div>
        {applies.length === 0 ? (
          <p className="empty-state compact">
            {isDemo ? productCopy.noApplicableItems : copy.results.noRequired}
          </p>
        ) : (
          <div className="requirement-list">
            {applies.map((item) => (
              <RequirementCard
                key={item.requirement_version_id}
                item={item}
                locale={locale}
                copy={copy}
                variant="applicable"
                completed={completed.has(item.requirement_version_id)}
                onCompletionChange={(value) => setRequirementCompleted(item.requirement_version_id, value)}
                onAnswerMissing={onAnswerMissing}
              />
            ))}
          </div>
        )}
      </section>

      <section className="result-group missing-group" aria-labelledby="missing-title">
        <div className="bucket-heading">
          <h3 id="missing-title">{isDemo ? productCopy.missingTitle : copy.results.missing}</h3>
          {needsInformation.length > 0 && (
            <p>
              {isDemo
                ? productCopy.missingBody
                : copy.results.missingBody}
            </p>
          )}
        </div>
        {needsInformation.length === 0 ? (
          <p className="empty-state compact">
            {isDemo ? productCopy.noMissingInformation : copy.results.noMissing}
          </p>
        ) : (
          <div className="requirement-list">
            {needsInformation.map((item) => (
              <RequirementCard
                key={item.requirement_version_id}
                item={item}
                locale={locale}
                copy={copy}
                variant="missing"
                onAnswerMissing={onAnswerMissing}
              />
            ))}
          </div>
        )}
      </section>

      <section className="result-group verification-group" aria-labelledby="verification-title">
        <div className="bucket-heading">
          <h3 id="verification-title">{isDemo ? productCopy.reviewTitle : copy.results.verify}</h3>
          <p>
            {isDemo
              ? productCopy.reviewBody
              : copy.results.verifyBody}
          </p>
        </div>
        <JourneyGuidanceList
          guidance={result.journey_guidance}
          missingNavigation={result.missing_navigation_information}
          locale={locale}
          copy={copy}
          onAnswerMissing={onAnswerMissing}
        />
      </section>

      <ActivityOfficialReference
        activityCode={result.activity.code}
        locale={locale}
        copy={copy}
      />
      <FinalOutcome
        result={result}
        completedCount={completedCount}
        locale={locale}
        copy={copy}
        onEdit={onEdit}
        onAnswerMissing={onAnswerMissing}
      />
      <CoverageNotice result={result} locale={locale} copy={copy} />

      {doesNotApply.length > 0 && (
        <details className="not-applicable-group">
          <summary>
            {isDemo ? productCopy.notSelectedTitle : copy.results.notRequired} ({formatNumber(doesNotApply.length, locale)})
          </summary>
          <div className="requirement-list secondary-list">
            {doesNotApply.map((item) => (
              <RequirementCard
                key={item.requirement_version_id}
                item={item}
                locale={locale}
                copy={copy}
                variant="secondary"
                onAnswerMissing={onAnswerMissing}
              />
            ))}
          </div>
        </details>
      )}

      {aiExplanation.length > 0 && (
        <details className="ai-explanation">
          <summary>{copy.ai.explanation}</summary>
          {aiExplanation.map((text, index) => <p key={`${index}-${text}`}>{text}</p>)}
        </details>
      )}
    </section>
  );
}
