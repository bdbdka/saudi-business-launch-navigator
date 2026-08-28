export type Locale = "ar" | "en";
export type ActivityCode = "coffee_shop" | "restaurant" | "cloud_kitchen";
export type FactCode =
  | "has_food_establishment_workers"
  | "zatca_confirmed_mandatory_vat_registration_applies"
  | "has_employees"
  | "gosi_coverage_conditions_met"
  | "offers_home_delivery"
  | "uses_public_sidewalk_for_customer_service";
export type NavigationFactCode =
  | "ownership_investor_route"
  | "planned_legal_form"
  | "has_selected_business_premises";
export type QuestionFactCode = FactCode | NavigationFactCode;
export type OwnershipInvestorRoute =
  | "saudi_person_or_saudi_owned_entity"
  | "gcc_person_or_wholly_gcc_owned_entity"
  | "foreign_legal_entity_or_mixed_foreign_ownership"
  | "premium_residency_individual"
  | "other";
export type PlannedLegalForm =
  | "individual_establishment"
  | "limited_liability_company"
  | "other";
export type ApplicabilityStatus = "APPLIES" | "DOES_NOT_APPLY" | "NEEDS_INFORMATION";
export type FactAnswers = Partial<Record<FactCode, boolean | null>>;
export type NavigationAnswers = {
  ownership_investor_route?: OwnershipInvestorRoute | null;
  planned_legal_form?: PlannedLegalForm | null;
  has_selected_business_premises?: boolean | null;
};
export type QuestionnaireAnswers = Partial<
  Record<QuestionFactCode, boolean | string | null>
>;

export interface CatalogBoundary {
  catalog_mode: "GOVERNED_REAL_CATALOG" | "PORTFOLIO_DEMO_CATALOG";
  publication_state: "UNPUBLISHED" | "SAMPLE_ONLY";
  data_classification: "PRIVATE_GOVERNED_UNPUBLISHED" | "SYNTHETIC_PORTFOLIO_DEMO";
  public_catalog_approved: false;
  warning_ar: string;
  warning_en: string;
}

export interface Activity {
  code: ActivityCode;
  name_ar: string;
  name_en: string;
}

export interface ActivitiesResponse {
  metadata: CatalogBoundary;
  activities: Activity[];
}

export interface BooleanAnswerLabels {
  true_ar: string;
  true_en: string;
  false_ar: string;
  false_en: string;
  unknown_ar: string;
  unknown_en: string;
}

export interface Question {
  fact_code: QuestionFactCode;
  fact_version: number;
  data_type: "boolean" | "enum";
  purpose: "APPLICABILITY" | "NAVIGATION";
  allows_unknown: boolean;
  question_ar: string;
  question_en: string;
  help_text_ar: string;
  help_text_en: string;
  answer_labels: BooleanAnswerLabels | null;
  options: Array<{ value: string; label_ar: string; label_en: string }>;
  unknown_label_ar: string;
  unknown_label_en: string;
  text_origin: "PROJECT_AUTHORED";
}

export interface QuestionnaireResponse {
  metadata: CatalogBoundary;
  questionnaire: {
    activity: Activity;
    questions: Question[];
  };
}

export interface AuthorityTrace {
  authority_id: string;
  code: string;
  name_ar: string;
  name_en: string | null;
  verification_status: string;
  last_verified_at: string | null;
  next_review_at: string | null;
}

export interface SourceTrace {
  requirement_source_id: string;
  source_id: string;
  source_code: string;
  official_title_ar: string | null;
  official_title_en: string | null;
  source_role: string;
  relationship_status: string;
  canonical_url: string;
  canonical_host: string;
  source_verification_status: string;
  source_last_verified_at: string | null;
  source_next_review_at: string | null;
  source_version_id: string;
  source_version_number: number;
  reviewed_url: string;
  resolved_url: string;
  source_version_review_status: string;
  source_version_is_current: boolean;
  source_version_last_verified_at: string | null;
  source_version_next_review_at: string | null;
  excerpt_locator: string | null;
}

export interface EvaluatedFactTrace {
  fact_code: FactCode;
  question_ar: string;
  question_en: string;
  supplied_value: boolean | null;
  answer_labels: BooleanAnswerLabels;
  text_origin: "PROJECT_AUTHORED";
}

export interface ChecklistItem {
  requirement_code: string;
  requirement_version_id: string;
  requirement_version: number;
  project_arabic_title: string;
  project_arabic_description: string;
  project_english_title: string | null;
  project_english_description: string | null;
  authority: AuthorityTrace;
  activity_code: ActivityCode;
  applicability_status: ApplicabilityStatus;
  reason_code:
    | "UNCONDITIONAL_CURRENT_REQUIREMENT"
    | "CONDITION_TRUE"
    | "CONDITION_FALSE"
    | "MISSING_REQUIRED_FACT";
  condition_result: "TRUE" | "FALSE" | "UNKNOWN" | null;
  missing_fact_codes: FactCode[];
  evaluated_facts: EvaluatedFactTrace[];
  condition_expression_sha256: string | null;
  sources: SourceTrace[];
  regulatory_status: string;
  actionability: ActionabilityItem[];
}

export interface GovernedSourceTrace {
  source_id: string;
  source_code: string;
  official_title_ar: string | null;
  official_title_en: string | null;
  official_url: string;
  canonical_host: string;
  source_version_id: string;
  source_version_number: number;
  authority: AuthorityTrace;
  platform: {
    platform_id: string;
    code: string;
    name_ar: string;
    name_en: string | null;
  } | null;
  last_verified_at: string;
  next_review_at: string;
}

export type ActionabilityValue =
  | { kind: "official_destination"; label_ar: string; label_en: string | null }
  | { kind: "text"; text_ar: string; text_en: string | null }
  | {
      kind: "money";
      amount_minor: number;
      currency: "SAR";
      label_ar: string;
      label_en: string | null;
    };

export interface ActionabilityItem {
  code: string;
  actionability_version_id: string;
  version_number: number;
  requirement_version_id: string;
  detail_type: string;
  display_order: number;
  label_ar: string;
  label_en: string;
  value: ActionabilityValue;
  source: GovernedSourceTrace;
  last_verified_at: string;
  next_review_at: string;
}

export interface JourneyGuidance {
  topic_code: string;
  topic_version_id: string;
  activity_code: ActivityCode;
  title_ar: string;
  title_en: string | null;
  coverage_state:
    | "VERIFIED"
    | "PARTIALLY_VERIFIED"
    | "REQUIRES_OFFICIAL_CONFIRMATION"
    | "UNRESOLVED";
  verified_summary_ar: string | null;
  verified_summary_en: string | null;
  limitation_summary_ar: string | null;
  limitation_summary_en: string | null;
  what_to_verify_ar: string | null;
  what_to_verify_en: string | null;
  routing_status: "ROUTED" | "NEEDS_INFORMATION";
  destinations: Array<{
    code: string;
    destination_kind: string;
    guidance_ar: string;
    guidance_en: string | null;
    what_to_verify_ar: string;
    what_to_verify_en: string | null;
    is_primary: boolean;
    source: GovernedSourceTrace;
  }>;
}

export interface CoverageNotice {
  coverage_status: "PARTIAL_VERIFIED_COVERAGE";
  message_ar: string;
  message_en: string;
  unresolved_topics: string[];
  source_artifact_id: string;
  source_artifact_fingerprint: string;
}

export interface ChecklistResult {
  activity: Activity;
  applies: ChecklistItem[];
  does_not_apply: ChecklistItem[];
  needs_information: ChecklistItem[];
  questions_needed: Question[];
  journey_guidance: JourneyGuidance[];
  missing_navigation_information: Array<{
    fact_code: NavigationFactCode;
    question: Question;
    affected_topic_codes: string[];
  }>;
  coverage_notice: CoverageNotice;
  regulatory_snapshot: {
    catalog_mode: "INTERNAL_GOVERNED" | "PORTFOLIO_DEMO";
    migration_revision: string;
    catalog_fingerprint: string;
    requirement_version_ids: string[];
    fact_definition_ids: string[];
    publication_count: number;
  };
}

export interface ChecklistResponse {
  metadata: CatalogBoundary;
  result: ChecklistResult;
}

export interface ValidatedInterpretation {
  language: Locale;
  activity_code: ActivityCode | null;
  facts: Array<{
    code: FactCode;
    value: boolean;
    evidence_text: string;
    mapping_basis: "explicit_statement" | "direct_semantic_equivalent";
  }>;
  clarification_needed: boolean;
  clarification_targets: string[];
  unsupported_or_unmapped_statements: string[];
}

export interface NavigatorResponse {
  metadata: CatalogBoundary;
  interpretation: ValidatedInterpretation;
  authoritative_result: ChecklistResult | null;
  explanation: {
    language: Locale;
    items: Array<{
      item: ChecklistItem;
      summary: string;
      why_status: string;
      next_question: Question | null;
    }>;
    authoritative_coverage: CoverageNotice;
    ai_coverage_summary: string;
  } | null;
  clarifications: Array<{
    target: string;
    question_ar: string;
    question_en: string;
    project_authored: true;
  }>;
  coverage_limitation: {
    unresolved_topics: string[];
    message_ar: string;
    message_en: string;
    supported_determination: false;
  } | null;
  ai_error: { code: string; message: string } | null;
}

export interface APIErrorEnvelope {
  error: {
    code: string;
    message: string;
    details: Array<{ field: string; error_type: string }>;
    request_id: string | null;
  };
}
