import { describe, expect, it } from "vitest";

import { navigatorAPI } from "@/lib/api/client";

const runLiveAPI = process.env.SBLN_RUN_FRONTEND_LIVE_API === "1";
const runLiveAI = process.env.SBLN_RUN_FRONTEND_LIVE_AI === "1";

describe.skipIf(!runLiveAPI)("live API contract", () => {
  it("loads activities and questionnaires for all three supported activities", async () => {
    const response = await navigatorAPI.activities();
    expect(response.activities.map((activity) => activity.code).sort()).toEqual([
      "cloud_kitchen",
      "coffee_shop",
      "restaurant",
    ]);
    expect(response.metadata).toMatchObject({
      catalog_mode: "PORTFOLIO_DEMO_CATALOG",
      publication_state: "SAMPLE_ONLY",
      data_classification: "SYNTHETIC_PORTFOLIO_DEMO",
      public_catalog_approved: false,
    });

    const expectedCounts = { coffee_shop: 7, restaurant: 8, cloud_kitchen: 7 } as const;
    for (const activity of response.activities) {
      const questionnaire = await navigatorAPI.questionnaire(activity.code);
      expect(questionnaire.questionnaire.activity.code).toBe(activity.code);
      expect(questionnaire.questionnaire.questions).toHaveLength(expectedCounts[activity.code]);
      expect(questionnaire.questionnaire.questions.every((question) => question.allows_unknown)).toBe(
        true,
      );
      expect(questionnaire.questionnaire.questions.slice(0, 3).map((question) => question.purpose)).toEqual([
        "NAVIGATION",
        "NAVIGATION",
        "NAVIGATION",
      ]);
      const vat = questionnaire.questionnaire.questions.find(
        (question) =>
          question.fact_code === "zatca_confirmed_mandatory_vat_registration_applies",
      );
      expect(vat?.answer_labels).toEqual({
        true_ar: "تأكدت عبر الهيئة أنه إلزامي",
        true_en: "I confirmed through ZATCA that it is mandatory",
        false_ar: "تأكدت عبر الهيئة أنه غير إلزامي",
        false_en: "I confirmed through ZATCA that it is not mandatory",
        unknown_ar: "لم أتأكد عبر الهيئة بعد",
        unknown_en: "I have not confirmed through ZATCA yet",
      });
      expect(questionnaire.questionnaire.questions.map((question) => question.fact_code)).not.toContain(
        "vat_registration_threshold_reached",
      );
    }
  });

  it("preserves true, false, and unknown through the real checklist boundary", async () => {
    const coffee = await navigatorAPI.checklist("coffee_shop", {
      ownership_investor_route: "foreign_legal_entity_or_mixed_foreign_ownership",
      planned_legal_form: "limited_liability_company",
      has_selected_business_premises: true,
      has_employees: true,
      has_food_establishment_workers: true,
      offers_home_delivery: true,
      zatca_confirmed_mandatory_vat_registration_applies: true,
    });
    expect(coffee.result.applies).toHaveLength(5);
    expect(coffee.result.does_not_apply).toHaveLength(0);
    expect(coffee.result.needs_information).toHaveLength(0);
    expect(coffee.result.journey_guidance).toHaveLength(6);
    expect(coffee.result.missing_navigation_information).toHaveLength(0);
    expect(coffee.result.applies.flatMap((item) => item.actionability).length).toBeGreaterThan(0);
    const unconditional = coffee.result.applies.find((item) => item.condition_result === null);
    expect(unconditional?.evaluated_facts).toEqual([]);
    const conditional = coffee.result.applies.find((item) => item.evaluated_facts.length > 0);
    expect(conditional?.evaluated_facts.every((fact) => fact.text_origin === "PROJECT_AUTHORED")).toBe(true);
    expect(conditional?.sources[0].official_title_ar).toBeTruthy();

    const restaurant = await navigatorAPI.checklist("restaurant", {
      ownership_investor_route: null,
      planned_legal_form: null,
      has_selected_business_premises: null,
      has_employees: false,
      has_food_establishment_workers: true,
      offers_home_delivery: true,
      uses_public_sidewalk_for_customer_service: null,
      zatca_confirmed_mandatory_vat_registration_applies: null,
    });
    expect(restaurant.result.applies).toHaveLength(4);
    expect(restaurant.result.does_not_apply).toHaveLength(2);
    expect(restaurant.result.needs_information).toHaveLength(2);
    expect(restaurant.result.missing_navigation_information).toHaveLength(3);
    expect(
      restaurant.result.does_not_apply.every((item) => item.actionability.length === 0),
    ).toBe(true);
    expect(
      restaurant.result.needs_information.every((item) =>
        item.evaluated_facts.some((fact) => fact.supplied_value === null),
      ),
    ).toBe(true);

    const cloudKitchen = await navigatorAPI.checklist("cloud_kitchen", {});
    expect(cloudKitchen.result.applies).toHaveLength(1);
    expect(cloudKitchen.result.needs_information).toHaveLength(4);
    expect(cloudKitchen.result.missing_navigation_information).toHaveLength(3);
    expect(cloudKitchen.result.coverage_notice.unresolved_topics).not.toHaveLength(0);
    expect(cloudKitchen.result.regulatory_snapshot.publication_count).toBe(0);

    const routedCloudKitchen = await navigatorAPI.checklist("cloud_kitchen", {
      ownership_investor_route: "foreign_legal_entity_or_mixed_foreign_ownership",
      planned_legal_form: "limited_liability_company",
      has_selected_business_premises: false,
      has_employees: true,
      has_food_establishment_workers: true,
      offers_home_delivery: true,
      zatca_confirmed_mandatory_vat_registration_applies: false,
    });
    const siteGuidance = routedCloudKitchen.result.journey_guidance.find(
      (item) => item.topic_code === "site_activity_verification",
    );
    expect(siteGuidance?.routing_status).toBe("ROUTED");
    expect(siteGuidance?.destinations).toHaveLength(1);
    expect(routedCloudKitchen.result.missing_navigation_information).toHaveLength(0);
    expect(routedCloudKitchen.result.regulatory_snapshot.catalog_mode).toBe("PORTFOLIO_DEMO");
    expect(
      [...routedCloudKitchen.result.applies, ...routedCloudKitchen.result.does_not_apply]
        .some((item) => item.requirement_code.toLowerCase().includes("misa")),
    ).toBe(false);
  });
});

describe.skipIf(!runLiveAPI || !runLiveAI)("optional live AI boundary", () => {
  it("returns a governed navigator envelope without making AI authoritative", async () => {
    const response = await navigatorAPI.navigate("أرغب في فتح مطعم ولدي موظفون", "ar");
    expect(response.metadata.public_catalog_approved).toBe(false);
    expect(response.interpretation.language).toBe("ar");
    if (response.authoritative_result) {
      expect(response.authoritative_result.regulatory_snapshot.publication_count).toBe(0);
    }
  });
});
