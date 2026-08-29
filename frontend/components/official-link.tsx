"use client";

import {
  useCatalogPresentation,
} from "@/components/catalog-mode-context";
import { ExternalLinkIcon } from "@/components/icons";
import { presentSourceLink } from "@/lib/catalog-presentation";

export { safeOfficialUrl } from "@/lib/catalog-presentation";

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
  const { locale, policy } = useCatalogPresentation();
  const presented = presentSourceLink(url, policy.mode, locale);
  if (presented.kind === "demo-information") {
    return (
      <a
        className={prominent ? "official-service-link" : "official-source-link"}
        href={presented.href}
        data-source-classification="synthetic-demo"
      >
        {presented.label}
      </a>
    );
  }

  if (presented.kind === "unavailable") {
    return <span className="source-unavailable">{unavailableLabel}</span>;
  }

  return (
    <a
      className={prominent ? "official-service-link" : "official-source-link"}
      href={presented.href}
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
