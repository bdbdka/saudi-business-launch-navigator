"use client";

import { createContext, useContext } from "react";

import type { CatalogBoundary } from "@/lib/api/types";
import { configuredCatalogMode } from "@/lib/catalog-presentation";
import type { Locale } from "@/lib/i18n";

const CatalogPresentationContext = createContext<{
  metadata: CatalogBoundary | null;
  locale: Locale;
}>({ metadata: null, locale: "ar" });

export function CatalogPresentationProvider({
  metadata,
  locale,
  children,
}: {
  metadata: CatalogBoundary | null;
  locale: Locale;
  children: React.ReactNode;
}) {
  return (
    <CatalogPresentationContext.Provider value={{ metadata, locale }}>
      {children}
    </CatalogPresentationContext.Provider>
  );
}

export function useCatalogPresentation() {
  return useContext(CatalogPresentationContext);
}

export function useIsPortfolioDemo(): boolean {
  const { metadata } = useCatalogPresentation();
  return (
    metadata?.catalog_mode === "PORTFOLIO_DEMO_CATALOG"
    || (metadata === null && configuredCatalogMode() === "PORTFOLIO_DEMO_CATALOG")
  );
}
