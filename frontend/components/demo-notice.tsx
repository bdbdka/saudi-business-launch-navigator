import type { CatalogBoundary } from "@/lib/api/types";
import type { Locale } from "@/lib/i18n";
import { configuredDemoBoundary } from "@/lib/catalog-presentation";

export function DemoNotice({
  metadata,
  locale,
}: {
  metadata: CatalogBoundary | null;
  locale: Locale;
}) {
  const resolved = metadata ?? configuredDemoBoundary();
  if (resolved?.catalog_mode !== "PORTFOLIO_DEMO_CATALOG") return null;
  return (
    <aside className="portfolio-demo-notice" data-testid="portfolio-demo-notice" role="note">
      <strong>{locale === "ar" ? "نسخة عرض تجريبية" : "Portfolio demo"}</strong>
      <span>{locale === "ar" ? resolved.warning_ar : resolved.warning_en}</span>
    </aside>
  );
}
