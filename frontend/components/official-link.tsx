"use client";

import {
  useCatalogPresentation,
  useIsPortfolioDemo,
} from "@/components/catalog-mode-context";
import { ExternalLinkIcon } from "@/components/icons";

export function OfficialLink({
  url,
  label,
  opensNewWindow,
  unavailableLabel,
  prominent = false,
}: {
  url: string;
  label: string;
  opensNewWindow: string;
  unavailableLabel: string;
  prominent?: boolean;
}) {
  const { locale } = useCatalogPresentation();
  const isDemo = useIsPortfolioDemo();
  if (isDemo) {
    const demoLabel = locale === "ar"
      ? "حول رابط العرض غير الحكومي"
      : "About this non-government demo link";
    return (
      <a
        className={prominent ? "official-service-link" : "official-source-link"}
        href={`/${locale}/about#methodology`}
        data-source-classification="synthetic-demo"
      >
        {demoLabel}
      </a>
    );
  }

  const safeUrl = safeOfficialUrl(url);
  if (!safeUrl) return <span className="source-unavailable">{unavailableLabel}</span>;

  return (
    <a
      className={prominent ? "official-service-link" : "official-source-link"}
      href={safeUrl}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`${label} (${opensNewWindow})`}
      data-source-classification="governed"
    >
      {label}
      <ExternalLinkIcon />
    </a>
  );
}

export function safeOfficialUrl(value: string): string | null {
  try {
    const url = new URL(value);
    return url.protocol === "https:" ? url.toString() : null;
  } catch {
    return null;
  }
}
