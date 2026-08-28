"use client";

import { usePathname } from "next/navigation";

import { NotFoundContent, localeFromPath } from "@/components/route-feedback";

export default function NotFound() {
  return <NotFoundContent locale={localeFromPath(usePathname())} />;
}
