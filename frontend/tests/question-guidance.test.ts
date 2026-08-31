import { describe, expect, it } from "vitest";

import type { QuestionFactCode } from "@/lib/api/types";
import { getQuestionGuidance } from "@/lib/question-guidance";

const factCodes: QuestionFactCode[] = [
  "ownership_investor_route",
  "planned_legal_form",
  "has_selected_business_premises",
  "has_employees",
  "gosi_coverage_conditions_met",
  "has_food_establishment_workers",
  "zatca_confirmed_mandatory_vat_registration_applies",
  "offers_home_delivery",
  "uses_public_sidewalk_for_customer_service",
];

describe("beginner question guidance", () => {
  it.each(["ar", "en"] as const)(
    "gives every governed fact a meaning, reason, and useful example in %s",
    (locale) => {
      for (const code of factCodes) {
        const guidance = getQuestionGuidance(code, locale);
        expect(guidance.meaning.trim(), `${code} meaning`).not.toBe("");
        expect(guidance.why.trim(), `${code} why`).not.toBe("");
        expect(guidance.example?.trim(), `${code} example`).not.toBe("");
      }
    },
  );

  it("keeps VAT unknown-safe and aligns sidewalk language", () => {
    const vat = getQuestionGuidance(
      "zatca_confirmed_mandatory_vat_registration_applies",
      "en",
    );
    expect(vat.meaning).toContain("does not calculate revenue");
    expect(vat.example).toContain("have not confirmed");

    const sidewalk = getQuestionGuidance(
      "uses_public_sidewalk_for_customer_service",
      "en",
    );
    expect(sidewalk.prompt).toContain("in front of the premises");
    expect(sidewalk.meaning).toContain("public sidewalk");
  });

  it("treats third-party delivery as delivery in the product guidance", () => {
    const delivery = getQuestionGuidance("offers_home_delivery", "en");
    expect(delivery.meaning).toContain("third-party platform");
  });
});
