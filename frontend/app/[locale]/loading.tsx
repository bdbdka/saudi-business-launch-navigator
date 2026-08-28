"use client";

import { usePathname } from "next/navigation";

import { RouteLoading, localeFromPath } from "@/components/route-feedback";

export default function Loading() {
  return <RouteLoading locale={localeFromPath(usePathname())} />;
}
