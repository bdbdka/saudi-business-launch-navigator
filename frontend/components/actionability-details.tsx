"use client";

import { useCatalogPresentation } from "@/components/catalog-mode-context";
import { OfficialLink } from "@/components/official-link";
import type { ActionabilityItem } from "@/lib/api/types";
import type { Dictionary, Locale } from "@/lib/i18n";

export function ActionabilityDetails({
  items,
  locale,
  copy,
}: {
  items: ActionabilityItem[];
  locale: Locale;
  copy: Dictionary;
}) {
  const { policy } = useCatalogPresentation();
  const ordered = [...items].sort((left, right) => left.display_order - right.display_order);
  const starts = ordered.filter(
    (item) => item.detail_type === "official_start" && item.value.kind === "official_destination",
  );
  const prerequisites = textItems(ordered, "prerequisite", locale);
  const documents = textItems(ordered, "document", locale);
  const steps = textItems(ordered, "sequence", locale);
  const fees = ordered.filter((item) => item.detail_type === "fee" && item.value.kind === "money");

  if (starts.length === 0 && prerequisites.length === 0 && documents.length === 0 && fees.length === 0 && steps.length === 0) {
    return null;
  }

  if (policy.isPortfolioDemo) {
    return (
      <div className="actionability-details" data-presentation="synthetic-demo">
        <p>{policy.text.actionabilityExplanation}</p>
      </div>
    );
  }

  return (
    <div className="actionability-details">
      {starts.map((item) => (
        <OfficialLink
          key={item.actionability_version_id}
          url={item.source.official_url}
          label={copy.results.officialService}
          opensNewWindow={copy.results.opensNewWindow}
          unavailableLabel={copy.results.sourceUnavailable}
          prominent
        />
      ))}

      <TextGroup title={copy.results.beforeStart} values={prerequisites} />
      <TextGroup title={copy.results.documents} values={documents} />

      {fees.length > 0 && (
        <div className="actionability-group">
          <h5>{copy.results.fees}</h5>
          <ul>
            {fees.map((item) => (
              <li key={item.actionability_version_id}>{formatMoney(item, locale, copy)}</li>
            ))}
          </ul>
        </div>
      )}

      {steps.length > 0 && (
        <div className="actionability-group">
          <h5>{copy.results.steps}</h5>
          <ol>
            {steps.map((value) => <li key={value.id}>{value.text}</li>)}
          </ol>
        </div>
      )}
    </div>
  );
}

function TextGroup({ title, values }: { title: string; values: Array<{ id: string; text: string }> }) {
  if (values.length === 0) return null;
  return (
    <div className="actionability-group">
      <h5>{title}</h5>
      <ul>
        {values.map((value) => <li key={value.id}>{value.text}</li>)}
      </ul>
    </div>
  );
}

function textItems(
  items: ActionabilityItem[],
  detailType: string,
  locale: Locale,
): Array<{ id: string; text: string }> {
  return items
    .filter((item) => item.detail_type === detailType && item.value.kind === "text")
    .map((item) => ({
      id: item.actionability_version_id,
      text: item.value.kind === "text"
        ? (locale === "ar" ? item.value.text_ar : item.value.text_en ?? item.value.text_ar)
        : "",
    }));
}

function formatMoney(item: ActionabilityItem, locale: Locale, copy: Dictionary): string {
  if (item.value.kind !== "money") return "";
  if (item.value.amount_minor === 0) return copy.results.free;
  const amount = item.value.amount_minor / 100;
  const formatted = new Intl.NumberFormat(locale === "ar" ? "ar-SA-u-nu-arab" : "en", {
    maximumFractionDigits: 2,
  }).format(amount);
  return locale === "ar" ? `${formatted} ر.س` : `SAR ${formatted}`;
}
