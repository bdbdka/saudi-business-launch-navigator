import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ActivityOfficialReference } from "@/components/activity-official-reference";
import { CatalogPresentationProvider } from "@/components/catalog-mode-context";
import {
  BALADY_ACTIVITY_HOSTNAME,
  officialActivityReference,
  officialActivityReferences,
  safeActivityReferenceUrl,
} from "@/lib/activity-references";
import type { ActivityCode, CatalogBoundary } from "@/lib/api/types";
import { getDictionary } from "@/lib/i18n";

const demoMetadata: CatalogBoundary = {
  catalog_mode: "PORTFOLIO_DEMO_CATALOG",
  publication_state: "SAMPLE_ONLY",
  data_classification: "SYNTHETIC_PORTFOLIO_DEMO",
  public_catalog_approved: false,
  warning_ar: "نسخة تجريبية ببيانات نموذجية.",
  warning_en: "Portfolio demo using sample data.",
};

const expectedReferences = {
  coffee_shop: {
    activityId: "1770",
    titleAr: "محلات تقديم المشروبات الكوفي شوب",
    officialUrl:
      "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=1770",
  },
  restaurant: {
    activityId: "1319",
    titleAr: "المطاعم مع الخدمة",
    officialUrl:
      "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=1319",
  },
  cloud_kitchen: {
    activityId: "859397",
    titleAr: "المطاعم السحابية لأنشطة تقديم الوجبات فقط تناول الوجبة خارج المحل Take Out",
    officialUrl:
      "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=859397",
  },
} as const satisfies Record<
  ActivityCode,
  { activityId: string; titleAr: string; officialUrl: string }
>;

describe("official activity references", () => {
  it("maps each supported activity to its exact verified Balady page", () => {
    expect(Object.keys(officialActivityReferences).sort()).toEqual(
      ["cloud_kitchen", "coffee_shop", "restaurant"],
    );

    for (const activityCode of Object.keys(expectedReferences) as ActivityCode[]) {
      const expected = expectedReferences[activityCode];
      const reference = officialActivityReference(activityCode);
      expect(reference).not.toBeNull();
      if (!reference) throw new Error(`missing activity reference for ${activityCode}`);
      const url = new URL(reference.officialUrl);

      expect(reference.activityCode).toBe(activityCode);
      expect(reference.activityId).toBe(expected.activityId);
      expect(reference.titleAr).toBe(expected.titleAr);
      expect(reference.officialUrl).toBe(expected.officialUrl);
      expect(safeActivityReferenceUrl(reference)).toBe(expected.officialUrl);
      expect(url.protocol).toBe("https:");
      expect(url.hostname).toBe(BALADY_ACTIVITY_HOSTNAME);
      expect(url.pathname).toBe("/commercial/inquiry/ActivitiesInquiry/GetDetails");
      expect(url.searchParams.get("type")).toBe("detailed");
      expect(url.searchParams.get("activityId")).toBe(expected.activityId);
      expect(url.username).toBe("");
      expect(url.password).toBe("");
      expect(url.href).not.toContain(".invalid");
    }

    expect(new Set(
      Object.values(officialActivityReferences).map((reference) => reference.officialUrl),
    ).size).toBe(3);
  });

  it("rejects a changed host, scheme, path, query, or activity identity", () => {
    expect(officialActivityReference("unsupported" as ActivityCode)).toBeNull();
    const reference = officialActivityReference("coffee_shop");
    expect(reference).not.toBeNull();
    if (!reference) throw new Error("missing coffee-shop activity reference");
    for (const officialUrl of [
      reference.officialUrl.replace("https:", "http:"),
      reference.officialUrl.replace(BALADY_ACTIVITY_HOSTNAME, "example.invalid"),
      reference.officialUrl.replace("ActivitiesInquiry/GetDetails", "ActivitiesInquiry/Other"),
      reference.officialUrl.replace("type=detailed", "type=summary"),
      reference.officialUrl.replace("activityId=1770", "activityId=1319"),
      `${reference.officialUrl}&extra=true`,
    ]) {
      expect(safeActivityReferenceUrl({ ...reference, officialUrl })).toBeNull();
    }
  });

  it("renders the exact Arabic reference copy and safe coffee-shop destination", () => {
    render(
      <CatalogPresentationProvider metadata={demoMetadata} locale="ar">
        <ActivityOfficialReference
          activityCode="coffee_shop"
          locale="ar"
          copy={getDictionary("ar")}
        />
      </CatalogPresentationProvider>,
    );

    const reference = screen.getByTestId("activity-official-reference");
    expect(within(reference).getByRole("heading", { name: "المصدر الرسمي للنشاط" })).toBeInTheDocument();
    expect(reference).toHaveTextContent("محلات تقديم المشروبات الكوفي شوب");
    expect(reference).toHaveTextContent(
      "يمكنك مراجعة صفحة النشاط الرسمية في منصة بلدي للاطلاع على وصف النشاط وتفاصيله المنشورة.",
    );
    expect(reference).toHaveTextContent("وزارة البلديات والإسكان — منصة بلدي");
    const external = within(reference).getByRole("link", { name: /فتح صفحة النشاط الرسمية/ });
    expect(external).toHaveAttribute("href", expectedReferences.coffee_shop.officialUrl);
    expect(external).toHaveAttribute("target", "_blank");
    expect(external).toHaveAttribute("rel", "noopener noreferrer");
    expect(external).toHaveAttribute("data-source-classification", "official-activity-reference");
    expect(within(reference).getByRole("link", { name: "عن بيانات النسخة التجريبية" })).toHaveAttribute(
      "href",
      "/ar/about#methodology",
    );
  });

  it("renders the exact English reference copy and selected cloud-kitchen destination", () => {
    render(
      <CatalogPresentationProvider metadata={demoMetadata} locale="en">
        <ActivityOfficialReference
          activityCode="cloud_kitchen"
          locale="en"
          copy={getDictionary("en")}
        />
      </CatalogPresentationProvider>,
    );

    const reference = screen.getByTestId("activity-official-reference");
    expect(within(reference).getByRole("heading", { name: "Official activity reference" })).toBeInTheDocument();
    expect(reference).toHaveTextContent("Cloud kitchen for take-out meal preparation");
    expect(reference).toHaveTextContent(
      "You can review the official Balady activity page for its published activity description and details.",
    );
    expect(reference).toHaveTextContent("Ministry of Municipalities and Housing — Balady");
    expect(within(reference).getByRole("link", { name: /Open official activity page/ })).toHaveAttribute(
      "href",
      expectedReferences.cloud_kitchen.officialUrl,
    );
  });
});
