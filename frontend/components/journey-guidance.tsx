"use client";

import { useCatalogPresentation } from "@/components/catalog-mode-context";
import { OfficialLink } from "@/components/official-link";
import type { ChecklistResult, JourneyGuidance, QuestionFactCode } from "@/lib/api/types";
import type { Dictionary, Locale } from "@/lib/i18n";
import {
  demoReviewTopicOrder,
  missingNavigationProductGuidance,
  resultProductCopy,
  reviewTopicProductGuidance,
} from "@/lib/product-guidance";

export type MissingNavigation = ChecklistResult["missing_navigation_information"][number];

export function visibleJourneyGuidance(
  guidance: JourneyGuidance[],
  missingNavigation: MissingNavigation[],
): JourneyGuidance[] {
  const missingTopicCodes = new Set(missingNavigation.flatMap((item) => item.affected_topic_codes));
  return [...guidance]
    .filter((item) => !(item.destinations.length === 0 && missingTopicCodes.has(item.topic_code)))
    .sort(
      (left, right) => demoReviewTopicOrder(left.topic_code) - demoReviewTopicOrder(right.topic_code),
    );
}

export function JourneyGuidanceList({
  guidance,
  missingNavigation,
  locale,
  copy,
  onAnswerMissing,
}: {
  guidance: JourneyGuidance[];
  missingNavigation: MissingNavigation[];
  locale: Locale;
  copy: Dictionary;
  onAnswerMissing: (factCode: QuestionFactCode) => void;
}) {
  const { policy } = useCatalogPresentation();
  const productCopy = resultProductCopy(locale);
  const visibleGuidance = visibleJourneyGuidance(guidance, missingNavigation);

  if (missingNavigation.length === 0 && visibleGuidance.length === 0) {
    return (
      <p className="empty-state compact">
        {policy.isPortfolioDemo ? productCopy.noReviewItems : copy.results.noVerification}
      </p>
    );
  }

  return (
    <div className="verification-list">
      {missingNavigation.map((item) => (
        <MissingNavigationItem
          key={item.fact_code}
          item={item}
          locale={locale}
          copy={copy}
          onAnswerMissing={onAnswerMissing}
        />
      ))}
      {visibleGuidance.map((item) => (
        <JourneyItem key={item.topic_version_id} item={item} locale={locale} copy={copy} />
      ))}
    </div>
  );
}

function MissingNavigationItem({
  item,
  locale,
  copy,
  onAnswerMissing,
}: {
  item: MissingNavigation;
  locale: Locale;
  copy: Dictionary;
  onAnswerMissing: (factCode: QuestionFactCode) => void;
}) {
  const { policy } = useCatalogPresentation();
  const text = policy.isPortfolioDemo
    ? missingNavigationProductGuidance(item.fact_code, locale)
      ?? copy.navigationMissing[item.fact_code]
    : copy.navigationMissing[item.fact_code];
  const productCopy = resultProductCopy(locale);
  return (
    <article className="verification-item navigation-missing">
      <h4>{text.title}</h4>
      <p>{text.body}</p>
      <button className="text-button" type="button" onClick={() => onAnswerMissing(item.fact_code)}>
        {policy.isPortfolioDemo ? productCopy.answerNow : copy.results.answerNow}
      </button>
    </article>
  );
}

function JourneyItem({
  item,
  locale,
  copy,
}: {
  item: JourneyGuidance;
  locale: Locale;
  copy: Dictionary;
}) {
  const { policy } = useCatalogPresentation();
  const isDemo = policy.isPortfolioDemo;
  const productCopy = resultProductCopy(locale);
  const productGuidance = isDemo ? reviewTopicProductGuidance(item.topic_code, locale) : null;
  const labels = copy.journeyLabels as Record<string, string>;
  const title = productGuidance?.title ?? labels[item.topic_code]
    ?? (locale === "ar" ? item.title_ar : item.title_en ?? item.title_ar);
  const confirmation = item.coverage_state === "REQUIRES_OFFICIAL_CONFIRMATION";
  const summary = confirmation
    ? null
    : localized(item.verified_summary_ar, item.verified_summary_en, locale);
  const limitation = isDemo
    ? null
    : localized(item.limitation_summary_ar, item.limitation_summary_en, locale);
  const whatToVerify = isDemo
    ? null
    : localized(item.what_to_verify_ar, item.what_to_verify_en, locale);

  if (isDemo) {
    return (
      <article className="verification-item" data-presentation="synthetic-demo">
        <h4>{title}</h4>
        {productGuidance ? (
          <>
            <div className="card-copy-section">
              <span className="card-copy-label">{productCopy.meaningLabel}</span>
              <p>{productGuidance.meaning}</p>
            </div>
            <div className="card-copy-section">
              <span className="card-copy-label">{productCopy.importanceLabel}</span>
              <p>{productGuidance.importance}</p>
            </div>
            <div className="card-copy-section verification-action">
              <span className="card-copy-label">{productCopy.reviewLabel}</span>
              <p>{productGuidance.review}</p>
            </div>
          </>
        ) : (
          <p>{productCopy.reviewFallback}</p>
        )}
      </article>
    );
  }

  return (
    <article className="verification-item">
      <h4>{title}</h4>
      {summary && <p>{summary}</p>}
      {limitation && <p className="guidance-limitation">{limitation}</p>}
      {whatToVerify && <p className="verification-action">{whatToVerify}</p>}
      {item.destinations.map((destination) => {
        const guidance = localized(destination.guidance_ar, destination.guidance_en, locale);
        const destinationCheck = localized(
              destination.what_to_verify_ar,
              destination.what_to_verify_en,
              locale,
            );
        const authority = localized(
              destination.source.authority.name_ar,
              destination.source.authority.name_en,
              locale,
            );
        return (
          <div className="journey-destination" key={destination.code}>
            {guidance && <p>{guidance}</p>}
            {destinationCheck && destinationCheck !== whatToVerify && <p>{destinationCheck}</p>}
            {authority && (
              <p className="authority-line">
                <strong>{copy.results.authority}:</strong>{" "}
                {authority}
              </p>
            )}
            <OfficialLink
              url={destination.source.official_url}
              label={copy.results.openOfficialGuidance}
              opensNewWindow={copy.results.opensNewWindow}
              unavailableLabel={copy.results.sourceUnavailable}
            />
          </div>
        );
      })}
    </article>
  );
}

function localized(arabic: string | null, english: string | null, locale: Locale): string | null {
  return locale === "ar" ? arabic ?? english : english ?? arabic;
}
