import type { CatalogBoundary } from "@/lib/api/types";

export type PublicCatalogMode = CatalogBoundary["catalog_mode"];

export function configuredCatalogMode(): PublicCatalogMode | null {
  const value = process.env.NEXT_PUBLIC_CATALOG_MODE;
  if (value === "GOVERNED_REAL_CATALOG" || value === "PORTFOLIO_DEMO_CATALOG") {
    return value;
  }
  return null;
}

export function catalogBoundaryMatchesBuild(metadata: CatalogBoundary): boolean {
  const expected = configuredCatalogMode();
  return expected !== null && metadata.catalog_mode === expected;
}
