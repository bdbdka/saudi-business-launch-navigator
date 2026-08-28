import type { Metadata } from "next";

import { getDictionary, type Locale } from "@/lib/i18n";

export function buildHomeMetadata(locale: Locale): Metadata {
  const copy = getDictionary(locale);
  return buildLocalizedMetadata({
    locale,
    title: copy.metadata.homeTitle,
    description: copy.metadata.homeDescription,
    path: `/${locale}`,
  });
}

export function buildAboutMetadata(locale: Locale): Metadata {
  const copy = getDictionary(locale);
  return buildLocalizedMetadata({
    locale,
    title: copy.metadata.aboutTitle,
    description: copy.metadata.aboutDescription,
    path: `/${locale}/about`,
    alternatePath: (alternateLocale) => `/${alternateLocale}/about`,
  });
}

function buildLocalizedMetadata({
  locale,
  title,
  description,
  path,
  alternatePath = (alternateLocale) => `/${alternateLocale}`,
}: {
  locale: Locale;
  title: string;
  description: string;
  path: string;
  alternatePath?: (locale: Locale) => string;
}): Metadata {
  return {
    title,
    description,
    applicationName: getDictionary(locale).productName,
    alternates: {
      canonical: path,
      languages: {
        "ar-SA": alternatePath("ar"),
        en: alternatePath("en"),
      },
    },
    openGraph: {
      type: "website",
      title,
      description,
      locale: locale === "ar" ? "ar_SA" : "en_US",
      alternateLocale: locale === "ar" ? ["en_US"] : ["ar_SA"],
    },
    robots: { index: false, follow: false },
  };
}
