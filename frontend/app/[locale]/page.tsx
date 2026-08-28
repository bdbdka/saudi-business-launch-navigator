import { notFound } from "next/navigation";

import { NavigatorApp } from "@/components/navigator-app";
import { isLocale } from "@/lib/i18n";

export default async function LocalePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return <NavigatorApp initialLocale={locale} />;
}
