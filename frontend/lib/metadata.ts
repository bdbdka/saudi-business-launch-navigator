import type { Metadata } from "next";

import {
  catalogPresentationPolicy,
  configuredCatalogMode,
} from "@/lib/catalog-presentation";
import { getDictionary, type Locale } from "@/lib/i18n";

export function buildHomeMetadata(locale: Locale): Metadata {
  const copy = homeMetadataCopy(locale);
  return buildLocalizedMetadata({
    locale,
    title: copy.title,
    description: copy.description,
    path: `/${locale}`,
  });
}

export function buildAboutMetadata(locale: Locale): Metadata {
  const copy = aboutMetadataCopy(locale);
  return buildLocalizedMetadata({
    locale,
    title: copy.title,
    description: copy.description,
    path: `/${locale}/about`,
    alternatePath: (alternateLocale) => `/${alternateLocale}/about`,
  });
}

export function homeMetadataCopy(locale: Locale): { title: string; description: string } {
  const copy = getDictionary(locale);
  const policy = catalogPresentationPolicy(configuredCatalogMode(), locale);
  return policy.isPortfolioDemo
    ? {
        title: policy.text.metadata.homeTitle,
        description: policy.text.metadata.homeDescription,
      }
    : {
        title: copy.metadata.homeTitle,
        description: copy.metadata.homeDescription,
      };
}

function aboutMetadataCopy(locale: Locale): { title: string; description: string } {
  const copy = getDictionary(locale);
  const policy = catalogPresentationPolicy(configuredCatalogMode(), locale);
  return policy.isPortfolioDemo
    ? {
        title: policy.text.metadata.aboutTitle,
        description: policy.text.metadata.aboutDescription,
      }
    : {
        title: copy.metadata.aboutTitle,
        description: copy.metadata.aboutDescription,
      };
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
