"use client";

import { createContext, useContext } from "react";

import type { CatalogBoundary } from "@/lib/api/types";
import {
  catalogPresentationPolicy,
  configuredCatalogMode,
  type CatalogPresentationPolicy,
} from "@/lib/catalog-presentation";
import type { Locale } from "@/lib/i18n";

const CatalogPresentationContext = createContext<{
  metadata: CatalogBoundary | null;
  locale: Locale;
  policy: CatalogPresentationPolicy;
}>({
  metadata: null,
  locale: "ar",
  policy: catalogPresentationPolicy(configuredCatalogMode(), "ar"),
});

export function CatalogPresentationProvider({
  metadata,
  locale,
  children,
}: {
  metadata: CatalogBoundary | null;
  locale: Locale;
  children: React.ReactNode;
}) {
  const mode = metadata?.catalog_mode ?? configuredCatalogMode();
  return (
    <CatalogPresentationContext.Provider
      value={{ metadata, locale, policy: catalogPresentationPolicy(mode, locale) }}
    >
      {children}
    </CatalogPresentationContext.Provider>
  );
}

export function useCatalogPresentation() {
  return useContext(CatalogPresentationContext);
}

export function useIsPortfolioDemo(): boolean {
  return useCatalogPresentation().policy.isPortfolioDemo;
}
