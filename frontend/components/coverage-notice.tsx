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
              ? "حدود التغطية · اعرف المزيد"
              : "Coverage limits · Learn more"
            : copy.coverage.compact}
        </summary>
        <p>
          {isDemo
            ? (locale === "ar"
                ? "تعرض القائمة السيناريوهات التي تغطيها النسخة الحالية فقط."
                : "The checklist covers only the scenarios represented in the current version.")
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
