import type { Metadata } from "next";
import { notFound } from "next/navigation";

import "../globals.css";
import { isLocale, locales, type Locale } from "@/lib/i18n";
import { buildHomeMetadata } from "@/lib/metadata";

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: value } = await params;
  const locale: Locale = isLocale(value) ? value : "ar";
  return buildHomeMetadata(locale);
}

export default async function LocaleLayout({
  children,
  params,
}: Readonly<{
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}>) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return (
    <html lang={locale} dir={locale === "ar" ? "rtl" : "ltr"} data-scroll-behavior="smooth">
      <body>{children}</body>
    </html>
  );
}
