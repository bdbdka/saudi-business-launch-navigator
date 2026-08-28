import type { NextConfig } from "next";

export type FrontendCatalogMode = "GOVERNED_REAL_CATALOG" | "PORTFOLIO_DEMO_CATALOG";

export function catalogMode(
  configured = process.env.NEXT_PUBLIC_CATALOG_MODE,
  environment = process.env.NODE_ENV,
): FrontendCatalogMode | null {
  if (configured === "GOVERNED_REAL_CATALOG" || configured === "PORTFOLIO_DEMO_CATALOG") {
    return configured;
  }
  if (environment === "production") {
    throw new Error(
      "NEXT_PUBLIC_CATALOG_MODE must select GOVERNED_REAL_CATALOG or PORTFOLIO_DEMO_CATALOG for a production frontend build.",
    );
  }
  return null;
}

export function apiOrigin(
  configured = process.env.NEXT_PUBLIC_API_BASE_URL,
  environment = process.env.NODE_ENV,
): string {
  const value = configured?.trim();
  if (!value && environment === "production") {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is required for a production frontend build.");
  }
  try {
    const parsed = new URL(value || "http://127.0.0.1:8000");
    if (!["http:", "https:"].includes(parsed.protocol)) {
      throw new Error("unsupported protocol");
    }
    if (
      parsed.username ||
      parsed.password ||
      parsed.pathname !== "/" ||
      parsed.search ||
      parsed.hash
    ) {
      throw new Error("origin must not contain credentials or a path");
    }
    if (
      environment === "production" &&
      parsed.protocol !== "https:" &&
      !["localhost", "127.0.0.1", "[::1]"].includes(parsed.hostname)
    ) {
      throw new Error("production origins require HTTPS outside loopback rehearsal");
    }
    return parsed.origin;
  } catch {
    throw new Error("NEXT_PUBLIC_API_BASE_URL must be an absolute HTTP(S) URL.");
  }
}

export function contentSecurityPolicy(
  development = process.env.NODE_ENV !== "production",
  configuredAPIOrigin = apiOrigin(),
): string {
  return [
    "default-src 'self'",
    `script-src 'self' 'unsafe-inline'${development ? " 'unsafe-eval'" : ""}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    `connect-src 'self'${configuredAPIOrigin ? ` ${configuredAPIOrigin}` : ""}${development ? " ws://localhost:3000 ws://127.0.0.1:3000" : ""}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join("; ");
}

const validatedCatalogMode = catalogMode();

const nextConfig: NextConfig = {
  agentRules: false,
  devIndicators: false,
  output: "standalone",
  poweredByHeader: false,
  reactStrictMode: true,
  env: validatedCatalogMode
    ? { NEXT_PUBLIC_CATALOG_MODE: validatedCatalogMode }
    : undefined,
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "Content-Security-Policy", value: contentSecurityPolicy() },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=(), payment=()",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
