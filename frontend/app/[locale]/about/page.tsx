import { notFound } from "next/navigation";

import { AboutPage } from "@/components/about-page";
import { getDictionary, isLocale } from "@/lib/i18n";
import { buildAboutMetadata } from "@/lib/metadata";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) return buildAboutMetadata("ar");
  return buildAboutMetadata(locale);
}

export default async function AboutRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return <AboutPage locale={locale} copy={getDictionary(locale)} />;
}
