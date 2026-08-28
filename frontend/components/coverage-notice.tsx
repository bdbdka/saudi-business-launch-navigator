"use client";

import { useIsPortfolioDemo } from "@/components/catalog-mode-context";
import type { ChecklistResult } from "@/lib/api/types";
import type { Dictionary, Locale } from "@/lib/i18n";

export function CoverageNotice({ result, locale, copy }: { result: ChecklistResult; locale: Locale; copy: Dictionary }) {
  const isDemo = useIsPortfolioDemo();
  const labels = copy.unresolvedLabels as Record<string, string>;
  return (
    <aside className="coverage-notice" id="coverage">
      <details>
        <summary>
          {isDemo
            ? locale === "ar"
              ? "حدود بيانات العرض النموذجية · اعرف المزيد"
              : "Sample demo coverage · Learn more"
            : copy.coverage.compact}
        </summary>
        <p>
          {isDemo
            ? (locale === "ar"
                ? "هذه التغطية نموذجية ومصممة لعرض سلوك المنتج فقط."
                : "This is sample coverage designed only to demonstrate product behavior.")
            : copy.coverage.body}
        </p>
        <p className="coverage-source-note">
          {locale === "ar" ? result.coverage_notice.message_ar : result.coverage_notice.message_en}
        </p>
        <strong>{copy.coverage.unresolved}</strong>
        <ul>
          {result.coverage_notice.unresolved_topics.map((topic) => (
            <li key={topic}>{labels[topic] ?? copy.coverage.unknownTopic}</li>
          ))}
        </ul>
      </details>
    </aside>
  );
}
