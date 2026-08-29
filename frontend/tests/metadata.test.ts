import { describe, expect, it, vi } from "vitest";

import { buildAboutMetadata, buildHomeMetadata } from "@/lib/metadata";

describe("localized production metadata", () => {
  it("describes the Arabic and English home routes without overclaiming coverage", () => {
    const arabic = buildHomeMetadata("ar");
    expect(arabic).toMatchObject({
      title: "دليل تأسيس المنشآت في السعودية",
      description: "اعرف المتطلبات والخطوات الرسمية لبدء مقهى أو مطعم أو مطبخ سحابي في السعودية.",
      applicationName: "دليل تأسيس المنشآت في السعودية",
      alternates: {
        canonical: "/ar",
        languages: { "ar-SA": "/ar", en: "/en" },
      },
      openGraph: {
        type: "website",
        title: "دليل تأسيس المنشآت في السعودية",
        locale: "ar_SA",
        alternateLocale: ["en_US"],
      },
      robots: { index: false, follow: false },
    });

    const english = buildHomeMetadata("en");
    expect(english).toMatchObject({
      title: "Saudi Business Launch Guide",
      description: "Understand the verified requirements and official next steps for launching a coffee shop, restaurant, or cloud kitchen in Saudi Arabia.",
      applicationName: "Saudi Business Launch Navigator",
      alternates: {
        canonical: "/en",
        languages: { "ar-SA": "/ar", en: "/en" },
      },
      openGraph: {
        type: "website",
        title: "Saudi Business Launch Guide",
        locale: "en_US",
        alternateLocale: ["ar_SA"],
      },
      robots: { index: false, follow: false },
    });
  });

  it("gives About its own bilingual metadata and route-preserving language alternates", () => {
    expect(buildAboutMetadata("ar")).toMatchObject({
      title: "حول دليل تأسيس المنشآت في السعودية",
      alternates: {
        canonical: "/ar/about",
        languages: { "ar-SA": "/ar/about", en: "/en/about" },
      },
      openGraph: { locale: "ar_SA", alternateLocale: ["en_US"] },
    });
    expect(buildAboutMetadata("en")).toMatchObject({
      title: "About the Saudi Business Launch Guide",
      alternates: {
        canonical: "/en/about",
        languages: { "ar-SA": "/ar/about", en: "/en/about" },
      },
      openGraph: { locale: "en_US", alternateLocale: ["ar_SA"] },
    });
  });

  it("describes the portfolio build as a technical demo using sample data", () => {
    vi.stubEnv("NEXT_PUBLIC_CATALOG_MODE", "PORTFOLIO_DEMO_CATALOG");

    const arabic = buildHomeMetadata("ar");
    expect(arabic).toMatchObject({
      title: "نسخة عرض تقنية | دليل تأسيس المنشآت",
      description:
        "نسخة عرض تقنية لدليل تأسيس المنشآت، توضح تجربة الأسئلة والقواعد الحتمية باستخدام بيانات نموذجية.",
      openGraph: {
        title: "نسخة عرض تقنية | دليل تأسيس المنشآت",
      },
    });

    const english = buildHomeMetadata("en");
    expect(english).toMatchObject({
      title: "Technical Demo | Saudi Business Launch Navigator",
      description:
        "Technical portfolio demo of a business launch navigator using deterministic rules and sample data.",
      openGraph: {
        title: "Technical Demo | Saudi Business Launch Navigator",
      },
    });
    expect(buildAboutMetadata("ar")).toMatchObject({
      title: "حول نسخة العرض | دليل تأسيس المنشآت",
    });
    expect(buildAboutMetadata("en")).toMatchObject({
      title: "About the Demo | Saudi Business Launch Navigator",
    });

    const serialized = JSON.stringify([arabic, english]);
    expect(serialized).not.toMatch(/verified requirements|official next steps/i);
    expect(serialized).not.toContain("المتطلبات والخطوات الرسمية");
  });

  it("does not invent a deployment origin, social handle, or preview image", () => {
    const serialized = JSON.stringify([
      buildHomeMetadata("ar"),
      buildHomeMetadata("en"),
      buildAboutMetadata("ar"),
      buildAboutMetadata("en"),
    ]);
    expect(serialized).not.toMatch(/https?:\/\//);
    expect(serialized).not.toMatch(/twitter|handle|image/i);
  });
});
