import { render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CatalogPresentationProvider } from "@/components/catalog-mode-context";
import { ChecklistResults } from "@/components/checklist-results";
import { OfficialLink } from "@/components/official-link";
import type { CatalogBoundary } from "@/lib/api/types";
import {
  catalogBoundaryMatchesBuild,
  catalogPresentationPolicy,
  presentSourceLink,
} from "@/lib/catalog-presentation";
import { getDictionary } from "@/lib/i18n";
import { activities, checklistResponse } from "@/tests/fixtures";

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
    const governedMetadata: CatalogBoundary = {
      catalog_mode: "GOVERNED_REAL_CATALOG",
      publication_state: "UNPUBLISHED",
      data_classification: "PRIVATE_GOVERNED_UNPUBLISHED",
      public_catalog_approved: false,
      warning_ar: "بيانات محكومة غير منشورة.",
      warning_en: "Governed unpublished data.",
    };
    expect(catalogBoundaryMatchesBuild(governedMetadata)).toBe(true);
    expect(catalogBoundaryMatchesBuild({
      ...governedMetadata,
      publication_state: "SAMPLE_ONLY",
      data_classification: "SYNTHETIC_PORTFOLIO_DEMO",
    })).toBe(false);

    vi.stubEnv("NEXT_PUBLIC_CATALOG_MODE", "PORTFOLIO_DEMO_CATALOG");
    expect(catalogBoundaryMatchesBuild(demoMetadata)).toBe(true);
    expect(catalogBoundaryMatchesBuild({
      ...demoMetadata,
      public_catalog_approved: true,
    } as unknown as CatalogBoundary)).toBe(false);
    expect(catalogBoundaryMatchesBuild({
      ...demoMetadata,
      publication_state: "UNPUBLISHED",
    })).toBe(false);
    expect(catalogBoundaryMatchesBuild({
      ...demoMetadata,
      data_classification: "PRIVATE_GOVERNED_UNPUBLISHED",
    })).toBe(false);
  });

  it("does not present governed evidence when catalog mode is missing", () => {
    const policy = catalogPresentationPolicy(null, "en");
    expect(policy.isPortfolioDemo).toBe(false);
    expect(policy.isGovernedCatalog).toBe(false);
    expect(policy.showAuthorityRows).toBe(false);
    expect(policy.showSourceMetadata).toBe(false);
    expect(presentSourceLink("https://www.example.gov.sa/service", null)).toEqual({
      kind: "unavailable",
    });
  });

  it("suppresses synthetic source destinations instead of turning them into evidence links", () => {
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

    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
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
    expect(screen.getByText("غير متاح")).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(document.querySelector('a[href*=".invalid"]')).not.toBeInTheDocument();

    rerender(
      <CatalogPresentationProvider metadata={demoMetadata} locale="en">
        <OfficialLink
          url="https://www.example.gov.sa/service"
          label="Official source"
          opensNewWindow="opens in a new window"
          unavailableLabel="Unavailable"
        />
      </CatalogPresentationProvider>,
    );
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.queryByText("Official source")).not.toBeInTheDocument();
  });

  it("fails closed for malformed and credential-bearing demo destinations", () => {
    const { rerender } = render(
      <CatalogPresentationProvider metadata={demoMetadata} locale="en">
        <OfficialLink
          url="javascript:alert(1)"
          label="Official source"
          opensNewWindow="opens in a new window"
          unavailableLabel="Unavailable"
        />
      </CatalogPresentationProvider>,
    );
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();

    rerender(
      <CatalogPresentationProvider metadata={demoMetadata} locale="en">
        <OfficialLink
          url="https://example.invalid@www.example.gov.sa/service"
          label="Official source"
          opensNewWindow="opens in a new window"
          unavailableLabel="Unavailable"
        />
      </CatalogPresentationProvider>,
    );
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
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

  it("uses sample-item language for an Arabic missing-information result", () => {
    const response = checklistResponse(
      activities[0],
      { applies: 0, doesNotApply: 1, needs: 1 },
    );
    render(
      <CatalogPresentationProvider metadata={demoMetadata} locale="ar">
        <ChecklistResults
          result={response.result}
          locale="ar"
          copy={getDictionary("ar")}
          aiExplanation={[]}
          onAnswerMissing={vi.fn()}
          onEdit={vi.fn()}
          onRestart={vi.fn()}
        />
      </CatalogPresentationProvider>,
    );

    expect(screen.getByRole("region", {
      name: "أكملت متابعة العناصر الحالية، لكن قائمة العرض لم تُحدد بالكامل بعد",
    })).toBeInTheDocument();
    expect(screen.getByText(/عناصر نموذجية لا تنطبق على إجاباتك/)).toBeInTheDocument();
    expect(screen.getByText("لا توجد عناصر نموذجية منطبقة في هذا السيناريو.")).toBeInTheDocument();
    expect(screen.queryByText(/المتطلبات الحالية/)).not.toBeInTheDocument();
  });

  it("uses sample-item language for an English no-applicable result", () => {
    const response = checklistResponse(
      activities[0],
      { applies: 0, doesNotApply: 1, needs: 0 },
    );
    response.result.journey_guidance = [];
    response.result.missing_navigation_information = [];
    render(
      <CatalogPresentationProvider metadata={demoMetadata} locale="en">
        <ChecklistResults
          result={response.result}
          locale="en"
          copy={getDictionary("en")}
          aiExplanation={[]}
          onAnswerMissing={vi.fn()}
          onEdit={vi.fn()}
          onRestart={vi.fn()}
        />
      </CatalogPresentationProvider>,
    );

    expect(screen.getByRole("region", {
      name: "The sample rules identified no applicable item",
    })).toBeInTheDocument();
    expect(screen.getByText("The sample rules need no more information right now.")).toBeInTheDocument();
    expect(screen.getByText("There are no additional examples to verify right now.")).toBeInTheDocument();
    expect(screen.getByText(/Sample items that do not apply to your answers/)).toBeInTheDocument();
    expect(screen.queryByText(/applicable requirements/i)).not.toBeInTheDocument();
  });

  it("uses sample-item language for an unconditional demo detail", () => {
    const response = checklistResponse(
      activities[0],
      { applies: 1, doesNotApply: 0, needs: 0 },
    );
    const tracedResponse = checklistResponse(
      activities[0],
      { applies: 7, doesNotApply: 0, needs: 0 },
    );
    const tracedItem = tracedResponse.result.applies.find(
      (item) => item.evaluated_facts.length > 0,
    );
    expect(tracedItem).toBeDefined();
    response.result.applies[0].evaluated_facts = tracedItem!.evaluated_facts;
    render(
      <CatalogPresentationProvider metadata={demoMetadata} locale="en">
        <ChecklistResults
          result={response.result}
          locale="en"
          copy={getDictionary("en")}
          aiExplanation={[]}
          onAnswerMissing={vi.fn()}
          onEdit={vi.fn()}
          onRestart={vi.fn()}
        />
      </CatalogPresentationProvider>,
    );

    expect(
      screen.getByText("This sample item needs no additional question in this path."),
    ).toBeInTheDocument();
    expect(screen.queryByText(/This requirement is unconditional/i)).not.toBeInTheDocument();
  });

  it("shows one activity reference and one methodology link without card-level destinations", () => {
    const response = checklistResponse(
      activities[2],
      { applies: 2, doesNotApply: 1, needs: 1 },
    );
    render(
      <CatalogPresentationProvider metadata={demoMetadata} locale="en">
        <ChecklistResults
          result={response.result}
          locale="en"
          copy={getDictionary("en")}
          aiExplanation={[]}
          onAnswerMissing={vi.fn()}
          onEdit={vi.fn()}
          onRestart={vi.fn()}
        />
      </CatalogPresentationProvider>,
    );

    const reference = screen.getByTestId("activity-official-reference");
    expect(within(reference).getByRole("link", { name: /Open official activity page/ })).toHaveAttribute(
      "href",
      "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=1319",
    );
    expect(screen.getAllByRole("link", { name: "About the demo data" })).toHaveLength(1);
    expect(screen.getByRole("link", { name: "About the demo data" })).toHaveAttribute(
      "href",
      "/en/about#methodology",
    );
    expect(document.querySelectorAll('.requirement-item a[href]')).toHaveLength(0);
    expect(document.querySelectorAll('.actionability-details a[href]')).toHaveLength(0);
    expect(document.querySelectorAll('.verification-list a[href]')).toHaveLength(0);
    expect(document.querySelectorAll('.final-outcome a[href]')).toHaveLength(0);
    expect(document.querySelectorAll('a[href*=".invalid"]')).toHaveLength(0);
    expect(document.querySelectorAll('a[href*="official.example.gov.sa"]')).toHaveLength(0);
  });
});
