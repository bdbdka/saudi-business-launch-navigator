"use client";

import { useCatalogPresentation } from "@/components/catalog-mode-context";
import type { ChecklistResult } from "@/lib/api/types";
import type { Dictionary, Locale } from "@/lib/i18n";

export function CoverageNotice({ result, locale, copy }: { result: ChecklistResult; locale: Locale; copy: Dictionary }) {
  const { policy } = useCatalogPresentation();
  const isDemo = policy.isPortfolioDemo;
  const labels = copy.unresolvedLabels as Record<string, string>;
  return (
    <aside className="coverage-notice" id="coverage">
      <details>
        <summary>
          {isDemo
            ? policy.text.coverageCompact
            : copy.coverage.compact}
        </summary>
        <p>
          {isDemo
            ? policy.text.coverageExplanation
            : copy.coverage.body}
        </p>
        {!isDemo && (
          <>
            <p className="coverage-source-note">
              {locale === "ar" ? result.coverage_notice.message_ar : result.coverage_notice.message_en}
            </p>
            <strong>{copy.coverage.unresolved}</strong>
            <ul>
              {result.coverage_notice.unresolved_topics.map((topic) => (
                <li key={topic}>{labels[topic] ?? copy.coverage.unknownTopic}</li>
              ))}
            </ul>
          </>
        )}
      </details>
    </aside>
  );
}
