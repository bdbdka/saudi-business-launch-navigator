import { afterEach, describe, expect, it, vi } from "vitest";

import {
  BUILD_COMMIT_HEADER,
  buildCommitHeader,
  validatedBuildCommit,
} from "@/lib/build-identity";
import nextConfig from "../next.config";

const LOWERCASE_SHA = "0123456789abcdef0123456789abcdef01234567";
const UPPERCASE_SHA = LOWERCASE_SHA.toUpperCase();

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("frontend build identity", () => {
  it("emits the exact valid Render commit as a nonvisual response header", async () => {
    vi.stubEnv("SBLN_FRONTEND_BUILD_COMMIT", LOWERCASE_SHA);

    expect(validatedBuildCommit(LOWERCASE_SHA)).toBe(LOWERCASE_SHA);
    expect(validatedBuildCommit(UPPERCASE_SHA)).toBe(UPPERCASE_SHA);
    expect(buildCommitHeader()).toEqual({
      key: BUILD_COMMIT_HEADER,
      value: LOWERCASE_SHA,
    });

    const configured = await nextConfig.headers!();
    const headers = Object.fromEntries(configured[0].headers.map((item) => [item.key, item.value]));
    expect(headers[BUILD_COMMIT_HEADER]).toBe(LOWERCASE_SHA);
  });

  it("omits deployment identity safely when a local build has no SHA", async () => {
    vi.stubEnv("SBLN_FRONTEND_BUILD_COMMIT", "");

    expect(validatedBuildCommit(undefined)).toBeNull();
    expect(buildCommitHeader()).toBeNull();

    const configured = await nextConfig.headers!();
    expect(configured[0].headers).not.toContainEqual(
      expect.objectContaining({ key: BUILD_COMMIT_HEADER }),
    );
  });

  it.each([
    "a".repeat(39),
    "a".repeat(41),
    "g".repeat(40),
    `${"a".repeat(40)}\n`,
    ` ${"a".repeat(39)}`,
  ])("rejects malformed or injectable build identity %j", (value) => {
    expect(() => validatedBuildCommit(value)).toThrow(
      "SBLN_FRONTEND_BUILD_COMMIT must be exactly 40 hexadecimal characters.",
    );
  });
});
