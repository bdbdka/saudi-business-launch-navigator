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

  it("presents portfolio routes as a professional product without regulatory overclaims", () => {
    vi.stubEnv("NEXT_PUBLIC_CATALOG_MODE", "PORTFOLIO_DEMO_CATALOG");

    const arabic = buildHomeMetadata("ar");
    expect(arabic).toMatchObject({
      title: "دليل تأسيس المنشآت في السعودية",
      description:
        "دليل عربي يساعدك على تنظيم خطوات بدء مقهى أو مطعم أو مطبخ سحابي من خلال أسئلة قصيرة.",
      openGraph: {
        title: "دليل تأسيس المنشآت في السعودية",
        description:
          "دليل عربي يساعدك على تنظيم خطوات بدء مقهى أو مطعم أو مطبخ سحابي من خلال أسئلة قصيرة.",
      },
    });

    const english = buildHomeMetadata("en");
    expect(english).toMatchObject({
      title: "Saudi Business Launch Navigator",
      description:
        "An Arabic-first guide that organizes launch steps for coffee shops, restaurants, and cloud kitchens through a short questionnaire.",
      openGraph: {
        title: "Saudi Business Launch Navigator",
        description:
          "An Arabic-first guide that organizes launch steps for coffee shops, restaurants, and cloud kitchens through a short questionnaire.",
      },
    });
    const arabicAbout = buildAboutMetadata("ar");
    expect(arabicAbout).toMatchObject({
      title: "حول دليل تأسيس المنشآت",
      description: "تعرّف على هدف الدليل وطريقة عمله ومصادره وحدود النسخة التجريبية.",
    });
    const englishAbout = buildAboutMetadata("en");
    expect(englishAbout).toMatchObject({
      title: "About | Saudi Business Launch Navigator",
      description: "Learn what the guide does, how it handles sources, and the limits of the public demo.",
    });

    const serialized = JSON.stringify([arabic, english, arabicAbout, englishAbout]);
    expect(serialized).not.toMatch(/verified requirements|official next steps/i);
    expect(serialized).not.toContain("المتطلبات والخطوات الرسمية");
    expect(serialized).not.toMatch(/technical demo|technical portfolio|deterministic rules/i);
    expect(serialized).not.toMatch(/نسخة عرض تقنية|القواعد الحتمية/);
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
