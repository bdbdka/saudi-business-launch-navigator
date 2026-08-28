import { afterEach, describe, expect, it, vi } from "vitest";

import { API_BASE_URL, navigatorAPI, resolveAPIBaseURL } from "@/lib/api/client";
import { activitiesResponse, checklistResponse, activities } from "@/tests/fixtures";

afterEach(() => vi.unstubAllGlobals());

describe("typed API client", () => {
  it("uses localhost only for local work and requires explicit production configuration", () => {
    expect(resolveAPIBaseURL("", "development")).toBe("http://127.0.0.1:8000");
    expect(resolveAPIBaseURL("", "test")).toBe("http://127.0.0.1:8000");
    expect(() => resolveAPIBaseURL("", "production")).toThrow(
      "NEXT_PUBLIC_API_BASE_URL is required",
    );
    expect(resolveAPIBaseURL("https://api.example.test/", "production")).toBe("https://api.example.test");
    expect(resolveAPIBaseURL("http://127.0.0.1:18000", "production")).toBe("http://127.0.0.1:18000");
    expect(() => resolveAPIBaseURL("http://api.example.test", "production")).toThrow("use HTTPS");
    expect(() => resolveAPIBaseURL("https://api.example.test/v1", "production")).toThrow(
      "without credentials or a path",
    );
    expect(() => resolveAPIBaseURL("https://user:secret@api.example.test", "production")).toThrow(
      "without credentials or a path",
    );
    expect(() => resolveAPIBaseURL("file:///tmp/socket", "production")).toThrow(
      "absolute HTTP(S) URL",
    );
  });

  it("loads activities from the centralized API base URL", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(activitiesResponse), {
        status: 200,
        headers: { "Content-Type": "application/json", "X-Request-ID": "request-one" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    await expect(navigatorAPI.activities()).resolves.toEqual(activitiesResponse);
    expect(fetchMock).toHaveBeenCalledWith(
      `${API_BASE_URL}/api/v1/activities`,
      expect.objectContaining({ cache: "no-store", credentials: "omit" }),
    );
  });

  it("preserves true false and unknown exactly in checklist JSON", async () => {
    const response = checklistResponse(activities[2], { applies: 3, doesNotApply: 1, needs: 1 });
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(response), { status: 200, headers: { "Content-Type": "application/json" } }),
    );
    vi.stubGlobal("fetch", fetchMock);
    await navigatorAPI.checklist("restaurant", {
      has_employees: false,
      has_food_establishment_workers: true,
      offers_home_delivery: true,
      uses_public_sidewalk_for_customer_service: null,
      zatca_confirmed_mandatory_vat_registration_applies: null,
    });
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(JSON.parse(String(init.body))).toEqual({
      activity_code: "restaurant",
      facts: {
        has_employees: false,
        has_food_establishment_workers: true,
        offers_home_delivery: true,
        uses_public_sidewalk_for_customer_service: null,
        zatca_confirmed_mandatory_vat_registration_applies: null,
      },
      navigation_facts: {},
    });
  });

  it("keeps navigation answers outside regulatory facts", async () => {
    const response = checklistResponse(activities[0], { applies: 2, doesNotApply: 0, needs: 1 });
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(response), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    await navigatorAPI.checklist("cloud_kitchen", {
      ownership_investor_route: "foreign_legal_entity_or_mixed_foreign_ownership",
      planned_legal_form: "limited_liability_company",
      has_selected_business_premises: null,
      has_employees: true,
    });
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(JSON.parse(String(init.body))).toEqual({
      activity_code: "cloud_kitchen",
      facts: { has_employees: true },
      navigation_facts: {
        ownership_investor_route: "foreign_legal_entity_or_mixed_foreign_ownership",
        planned_legal_form: "limited_liability_company",
        has_selected_business_premises: null,
      },
    });
  });

  it("maps the stable API error envelope without exposing a secret", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: { code: "VALIDATION_ERROR", message: "Invalid request", details: [], request_id: "r7" },
          }),
          { status: 422, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    await expect(navigatorAPI.questionnaire("restaurant")).rejects.toMatchObject({
      code: "VALIDATION_ERROR",
      status: 422,
      requestId: "r7",
    });
  });

  it("maps network failure to backend unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network down")));
    await expect(navigatorAPI.activities()).rejects.toMatchObject({
      code: "BACKEND_UNAVAILABLE",
      status: null,
    });
  });
});
