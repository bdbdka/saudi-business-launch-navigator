import { describe, expect, it } from "vitest";

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
