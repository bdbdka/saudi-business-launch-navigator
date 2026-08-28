"use client";

import { useEffect, useState } from "react";

import { DemoNotice } from "@/components/demo-notice";
import { navigatorAPI } from "@/lib/api/client";
import type { CatalogBoundary } from "@/lib/api/types";
import { catalogBoundaryMatchesBuild } from "@/lib/catalog-presentation";
import type { Locale } from "@/lib/i18n";

export function DemoBoundaryProbe({ locale }: { locale: Locale }) {
  const [metadata, setMetadata] = useState<CatalogBoundary | null>(null);

  useEffect(() => {
    let cancelled = false;
    navigatorAPI.activities()
      .then((response) => {
        if (!cancelled && catalogBoundaryMatchesBuild(response.metadata)) {
          setMetadata(response.metadata);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  return <DemoNotice metadata={metadata} locale={locale} />;
}
