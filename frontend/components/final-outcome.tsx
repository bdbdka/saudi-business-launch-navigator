"use client";

import { useIsPortfolioDemo } from "@/components/catalog-mode-context";
import { visibleJourneyGuidance, type MissingNavigation } from "@/components/journey-guidance";
import { OfficialLink } from "@/components/official-link";
import type { ChecklistResult, JourneyGuidance } from "@/lib/api/types";
import { formatNumber, type Dictionary, type Locale } from "@/lib/i18n";

export function FinalOutcome({
  result,
  completedCount,
  locale,
  copy,
  onEdit,
  onAnswerMissing,
}: {
  result: ChecklistResult;
  completedCount: number;
  locale: Locale;
  copy: Dictionary;
  onEdit: () => void;
  onAnswerMissing: (factCode: MissingNavigation["fact_code"]) => void;
}) {
  const isDemo = useIsPortfolioDemo();
  const totalApplicable = result.applies.length;
  const remaining = Math.max(0, totalApplicable - completedCount);
  const allApplicableMarked = totalApplicable > 0 && completedCount === totalApplicable;
  const unresolvedRegulatoryInformation = result.needs_information.length > 0;
  const missingOnlyState = totalApplicable === 0 && unresolvedRegulatoryInformation;
  const noApplicableState = totalApplicable === 0 && !unresolvedRegulatoryInformation;
  const requestedAnswerCount = result.questions_needed.length > 0
    ? result.questions_needed.length
    : new Set(result.needs_information.flatMap((item) => item.missing_fact_codes)).size;
  const guidance = visibleJourneyGuidance(
    result.journey_guidance,
    result.missing_navigation_information,
  );
  const verificationCount = guidance.length + result.missing_navigation_information.length;
  const values = {
    completed: formatNumber(completedCount, locale),
    total: formatNumber(totalApplicable, locale),
    remaining: formatNumber(remaining, locale),
    count: formatNumber(requestedAnswerCount, locale),
  };

  return (
    <section className="final-outcome" aria-labelledby="final-outcome-title">
      <p className="stage-label">{copy.results.finalOutcomeLabel}</p>

      {!allApplicableMarked && !missingOnlyState && !noApplicableState && (
        <div className="final-outcome-state">
          <h3 id="final-outcome-title">{copy.results.finalInProgressTitle}</h3>
          <p>{interpolate(copy.results.finalInProgressCompletedTemplate, values)}</p>
          <p>{interpolate(copy.results.finalInProgressRemainingTemplate, values)}</p>
        </div>
      )}

      {noApplicableState && (
        <div className="final-outcome-state">
          <h3 id="final-outcome-title">{copy.results.finalNoApplicableTitle}</h3>
          <p>{copy.results.finalNoApplicableBody}</p>
        </div>
      )}

      {(allApplicableMarked || missingOnlyState) && unresolvedRegulatoryInformation && (
        <div className="final-outcome-state unresolved">
          <h3 id="final-outcome-title">{copy.results.finalMissingInformationTitle}</h3>
          <p>{interpolate(copy.results.finalMissingInformationTemplate, values)}</p>
          <button className="button secondary small" type="button" onClick={onEdit}>
            {copy.results.edit}
          </button>
        </div>
      )}

      {allApplicableMarked && !unresolvedRegulatoryInformation && (
        <>
          <div className="final-outcome-state complete">
            <h3 id="final-outcome-title">{copy.results.finalFollowUpCompleteTitle}</h3>
            <p>
              {isDemo
                ? (locale === "ar"
                    ? "وضعت علامة إنجاز على جميع مهام العرض النموذجية في هذه التجربة التقنية."
                    : "You marked all sample portfolio-demo tasks as complete in this technical demonstration.")
                : copy.results.finalFollowUpCompleteBody}
            </p>
          </div>

          {verificationCount > 0 ? (
            <div className="final-verification-summary">
              <h4>{copy.results.finalVerificationTitle}</h4>
              <ol className="final-verification-list">
                {result.missing_navigation_information.map((item) => (
                  <MissingNavigationSummary
                    key={item.fact_code}
                    item={item}
                    copy={copy}
                    onAnswerMissing={onAnswerMissing}
                  />
                ))}
                {guidance.map((item) => (
                  <OfficialVerificationSummary
                    key={item.topic_version_id}
                    item={item}
                    locale={locale}
                    copy={copy}
                  />
                ))}
              </ol>
              <a className="final-verification-anchor" href="#verification-title">
                {copy.results.reviewFullVerification}
              </a>
            </div>
          ) : (
            <div className="final-no-verification">
              <h4>{copy.results.finalNoVerificationTitle}</h4>
              <p>
                {isDemo
                  ? (locale === "ar"
                      ? "لا توجد وجهة نموذجية إضافية في هذه التجربة."
                      : "No additional sample destination remains in this demonstration.")
                  : copy.results.finalNoVerificationBody}
              </p>
            </div>
          )}
        </>
      )}

      <div className="final-outcome-boundary">
        <p>
          {isDemo
            ? (locale === "ar"
                ? "تعرض هذه النتيجة بيانات نموذجية لإثبات عمل القواعد والواجهة فقط."
                : "This result uses sample data only to demonstrate the rules engine and interface.")
            : copy.results.finalScope}
        </p>
        <p>
          {isDemo
            ? (locale === "ar"
                ? "لا تمثل هذه المهام متطلبات سعودية منشورة أو معتمدة."
                : "These tasks are not published or approved Saudi regulatory requirements.")
            : copy.results.finalScopeCaution}
        </p>
        <strong>
          {isDemo
            ? (locale === "ar"
                ? "لا تستخدم هذه النتيجة لاتخاذ قرار تنظيمي فعلي."
                : "Do not use this result for a real regulatory decision.")
            : copy.results.finalSafety}
        </strong>
      </div>
    </section>
  );
}

function OfficialVerificationSummary({
  item,
  locale,
  copy,
}: {
  item: JourneyGuidance;
  locale: Locale;
  copy: Dictionary;
}) {
  const isDemo = useIsPortfolioDemo();
  const labels = copy.journeyLabels as Record<string, string>;
  const title = labels[item.topic_code]
    ?? localized(item.title_ar, item.title_en, locale)
    ?? item.topic_code;
  const destination = item.destinations.find((candidate) => candidate.is_primary)
    ?? item.destinations[0];
  const whatToVerify = localized(item.what_to_verify_ar, item.what_to_verify_en, locale)
    ?? (destination
      ? localized(destination.what_to_verify_ar, destination.what_to_verify_en, locale)
      : null)
    ?? localized(item.limitation_summary_ar, item.limitation_summary_en, locale);
  const authority = destination
    ? localized(destination.source.authority.name_ar, destination.source.authority.name_en, locale)
    : null;

  return (
    <li className="final-verification-item">
      <h5>{title}</h5>
      {whatToVerify && <p>{whatToVerify}</p>}
      {authority && (
        <p className="final-verification-authority">
          <strong>
            {isDemo
              ? (locale === "ar" ? "جهة نموذجية" : "Sample provider")
              : copy.results.authority}:
          </strong>{" "}
          {authority}
        </p>
      )}
      {destination ? (
        <OfficialLink
          url={destination.source.official_url}
          label={copy.results.openOfficialGuidance}
          opensNewWindow={copy.results.opensNewWindow}
          unavailableLabel={copy.results.sourceUnavailable}
        />
      ) : (
        <p className="source-unavailable">{copy.results.finalDestinationUnavailable}</p>
      )}
    </li>
  );
}

function MissingNavigationSummary({
  item,
  copy,
  onAnswerMissing,
}: {
  item: MissingNavigation;
  copy: Dictionary;
  onAnswerMissing: (factCode: MissingNavigation["fact_code"]) => void;
}) {
  const text = copy.navigationMissing[item.fact_code];
  return (
    <li className="final-verification-item navigation-needed">
      <h5>{text.title}</h5>
      <p>{text.body}</p>
      <button className="button secondary small" type="button" onClick={() => onAnswerMissing(item.fact_code)}>
        {copy.results.answerNow}
      </button>
    </li>
  );
}

function localized(
  arabic: string | null,
  english: string | null,
  locale: Locale,
): string | null {
  return locale === "ar" ? arabic ?? english : english ?? arabic;
}

function interpolate(template: string, values: Record<string, string>): string {
  return Object.entries(values).reduce(
    (text, [key, value]) => text.replace(`{${key}}`, value),
    template,
  );
}
