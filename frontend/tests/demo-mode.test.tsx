import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CatalogPresentationProvider } from "@/components/catalog-mode-context";
import { DemoNotice } from "@/components/demo-notice";
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

  it("shows the data-derived bilingual warning only for synthetic demo mode", () => {
    const { rerender } = render(<DemoNotice metadata={demoMetadata} locale="ar" />);

    expect(screen.getByTestId("portfolio-demo-notice")).toHaveTextContent("نسخة عرض تجريبية");
    expect(screen.getByTestId("portfolio-demo-notice")).toHaveTextContent(
      "نسخة تجريبية ببيانات نموذجية.",
    );

    rerender(<DemoNotice metadata={demoMetadata} locale="en" />);
    expect(screen.getByTestId("portfolio-demo-notice")).toHaveTextContent("Portfolio demo");
    expect(screen.getByTestId("portfolio-demo-notice")).toHaveTextContent(
      "Portfolio demo using sample data.",
    );
  });

  it("never labels a synthetic link as an official source", () => {
    render(
      <CatalogPresentationProvider metadata={demoMetadata} locale="en">
        <OfficialLink
          url="https://example.invalid/portfolio-demo"
          label="Official source"
          opensNewWindow="opens in a new window"
          unavailableLabel="Unavailable"
        />
      </CatalogPresentationProvider>,
    );

    const link = screen.getByRole("link", { name: /About this non-government demo link/ });
    expect(link).toHaveAttribute("href", "/en/about#methodology");
    expect(link).not.toHaveAttribute("target");
    expect(link).toHaveAttribute("data-source-classification", "synthetic-demo");
    expect(screen.queryByText("Official source")).not.toBeInTheDocument();
  });
});
