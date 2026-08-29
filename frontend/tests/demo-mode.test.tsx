import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CatalogPresentationProvider } from "@/components/catalog-mode-context";
import { OfficialLink } from "@/components/official-link";
import type { CatalogBoundary } from "@/lib/api/types";
import { catalogBoundaryMatchesBuild } from "@/lib/catalog-presentation";

const demoMetadata: CatalogBoundary = {
  catalog_mode: "PORTFOLIO_DEMO_CATALOG",
  publication_state: "SAMPLE_ONLY",
  data_classification: "SYNTHETIC_PORTFOLIO_DEMO",
  public_catalog_approved: false,
  warning_ar: "نسخة تجريبية ببيانات نموذجية.",
  warning_en: "Portfolio demo using sample data.",
};

describe("portfolio demo presentation boundary", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("fails closed when the browser build has no exact catalog mode", () => {
    vi.stubEnv("NEXT_PUBLIC_CATALOG_MODE", "");
    expect(catalogBoundaryMatchesBuild(demoMetadata)).toBe(false);

    vi.stubEnv("NEXT_PUBLIC_CATALOG_MODE", "GOVERNED_REAL_CATALOG");
    expect(catalogBoundaryMatchesBuild(demoMetadata)).toBe(false);

    vi.stubEnv("NEXT_PUBLIC_CATALOG_MODE", "PORTFOLIO_DEMO_CATALOG");
    expect(catalogBoundaryMatchesBuild(demoMetadata)).toBe(true);
  });

  it("routes every reserved demo hostname to the localized methodology explanation", () => {
    const { rerender } = render(
      <CatalogPresentationProvider metadata={demoMetadata} locale="en">
        <OfficialLink
          url="https://records.example.invalid/portfolio-demo"
          label="Official source"
          opensNewWindow="opens in a new window"
          unavailableLabel="Unavailable"
        />
      </CatalogPresentationProvider>,
    );

    const link = screen.getByRole("link", { name: "About the demo data" });
    expect(link).toHaveAttribute("href", "/en/about#methodology");
    expect(link).not.toHaveAttribute("target");
    expect(link).toHaveAttribute("data-source-classification", "synthetic-demo");
    expect(screen.queryByText("Official source")).not.toBeInTheDocument();
    expect(document.querySelector('a[href*=".invalid"]')).not.toBeInTheDocument();

    rerender(
      <CatalogPresentationProvider metadata={demoMetadata} locale="ar">
        <OfficialLink
          url="https://example.invalid/portfolio-demo"
          label="المصدر الرسمي"
          opensNewWindow="يفتح في نافذة جديدة"
          unavailableLabel="غير متاح"
        />
      </CatalogPresentationProvider>,
    );
    expect(screen.getByRole("link", { name: "عن بيانات النسخة التجريبية" })).toHaveAttribute(
      "href",
      "/ar/about#methodology",
    );
    expect(document.querySelector('a[href*=".invalid"]')).not.toBeInTheDocument();
  });

  it("preserves legitimate official HTTPS links outside demo mode", () => {
    const governedMetadata: CatalogBoundary = {
      catalog_mode: "GOVERNED_REAL_CATALOG",
      publication_state: "UNPUBLISHED",
      data_classification: "PRIVATE_GOVERNED_UNPUBLISHED",
      public_catalog_approved: false,
      warning_ar: "بيانات محكومة غير منشورة.",
      warning_en: "Governed unpublished data.",
    };
    render(
      <CatalogPresentationProvider metadata={governedMetadata} locale="en">
        <OfficialLink
          url="https://www.example.gov.sa/service"
          label="Official source"
          opensNewWindow="opens in a new window"
          unavailableLabel="Unavailable"
        />
      </CatalogPresentationProvider>,
    );

    const link = screen.getByRole("link", { name: /Official source/ });
    expect(link).toHaveAttribute("href", "https://www.example.gov.sa/service");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(link).toHaveAttribute("data-source-classification", "governed");
  });
});
