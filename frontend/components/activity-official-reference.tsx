"use client";

import { useCatalogPresentation } from "@/components/catalog-mode-context";
import { ExternalLinkIcon } from "@/components/icons";
import {
  officialActivityReference,
  safeActivityReferenceUrl,
} from "@/lib/activity-references";
import type { ActivityCode } from "@/lib/api/types";
import type { Dictionary, Locale } from "@/lib/i18n";

export function ActivityOfficialReference({
  activityCode,
  locale,
  copy,
}: {
  activityCode: ActivityCode;
  locale: Locale;
  copy: Dictionary;
}) {
  const { policy } = useCatalogPresentation();
  if (!policy.isPortfolioDemo) return null;

  const reference = officialActivityReference(activityCode);
  if (!reference) return null;
  const safeUrl = safeActivityReferenceUrl(reference);
  if (!safeUrl) return null;

  const title = locale === "ar" ? reference.titleAr : reference.titleEn;
  const authority = locale === "ar" ? reference.authorityAr : reference.authorityEn;
  const platform = locale === "ar" ? reference.platformAr : reference.platformEn;

  return (
    <aside
      className="activity-official-reference"
      aria-labelledby="activity-reference-title"
      data-testid="activity-official-reference"
    >
      <h3 id="activity-reference-title">{copy.results.activityReferenceTitle}</h3>
      <p className="activity-reference-name">{title}</p>
      <p>{copy.results.activityReferenceBody}</p>
      <p className="activity-reference-authority">{authority} — {platform}</p>
      <div className="activity-reference-links">
        <a
          className="activity-reference-link"
          href={safeUrl}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`${copy.results.openActivityReference} (${copy.results.opensNewWindow})`}
          data-source-classification="official-activity-reference"
        >
          {copy.results.openActivityReference}
          <ExternalLinkIcon />
        </a>
        <a className="demo-methodology-link" href={`/${locale}/about#methodology`}>
          {policy.text.demoDataLink}
        </a>
      </div>
    </aside>
  );
}
