import "@testing-library/jest-dom/vitest";

import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

process.env.NEXT_PUBLIC_CATALOG_MODE = "GOVERNED_REAL_CATALOG";

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
});

Object.defineProperty(window.HTMLElement.prototype, "scrollIntoView", {
  configurable: true,
  value: () => undefined,
});
