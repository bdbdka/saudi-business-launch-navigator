import { readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { safeOfficialUrl } from "@/components/official-link";
import nextConfig, { apiOrigin, catalogMode, contentSecurityPolicy } from "../next.config";

describe("public frontend security configuration", () => {
  it("sets a restrictive baseline CSP and security headers", async () => {
    expect(nextConfig.headers).toBeTypeOf("function");
    const configured = await nextConfig.headers!();
    const headers = Object.fromEntries(configured[0].headers.map((item) => [item.key, item.value]));

    expect(headers["Content-Security-Policy"]).toContain("default-src 'self'");
    expect(headers["Content-Security-Policy"]).toContain("object-src 'none'");
    expect(headers["Content-Security-Policy"]).toContain("frame-ancestors 'none'");
    expect(headers["X-Content-Type-Options"]).toBe("nosniff");
    expect(headers["Permissions-Policy"]).toContain("camera=()");
    expect(contentSecurityPolicy(false)).not.toContain("'unsafe-eval'");
  });

  it("requires production API configuration and does not add wildcard destinations", () => {
    expect(() => apiOrigin("", "production")).toThrow(
      "NEXT_PUBLIC_API_BASE_URL is required",
    );
    const productionOrigin = apiOrigin("https://api.example.invalid", "production");
    expect(apiOrigin("http://127.0.0.1:18000", "production")).toBe("http://127.0.0.1:18000");
    expect(() => apiOrigin("http://api.example.invalid", "production")).toThrow(
      "absolute HTTP(S) URL",
    );
    expect(() => apiOrigin("https://api.example.invalid/v1", "production")).toThrow(
      "absolute HTTP(S) URL",
    );
    const policy = contentSecurityPolicy(false, productionOrigin);
    expect(productionOrigin).toBe("https://api.example.invalid");
    expect(policy).toContain("connect-src 'self' https://api.example.invalid");
    expect(policy).not.toMatch(/localhost|127\.0\.0\.1|0\.0\.0\.0|\[::\]|\s\*\s/);
  });

  it("requires one explicit typed catalog mode for production builds", () => {
    expect(catalogMode("PORTFOLIO_DEMO_CATALOG", "production")).toBe(
      "PORTFOLIO_DEMO_CATALOG",
    );
    expect(catalogMode("GOVERNED_REAL_CATALOG", "production")).toBe(
      "GOVERNED_REAL_CATALOG",
    );
    expect(() => catalogMode("", "production")).toThrow("NEXT_PUBLIC_CATALOG_MODE");
    expect(() => catalogMode("demo", "production")).toThrow("NEXT_PUBLIC_CATALOG_MODE");
    expect(catalogMode("", "development")).toBeNull();
  });

  it("contains no unsafe rendering primitives or browser-exposed secret names", () => {
    const root = resolve(import.meta.dirname, "..");
    const files = ["app", "components", "lib"]
      .flatMap((directory) => productionSourceFiles(resolve(root, directory)));
    const content = [
      ...files.map((file) => readFileSync(file, "utf8")),
      readFileSync(resolve(root, ".env.example"), "utf8"),
    ].join("\n");

    expect(content).not.toContain("dangerouslySetInnerHTML");
    expect(content).not.toMatch(/\beval\s*\(/);
    expect(content).not.toContain("new Function");
    expect(content).not.toMatch(/NEXT_PUBLIC_(OPENAI|DATABASE|SECRET|TOKEN|PASSWORD)/);
    expect(content).not.toMatch(/\b(?:localStorage|sessionStorage)\b/);
    expect(content).not.toMatch(/\bdocument\.cookie\b/);
  });

  it("allows only HTTPS official links", () => {
    expect(safeOfficialUrl("https://official.example.invalid/service")).toBe(
      "https://official.example.invalid/service",
    );
    expect(safeOfficialUrl("http://official.example.invalid/service")).toBeNull();
    expect(safeOfficialUrl("javascript:alert(1)")).toBeNull();
    expect(safeOfficialUrl("not-a-url")).toBeNull();
  });
});

function productionSourceFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) return productionSourceFiles(path);
    return /\.(?:ts|tsx)$/.test(entry.name) ? [path] : [];
  });
}
