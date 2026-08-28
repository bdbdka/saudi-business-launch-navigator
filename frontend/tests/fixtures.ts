import type {
  ActivitiesResponse,
  Activity,
  ActionabilityItem,
  ApplicabilityStatus,
  ChecklistItem,
  ChecklistResponse,
  FactCode,
  GovernedSourceTrace,
  JourneyGuidance,
  NavigationFactCode,
  NavigatorResponse,
  Question,
  QuestionnaireResponse,
} from "@/lib/api/types";

export const metadata = {
  catalog_mode: "GOVERNED_REAL_CATALOG",
  publication_state: "UNPUBLISHED",
  data_classification: "PRIVATE_GOVERNED_UNPUBLISHED",
  public_catalog_approved: false,
  warning_ar: "واجهة تطوير داخلية لبيانات محكومة غير منشورة، وليست كتالوجاً تنظيمياً عاماً.",
  warning_en: "Internal development API over governed unpublished data; not a public catalog.",
} as const;

export const activities: Activity[] = [
  { code: "cloud_kitchen", name_ar: "مطبخ سحابي", name_en: "Cloud kitchen" },
  { code: "coffee_shop", name_ar: "مقهى", name_en: "Coffee shop" },
  { code: "restaurant", name_ar: "مطعم", name_en: "Restaurant" },
];

export const activitiesResponse: ActivitiesResponse = { metadata, activities };

const questionText: Record<FactCode, { ar: string; en: string; helpAr: string; helpEn: string }> = {
  gosi_coverage_conditions_met: { ar: "هل تحققت شروط التأمينات؟", en: "Are GOSI conditions met?", helpAr: "تحقق من الشروط الرسمية.", helpEn: "Confirm the official conditions." },
  has_employees: { ar: "هل ستوظف موظفين أو عمالًا للعمل في المنشأة؟", en: "Will the business employ staff or workers?", helpAr: "المقصود موظفو المنشأة وعمالها، وليس عمال شركات التوصيل أو المقاولين الخارجيين.", helpEn: "This means people employed by the business, not third-party delivery workers or external contractors." },
  has_food_establishment_workers: { ar: "هل سيعمل موظفون أو عمال داخل منشأة الطعام أو المشروبات؟", en: "Will staff or workers work in the food or beverage establishment?", helpAr: "المقصود الأشخاص الذين سيعملون داخل نشاط الطعام أو المشروبات عند بدء التشغيل.", helpEn: "This means people who will work inside the food or beverage business when it starts operating." },
  zatca_confirmed_mandatory_vat_registration_applies: { ar: "بعد التحقق عبر المسار الرسمي لهيئة الزكاة والضريبة والجمارك، ما حالة التسجيل الإلزامي في ضريبة القيمة المضافة لمنشأتك؟", en: "After checking through ZATCA’s official route, what is the mandatory VAT registration status for your business?", helpAr: "اختر «إلزامي» أو «غير إلزامي» فقط إذا تأكدت من حالة منشأتك عبر المسار الرسمي للهيئة. إذا لم تتحقق، أو بقيت الحالة غير واضحة، اختر «لم أتأكد عبر الهيئة بعد». لا يحسب الدليل الإيرادات أو التوريدات، ولا يحدد الحدود أو الاستثناءات، ولا يحول التسجيل الاختياري إلى التزام.", helpEn: "Choose “Mandatory” or “Not mandatory” only after confirming the business’s status through ZATCA’s official route. If you have not checked or the status remains unclear, choose “I have not confirmed through ZATCA yet.” The Navigator does not calculate revenue or supplies, determine thresholds or exceptions, or turn optional registration into an obligation." },
  offers_home_delivery: { ar: "هل ستقدم المنشأة خدمة التوصيل المنزلي؟", en: "Will the establishment offer home delivery?", helpAr: "المقصود توصيل طلبات المنشأة إلى العملاء.", helpEn: "This means delivering the business's orders to customers." },
  uses_public_sidewalk_for_customer_service: { ar: "هل ستستخدم الرصيف العام أمام المطعم لخدمة العملاء؟", en: "Will the restaurant use the public sidewalk opposite the premises for customer service?", helpAr: "المقصود الجزء العام خارج حدود موقعك المرخص، وليس المساحة الخاصة داخل المنشأة.", helpEn: "This means public space outside the licensed premises, not private space inside the business." },
};

function question(factCode: FactCode): Question {
  const vat = factCode === "zatca_confirmed_mandatory_vat_registration_applies";
  return {
    fact_code: factCode,
    fact_version: 1,
    data_type: "boolean",
    purpose: "APPLICABILITY",
    allows_unknown: true,
    question_ar: questionText[factCode].ar,
    question_en: questionText[factCode].en,
    help_text_ar: questionText[factCode].helpAr,
    help_text_en: questionText[factCode].helpEn,
    answer_labels: vat
      ? {
          true_ar: "تأكدت عبر الهيئة أنه إلزامي",
          true_en: "I confirmed through ZATCA that it is mandatory",
          false_ar: "تأكدت عبر الهيئة أنه غير إلزامي",
          false_en: "I confirmed through ZATCA that it is not mandatory",
          unknown_ar: "لم أتأكد عبر الهيئة بعد",
          unknown_en: "I have not confirmed through ZATCA yet",
        }
      : {
          true_ar: "نعم",
          true_en: "Yes",
          false_ar: "لا",
          false_en: "No",
          unknown_ar: "لست متأكدًا",
          unknown_en: "Not sure",
        },
    options: [],
    unknown_label_ar: vat ? "لم أتأكد عبر الهيئة بعد" : "لست متأكدًا",
    unknown_label_en: vat ? "I have not confirmed through ZATCA yet" : "Not sure",
    text_origin: "PROJECT_AUTHORED",
  };
}

const sharedFactCodes: FactCode[] = [
  "has_employees",
  "has_food_establishment_workers",
  "offers_home_delivery",
];
const vatFactCode = "zatca_confirmed_mandatory_vat_registration_applies" as const;

const navigationQuestions: Question[] = [
  {
    fact_code: "ownership_investor_route",
    fact_version: 1,
    data_type: "enum",
    purpose: "NAVIGATION",
    allows_unknown: true,
    question_ar: "من سيملك المشروع؟",
    question_en: "Who will own the business?",
    help_text_ar: "اختر الخيار الأقرب لحالتك.",
    help_text_en: "Choose the option closest to your situation.",
    answer_labels: null,
    options: [
      { value: "saudi_person_or_saudi_owned_entity", label_ar: "فرد سعودي أو منشأة مملوكة سعودياً", label_en: "Saudi person or Saudi-owned entity" },
      { value: "gcc_person_or_wholly_gcc_owned_entity", label_ar: "فرد خليجي أو منشأة مملوكة بالكامل لمواطني دول مجلس التعاون", label_en: "GCC person or wholly GCC-owned entity" },
      { value: "foreign_legal_entity_or_mixed_foreign_ownership", label_ar: "جهة أجنبية أو ملكية مختلطة تشمل مستثمراً أجنبياً", label_en: "Foreign legal entity or mixed ownership including a foreign investor" },
      { value: "premium_residency_individual", label_ar: "فرد يحمل الإقامة المميزة", label_en: "Premium Residency holder" },
      { value: "other", label_ar: "حالة ملكية أخرى", label_en: "Other ownership situation" },
    ],
    unknown_label_ar: "لست متأكدًا",
    unknown_label_en: "Not sure",
    text_origin: "PROJECT_AUTHORED",
  },
  {
    fact_code: "planned_legal_form",
    fact_version: 1,
    data_type: "enum",
    purpose: "NAVIGATION",
    allows_unknown: true,
    question_ar: "ما الشكل القانوني الذي تنوي استخدامه؟",
    question_en: "Which legal form do you plan to use?",
    help_text_ar: "اختر الشكل القانوني أو لم أحدد بعد.",
    help_text_en: "Choose the legal form or Not decided yet.",
    answer_labels: null,
    options: [
      { value: "individual_establishment", label_ar: "مؤسسة فردية", label_en: "Individual establishment" },
      { value: "limited_liability_company", label_ar: "شركة ذات مسؤولية محدودة", label_en: "Limited liability company" },
      { value: "other", label_ar: "شكل قانوني آخر", label_en: "Another legal form" },
    ],
    unknown_label_ar: "لم أحدد بعد",
    unknown_label_en: "Not decided yet",
    text_origin: "PROJECT_AUTHORED",
  },
  {
    ...question("has_employees"),
    fact_code: "has_selected_business_premises",
    purpose: "NAVIGATION",
    question_ar: "هل اخترت موقعًا للمشروع؟",
    question_en: "Have you chosen premises for the business?",
    help_text_ar: "لا تحتاج إلى إدخال عنوان.",
    help_text_en: "Do not enter an address.",
  },
];

const navigationQuestionByCode = Object.fromEntries(
  navigationQuestions.map((item) => [item.fact_code, item]),
) as Record<NavigationFactCode, Question>;

export const questionsByActivity: Record<Activity["code"], Question[]> = {
  coffee_shop: [...navigationQuestions, ...[...sharedFactCodes, vatFactCode].map(question)],
  cloud_kitchen: [...navigationQuestions, ...[...sharedFactCodes, vatFactCode].map(question)],
  restaurant: [
    ...navigationQuestions,
    ...([
      ...sharedFactCodes,
      "uses_public_sidewalk_for_customer_service",
      vatFactCode,
    ] satisfies FactCode[]).map(question),
  ],
};

export const questions = questionsByActivity.coffee_shop;

export function questionnaireResponse(activity: Activity): QuestionnaireResponse {
  return { metadata, questionnaire: { activity, questions: questionsByActivity[activity.code] } };
}

function checklistItem(
  index: number,
  status: ApplicabilityStatus,
  activity: Activity,
  missing: FactCode[] = [],
): ChecklistItem {
  const regulatoryQuestions = questionsByActivity[activity.code].filter(
    (item) => item.purpose === "APPLICABILITY",
  );
  const fact = (missing[0] ?? regulatoryQuestions[index % regulatoryQuestions.length].fact_code) as FactCode;
  const unconditional = status === "APPLIES" && index === 1;
  return {
    requirement_code: `synthetic_requirement_${index}`,
    requirement_version_id: `00000000-0000-4000-8000-0000000000${String(index).padStart(2, "0")}`,
    requirement_version: 1,
    project_arabic_title: `متطلب اختباري ${index}`,
    project_arabic_description: "ملخص ملاحي من المشروع للاختبار فقط.",
    project_english_title: `Synthetic requirement ${index}`,
    project_english_description: "Project-authored navigation summary for testing only.",
    authority: {
      authority_id: "00000000-0000-4000-8000-100000000001",
      code: "synthetic_authority",
      name_ar: "جهة رسمية اختبارية",
      name_en: "Synthetic official authority",
      verification_status: "approved",
      last_verified_at: "2026-08-01T00:00:00Z",
      next_review_at: "2030-01-01T00:00:00Z",
    },
    activity_code: activity.code,
    applicability_status: status,
    reason_code: unconditional
      ? "UNCONDITIONAL_CURRENT_REQUIREMENT"
      : status === "APPLIES"
        ? "CONDITION_TRUE"
        : status === "DOES_NOT_APPLY"
          ? "CONDITION_FALSE"
          : "MISSING_REQUIRED_FACT",
    condition_result: unconditional
      ? null
      : status === "APPLIES"
        ? "TRUE"
        : status === "DOES_NOT_APPLY"
          ? "FALSE"
          : "UNKNOWN",
    missing_fact_codes: missing,
    evaluated_facts: unconditional
      ? []
      : [{
          fact_code: fact,
          question_ar: questionText[fact].ar,
          question_en: questionText[fact].en,
          supplied_value: status === "APPLIES" ? true : status === "DOES_NOT_APPLY" ? false : null,
          answer_labels: question(fact).answer_labels!,
          text_origin: "PROJECT_AUTHORED",
        }],
    condition_expression_sha256: unconditional ? null : "synthetic-test-only",
    sources: [
      {
        requirement_source_id: `00000000-0000-4000-8000-2000000000${String(index).padStart(2, "0")}`,
        source_id: "00000000-0000-4000-8000-300000000001",
        source_code: `official_source_${index}`,
        official_title_ar: `صفحة حكومية رسمية ${index}`,
        official_title_en: `Official government page ${index}`,
        source_role: "primary",
        relationship_status: "active",
        canonical_url: "https://official.example.invalid/official-source",
        canonical_host: "official.example.invalid",
        source_verification_status: "approved",
        source_last_verified_at: "2026-08-01T00:00:00Z",
        source_next_review_at: "2030-01-01T00:00:00Z",
        source_version_id: "00000000-0000-4000-8000-400000000001",
        source_version_number: 1,
        reviewed_url: "https://official.example.invalid/official-source",
        resolved_url: "https://official.example.invalid/official-source",
        source_version_review_status: "approved",
        source_version_is_current: true,
        source_version_last_verified_at: "2026-08-01T00:00:00Z",
        source_version_next_review_at: "2030-01-01T00:00:00Z",
        excerpt_locator: "Synthetic test locator",
      },
    ],
    regulatory_status: "approved",
    actionability: status === "APPLIES" ? actionabilityFor(index) : [],
  };
}

const governedSource: GovernedSourceTrace = {
  source_id: "00000000-0000-4000-8000-510000000001",
  source_code: "official_navigation_service",
  official_title_ar: "خدمة حكومية رسمية",
  official_title_en: "Official government service",
  official_url: "https://official.example.invalid/service",
  canonical_host: "official.example.invalid",
  source_version_id: "00000000-0000-4000-8000-520000000001",
  source_version_number: 1,
  authority: {
    authority_id: "00000000-0000-4000-8000-100000000001",
    code: "synthetic_authority",
    name_ar: "جهة رسمية اختبارية",
    name_en: "Synthetic official authority",
    verification_status: "approved",
    last_verified_at: "2026-08-01T00:00:00Z",
    next_review_at: "2030-01-01T00:00:00Z",
  },
  platform: {
    platform_id: "00000000-0000-4000-8000-530000000001",
    code: "official_platform",
    name_ar: "منصة حكومية رسمية",
    name_en: "Official government platform",
  },
  last_verified_at: "2026-08-01T00:00:00Z",
  next_review_at: "2030-01-01T00:00:00Z",
};

function actionabilityFor(index: number): ActionabilityItem[] {
  const values: Array<Pick<ActionabilityItem, "detail_type" | "value">> = index === 1
    ? [
        {
          detail_type: "official_start",
          value: { kind: "official_destination", label_ar: "الخدمة الرسمية", label_en: "Official service" },
        },
        {
          detail_type: "prerequisite",
          value: { kind: "text", text_ar: "تحقق من جاهزية النشاط.", text_en: "Confirm the business is ready." },
        },
        {
          detail_type: "document",
          value: { kind: "text", text_ar: "مستند رسمي اختباري.", text_en: "Synthetic official document." },
        },
        {
          detail_type: "fee",
          value: { kind: "money", amount_minor: 6000, currency: "SAR", label_ar: "60 ريالًا", label_en: "SAR 60" },
        },
        {
          detail_type: "sequence",
          value: { kind: "text", text_ar: "أرسل الطلب عبر الخدمة الرسمية.", text_en: "Submit through the official service." },
        },
      ]
    : index === 2
      ? [{
          detail_type: "fee",
          value: { kind: "money", amount_minor: 0, currency: "SAR", label_ar: "مجانًا", label_en: "Free" },
        }]
      : index === 3
        ? [{
            detail_type: "sequence",
            value: { kind: "text", text_ar: "سجّل المنشأة ضمن التسلسل الرسمي.", text_en: "Register in the official sequence." },
          }]
        : [];

  return values.map((item, itemIndex) => ({
    code: `synthetic_action_${index}_${itemIndex}`,
    actionability_version_id: `00000000-0000-4000-8000-54000000${String(index).padStart(2, "0")}${String(itemIndex).padStart(2, "0")}`,
    version_number: 1,
    requirement_version_id: `00000000-0000-4000-8000-0000000000${String(index).padStart(2, "0")}`,
    detail_type: item.detail_type,
    display_order: itemIndex + 1,
    label_ar: "تفصيل تشغيلي متحقق",
    label_en: "Verified operational detail",
    value: item.value,
    source: governedSource,
    last_verified_at: "2026-08-01T00:00:00Z",
    next_review_at: "2030-01-01T00:00:00Z",
  }));
}

const journeyTitles: Record<string, { ar: string; en: string }> = {
  ownership_investment_route: { ar: "الملكية والاستثمار", en: "Ownership and investment" },
  business_registration_route: { ar: "الشكل القانوني والتسجيل", en: "Legal form and registration" },
  site_activity_verification: { ar: "اختيار الموقع", en: "Choosing premises" },
  vat_registration_navigation: { ar: "ضريبة القيمة المضافة", en: "Value Added Tax" },
  e_invoicing_confirmation: { ar: "الفوترة الإلكترونية", en: "E-invoicing" },
  zakat_registration_confirmation: { ar: "الزكاة", en: "Zakat" },
};

function journeyGuidance(missingNavigation: NavigationFactCode[]): JourneyGuidance[] {
  const topicForFact: Partial<Record<NavigationFactCode, string>> = {
    ownership_investor_route: "ownership_investment_route",
    planned_legal_form: "business_registration_route",
    has_selected_business_premises: "site_activity_verification",
  };
  const missingTopics = new Set(missingNavigation.map((code) => topicForFact[code]));
  return Object.entries(journeyTitles).map(([topicCode, title], index) => {
    const confirmation = topicCode === "e_invoicing_confirmation" || topicCode === "zakat_registration_confirmation";
    const noRoute = missingTopics.has(topicCode) && topicCode !== "site_activity_verification";
    return {
      topic_code: topicCode,
      topic_version_id: `00000000-0000-4000-8000-5500000000${String(index).padStart(2, "0")}`,
      activity_code: "coffee_shop",
      title_ar: title.ar,
      title_en: title.en,
      coverage_state: confirmation ? "REQUIRES_OFFICIAL_CONFIRMATION" : "PARTIALLY_VERIFIED",
      verified_summary_ar: confirmation ? null : "مسار رسمي راجعه المشروع.",
      verified_summary_en: confirmation ? null : "A project-reviewed official route.",
      limitation_summary_ar: confirmation ? "لا يحدد الدليل الحالة التي تنطبق على منشأتك تلقائيًا." : "التغطية الحالية محدودة بالمسار الرسمي المتاح.",
      limitation_summary_en: confirmation ? "The Navigator does not automatically decide your business's status." : "Current coverage is limited to the available official route.",
      what_to_verify_ar: "تحقق من حالتك عبر الجهة الرسمية.",
      what_to_verify_en: "Confirm your case with the official authority.",
      routing_status: missingTopics.has(topicCode) ? "NEEDS_INFORMATION" : "ROUTED",
      destinations: noRoute ? [] : [{
        code: `${topicCode}_official_destination`,
        destination_kind: "service",
        guidance_ar: "راجع المسار الرسمي المناسب لحالتك.",
        guidance_en: "Review the official route for your case.",
        what_to_verify_ar: "تحقق من التفاصيل لدى الجهة الرسمية.",
        what_to_verify_en: "Confirm the details with the official authority.",
        is_primary: true,
        source: governedSource,
      }],
    };
  });
}

export function checklistResponse(
  activity: Activity,
  counts: { applies: number; doesNotApply: number; needs: number },
  options: { missingNavigation?: NavigationFactCode[] } = {},
): ChecklistResponse {
  const missingNavigation = options.missingNavigation ?? [];
  const applies = Array.from({ length: counts.applies }, (_, index) => checklistItem(index + 1, "APPLIES", activity));
  const doesNotApply = Array.from({ length: counts.doesNotApply }, (_, index) => checklistItem(index + 20, "DOES_NOT_APPLY", activity));
  const needs = Array.from({ length: counts.needs }, (_, index) => {
    const activityQuestions = questionsByActivity[activity.code].filter(
      (item) => item.purpose === "APPLICABILITY",
    );
    return checklistItem(index + 40, "NEEDS_INFORMATION", activity, [
      activityQuestions[index % activityQuestions.length].fact_code as FactCode,
    ]);
  });
  return {
    metadata,
    result: {
      activity,
      applies,
      does_not_apply: doesNotApply,
      needs_information: needs,
      questions_needed: questionsByActivity[activity.code]
        .filter((item) => item.purpose === "APPLICABILITY")
        .slice(0, counts.needs),
      journey_guidance: journeyGuidance(missingNavigation).map((item) => ({ ...item, activity_code: activity.code })),
      missing_navigation_information: missingNavigation.map((factCode) => ({
        fact_code: factCode,
        question: navigationQuestionByCode[factCode],
        affected_topic_codes: [
          factCode === "ownership_investor_route"
            ? "ownership_investment_route"
            : factCode === "planned_legal_form"
              ? "business_registration_route"
              : "site_activity_verification",
        ],
      })),
      coverage_notice: {
        coverage_status: "PARTIAL_VERIFIED_COVERAGE",
        message_ar: "التغطية جزئية والمجالات غير المحسومة لا تعامل كغير منطبقة.",
        message_en: "Coverage is partial; unresolved areas are not treated as not applicable.",
        unresolved_topics: ["civil_defense", "sfda", "zakat", "e_invoicing"],
        source_artifact_id: "synthetic-closeout",
        source_artifact_fingerprint: "a".repeat(64),
      },
      regulatory_snapshot: {
        catalog_mode: "INTERNAL_GOVERNED",
        migration_revision: "0005_coverage_actionability",
        catalog_fingerprint: "b".repeat(64),
        requirement_version_ids: [...applies, ...doesNotApply, ...needs].map((item) => item.requirement_version_id),
        fact_definition_ids: [],
        publication_count: 0,
      },
    },
  };
}

export function navigatorResponse(checklist: ChecklistResponse): NavigatorResponse {
  return {
    metadata,
    interpretation: {
      language: "ar",
      activity_code: checklist.result.activity.code,
      facts: [{ code: "has_employees", value: true, evidence_text: "لدي موظفين", mapping_basis: "explicit_statement" }],
      clarification_needed: false,
      clarification_targets: [],
      unsupported_or_unmapped_statements: [],
    },
    authoritative_result: checklist.result,
    explanation: {
      language: "ar",
      items: checklist.result.applies.map((item) => ({
        item,
        summary: "شرح مبسط للنتيجة الحتمية.",
        why_status: "حدد محرك القواعد هذه الحالة.",
        next_question: null,
      })),
      authoritative_coverage: checklist.result.coverage_notice,
      ai_coverage_summary: "التغطية جزئية والمجالات غير المحسومة باقية.",
    },
    clarifications: [],
    coverage_limitation: null,
    ai_error: null,
  };
}
