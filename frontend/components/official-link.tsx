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
  const safeUrl = safeOfficialUrl(url);
  if (!safeUrl) return <span className="source-unavailable">{unavailableLabel}</span>;
  const resolvedLabel = isDemo
    ? (locale === "ar" ? "رابط تجريبي غير حكومي" : "Non-government demo link")
    : label;

  return (
    <a
      className={prominent ? "official-service-link" : "official-source-link"}
      href={safeUrl}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`${resolvedLabel} (${opensNewWindow})`}
      data-source-classification={
        isDemo ? "synthetic-demo" : "governed"
      }
    >
      {resolvedLabel}
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
