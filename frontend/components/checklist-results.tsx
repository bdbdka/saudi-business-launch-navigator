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
          <h2 id="results-title" ref={titleRef} tabIndex={-1}>{copy.results.title}</h2>
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

      <section className="result-group" aria-labelledby="required-title">
        <div className="bucket-heading">
          <h3 id="required-title">{copy.results.required}</h3>
          <p>
            {isDemo
              ? policy.text.applicableGroupExplanation
              : copy.results.requiredBody}
          </p>
        </div>
        {result.applies.length === 0 ? (
          <p className="empty-state compact">
            {isDemo ? policy.text.noApplicableItems : copy.results.noRequired}
          </p>
        ) : (
          <div className="requirement-list">
            {result.applies.map((item) => (
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
          <h3 id="missing-title">{copy.results.missing}</h3>
          {result.needs_information.length > 0 && (
            <p>
              {isDemo
                ? policy.text.missingGroupExplanation
                : copy.results.missingBody}
            </p>
          )}
        </div>
        {result.needs_information.length === 0 ? (
          <p className="empty-state compact">
            {isDemo ? policy.text.noMissingInformation : copy.results.noMissing}
          </p>
        ) : (
          <div className="requirement-list">
            {result.needs_information.map((item) => (
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
          <h3 id="verification-title">{copy.results.verify}</h3>
          <p>
            {isDemo
              ? policy.text.verificationGroupExplanation
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

      {result.does_not_apply.length > 0 && (
        <details className="not-applicable-group">
          <summary>
            {isDemo ? policy.text.notApplicableItemsTitle : copy.results.notRequired} ({formatNumber(result.does_not_apply.length, locale)})
          </summary>
          <div className="requirement-list secondary-list">
            {result.does_not_apply.map((item) => (
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
