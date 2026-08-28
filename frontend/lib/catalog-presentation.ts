import type { CatalogBoundary } from "@/lib/api/types";

export type PublicCatalogMode = CatalogBoundary["catalog_mode"];

export function configuredCatalogMode(): PublicCatalogMode | null {
  const value = process.env.NEXT_PUBLIC_CATALOG_MODE;
  if (value === "GOVERNED_REAL_CATALOG" || value === "PORTFOLIO_DEMO_CATALOG") {
    return value;
  }
  return null;
}

export function configuredDemoBoundary(): CatalogBoundary | null {
  if (configuredCatalogMode() !== "PORTFOLIO_DEMO_CATALOG") return null;
  return {
    catalog_mode: "PORTFOLIO_DEMO_CATALOG",
    publication_state: "SAMPLE_ONLY",
    data_classification: "SYNTHETIC_PORTFOLIO_DEMO",
    public_catalog_approved: false,
    warning_ar:
      "نسخة تجريبية لأغراض العرض التقني. تستخدم هذه النسخة بيانات نموذجية ولا ينبغي الاعتماد عليها لاتخاذ قرار تنظيمي فعلي.",
    warning_en:
      "Portfolio demonstration. This version uses sample data and should not be relied on for real regulatory decisions.",
  };
}

export function catalogBoundaryMatchesBuild(metadata: CatalogBoundary): boolean {
  const expected = configuredCatalogMode();
  return expected !== null && metadata.catalog_mode === expected;
}
