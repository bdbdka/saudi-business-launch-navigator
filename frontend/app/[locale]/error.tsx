"use client";

import { usePathname } from "next/navigation";

import { RouteError, localeFromPath } from "@/components/route-feedback";

export default function ErrorBoundary({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <RouteError locale={localeFromPath(usePathname())} reset={reset} />;
}
