import type { CatalogBoundary } from "@/lib/api/types";
import type { Locale } from "@/lib/i18n";

export type PublicCatalogMode = CatalogBoundary["catalog_mode"];

export type CatalogPresentationPolicy = {
  mode: PublicCatalogMode | null;
  isPortfolioDemo: boolean;
  isGovernedCatalog: boolean;
  catalogIsSynthetic: boolean;
  authoritiesAreSynthetic: boolean;
  sourcesAreSynthetic: boolean;
  externalDestinationsAreSynthetic: boolean;
  showAuthorityRows: boolean;
  showSourceMetadata: boolean;
  text: {
    homepageNotice: string;
    footerNotice: string;
    landingChecklist: string;
    landingCoverage: string;
    questionnaireIntro: string;
    questionnaireEmptyBody: string;
    resultScopeNote: string;
    resultIntro: string;
    resultDetermined: string;
    applicableGroupExplanation: string;
    missingGroupExplanation: string;
    verificationGroupExplanation: string;
    journeyExplanation: string;
    actionabilityExplanation: string;
    missingNavigationExplanation: string;
    noApplicableExplanation: string;
    completedChecklistExplanation: string;
    coverageCompact: string;
    coverageExplanation: string;
    checklistItemsTitle: string;
    applicableItemsTemplate: string;
    notApplicableItemsTitle: string;
    noApplicableItems: string;
    noMissingInformation: string;
    noVerificationItems: string;
    answersUsed: string;
    unconditionalItem: string;
    progressBarLabel: string;
    finalInProgressCompletedTemplate: string;
    finalInProgressRemainingTemplate: string;
    finalNoApplicableTitle: string;
    finalMissingInformationTitle: string;
    finalFollowUpCompleteTitle: string;
    demoDataLink: string;
    demoLinkUnavailable: string;
    demoSourceLabel: string;
    metadata: {
      homeTitle: string;
      homeDescription: string;
      aboutTitle: string;
      aboutDescription: string;
    };
  };
};

export type PresentedSourceLink =
  | { kind: "demo-information"; href: string; label: string }
  | { kind: "governed-external"; href: string }
  | { kind: "unavailable" };

const portfolioDemoText: Record<Locale, CatalogPresentationPolicy["text"]> = {
  ar: {
    homepageNotice: "نسخة تجريبية مستقلة وليست منصة حكومية.",
    footerNotice: "يعتمد الدليل على بيانات نموذجية في النسخة التجريبية، ولا يمثل جهة حكومية.",
    landingChecklist: "استكشف قائمة نموذجية ومسار الخطوات التالية",
    landingCoverage:
      "تعرض نسخة المحفظة مسارات نموذجية للمقاهي والمطاعم والمطابخ السحابية؛ ولا تقيّم اختلافات خاصة بالمدن.",
    questionnaireIntro:
      "سنطرح عليك أسئلة قصيرة لنوضح كيف تستجيب القواعد النموذجية لإجاباتك.",
    questionnaireEmptyBody:
      "يمكنك إنشاء قائمة العرض مباشرة لأن العناصر النموذجية لا تحتاج إلى إجابات إضافية.",
    resultScopeNote:
      "هذه نسخة تجريبية تستخدم بيانات نموذجية لعرض طريقة عمل الدليل. في الاستخدام الفعلي، ترتبط المتطلبات والخطوات بالمصادر والخدمات الرسمية المناسبة.",
    resultIntro: "راجع العناصر وأكمل أي إجابة ناقصة لفهم مسار المنتج.",
    resultDetermined: "حُددت هذه القائمة بناءً على إجاباتك الحالية.",
    applicableGroupExplanation: "تظهر هذه العناصر وفق إجاباتك الحالية.",
    missingGroupExplanation: "أكمل الإجابات الناقصة حتى تظهر النتيجة الحتمية.",
    verificationGroupExplanation: "هذه الأمور خارج نسبة الإنجاز وتحتاج إلى مراجعة منفصلة.",
    journeyExplanation:
      "هذا مثال يوضح كيف يعرض الدليل أمراً يحتاج إلى تحقق إضافي.",
    actionabilityExplanation:
      "هذا مثال يوضح موضع عرض خطوات البدء والتفاصيل المساندة بعد مراجعتها.",
    missingNavigationExplanation:
      "أكمل هذه الإجابة لعرض مسار التنقل النموذجي المناسب.",
    noApplicableExplanation:
      "تعني هذه النتيجة أن البيانات النموذجية الحالية لم تُظهر عنصراً منطبقاً؛ وليست حكماً تنظيمياً.",
    completedChecklistExplanation: "وضعت علامة إنجاز على جميع مهام القائمة.",
    coverageCompact: "حدود التغطية · اعرف المزيد",
    coverageExplanation: "تعرض القائمة السيناريوهات التي تغطيها النسخة الحالية فقط.",
    checklistItemsTitle: "قائمة عناصر العرض",
    applicableItemsTemplate: "عدد العناصر النموذجية الظاهرة لهذا المشروع: {total}",
    notApplicableItemsTitle: "عناصر نموذجية لا تنطبق على إجاباتك",
    noApplicableItems: "لا توجد عناصر نموذجية منطبقة في هذا السيناريو.",
    noMissingInformation: "لا تحتاج القواعد النموذجية إلى معلومات إضافية الآن.",
    noVerificationItems: "لا توجد أمثلة إضافية للتحقق منها الآن.",
    answersUsed: "إجاباتك المرتبطة بهذا العنصر النموذجي",
    unconditionalItem: "هذا العنصر النموذجي لا يحتاج إلى سؤال إضافي في هذا المسار.",
    progressBarLabel: "تقدم إنجاز عناصر العرض",
    finalInProgressCompletedTemplate: "العناصر النموذجية المنجزة: {completed} من {total}.",
    finalInProgressRemainingTemplate: "العناصر النموذجية المتبقية: {remaining}.",
    finalNoApplicableTitle: "لم تُظهر القواعد النموذجية عنصراً منطبقاً",
    finalMissingInformationTitle:
      "أكملت متابعة العناصر الحالية، لكن قائمة العرض لم تُحدد بالكامل بعد",
    finalFollowUpCompleteTitle: "أنهيت متابعة عناصر قائمة العرض",
    demoDataLink: "عن بيانات النسخة التجريبية",
    demoLinkUnavailable: "لا تتوفر صفحة توضيحية لهذا العنصر النموذجي.",
    demoSourceLabel: "بيانات مصدر نموذجية",
    metadata: {
      homeTitle: "نسخة عرض تقنية | دليل تأسيس المنشآت",
      homeDescription:
        "نسخة عرض تقنية لدليل تأسيس المنشآت، توضح تجربة الأسئلة والقواعد الحتمية باستخدام بيانات نموذجية.",
      aboutTitle: "حول نسخة العرض | دليل تأسيس المنشآت",
      aboutDescription:
        "تعرّف على بنية نسخة العرض التقنية وبياناتها النموذجية ومنهجيتها وحدود استخدامها.",
    },
  },
  en: {
    homepageNotice: "Independent portfolio demo. Not a government service.",
    footerNotice: "This demo uses sample data and is not a government service.",
    landingChecklist: "Explore a sample checklist and next-step flow",
    landingCoverage:
      "This portfolio build demonstrates sample coffee-shop, restaurant, and cloud-kitchen paths; it does not evaluate city-specific differences.",
    questionnaireIntro:
      "We will ask a few short questions to show how the sample rules respond to your answers.",
    questionnaireEmptyBody:
      "You can build the demo checklist directly because the sample items need no extra answers.",
    resultScopeNote:
      "This portfolio demo uses sample data to demonstrate how the guide works. In a production catalog, requirements and next steps are linked to the relevant official sources and services.",
    resultIntro: "Review the items and complete missing answers to explore the product flow.",
    resultDetermined: "This checklist was determined from your current answers.",
    applicableGroupExplanation: "These items follow from your current answers.",
    missingGroupExplanation: "Complete missing answers to resolve the deterministic result.",
    verificationGroupExplanation:
      "These items are outside completion progress and need separate review.",
    journeyExplanation:
      "This example demonstrates how the guide presents an item that requires additional verification.",
    actionabilityExplanation:
      "This example demonstrates where reviewed start steps and supporting details would appear.",
    missingNavigationExplanation:
      "Complete this answer to display the relevant sample navigation path.",
    noApplicableExplanation:
      "The current sample data produced no applicable item; this is not a regulatory determination.",
    completedChecklistExplanation: "You marked all checklist tasks as complete.",
    coverageCompact: "Coverage limits · Learn more",
    coverageExplanation:
      "The checklist covers only the scenarios represented in the current version.",
    checklistItemsTitle: "Demo checklist items",
    applicableItemsTemplate: "Sample items shown for this project: {total}",
    notApplicableItemsTitle: "Sample items that do not apply to your answers",
    noApplicableItems: "No sample items apply in this scenario.",
    noMissingInformation: "The sample rules need no more information right now.",
    noVerificationItems: "There are no additional examples to verify right now.",
    answersUsed: "Your answers connected to this sample item",
    unconditionalItem: "This sample item needs no additional question in this path.",
    progressBarLabel: "Demo item completion progress",
    finalInProgressCompletedTemplate: "Completed sample items: {completed} of {total}.",
    finalInProgressRemainingTemplate: "Sample items remaining: {remaining}.",
    finalNoApplicableTitle: "The sample rules identified no applicable item",
    finalMissingInformationTitle:
      "You have followed up on the current items, but the demo checklist is not fully determined yet",
    finalFollowUpCompleteTitle: "Demo checklist follow-up complete",
    demoDataLink: "About the demo data",
    demoLinkUnavailable: "No demo-data information page is available for this sample item.",
    demoSourceLabel: "Sample source data",
    metadata: {
      homeTitle: "Technical Demo | Saudi Business Launch Navigator",
      homeDescription:
        "Technical portfolio demo of a business launch navigator using deterministic rules and sample data.",
      aboutTitle: "About the Demo | Saudi Business Launch Navigator",
      aboutDescription:
        "Learn how this technical portfolio demo uses sample data to demonstrate its architecture, methodology, and limits.",
    },
  },
};

export function configuredCatalogMode(): PublicCatalogMode | null {
  const value = process.env.NEXT_PUBLIC_CATALOG_MODE;
  if (value === "GOVERNED_REAL_CATALOG" || value === "PORTFOLIO_DEMO_CATALOG") {
    return value;
  }
  return null;
}

export function catalogBoundaryMatchesBuild(metadata: CatalogBoundary): boolean {
  const expected = configuredCatalogMode();
  if (expected === null || metadata.catalog_mode !== expected) return false;
  if (expected === "PORTFOLIO_DEMO_CATALOG") {
    return (
      metadata.publication_state === "SAMPLE_ONLY"
      && metadata.data_classification === "SYNTHETIC_PORTFOLIO_DEMO"
      && metadata.public_catalog_approved === false
    );
  }
  return (
    metadata.publication_state === "UNPUBLISHED"
    && metadata.data_classification === "PRIVATE_GOVERNED_UNPUBLISHED"
    && metadata.public_catalog_approved === false
  );
}

export function catalogPresentationPolicy(
  mode: PublicCatalogMode | null,
  locale: Locale,
): CatalogPresentationPolicy {
  const isPortfolioDemo = mode === "PORTFOLIO_DEMO_CATALOG";
  const isGovernedCatalog = mode === "GOVERNED_REAL_CATALOG";
  return {
    mode,
    isPortfolioDemo,
    isGovernedCatalog,
    catalogIsSynthetic: isPortfolioDemo,
    authoritiesAreSynthetic: isPortfolioDemo,
    sourcesAreSynthetic: isPortfolioDemo,
    externalDestinationsAreSynthetic: isPortfolioDemo,
    showAuthorityRows: isGovernedCatalog,
    showSourceMetadata: isGovernedCatalog,
    text: portfolioDemoText[locale],
  };
}

export function presentSourceLink(
  value: string,
  mode: PublicCatalogMode | null,
  locale: Locale,
): PresentedSourceLink {
  const parsed = parseSafeHttpsUrl(value);
  if (!parsed) return { kind: "unavailable" };

  if (mode === "PORTFOLIO_DEMO_CATALOG") {
    return {
      kind: "demo-information",
      href: `/${locale}/about#methodology`,
      label: portfolioDemoText[locale].demoDataLink,
    };
  }

  if (mode !== "GOVERNED_REAL_CATALOG") return { kind: "unavailable" };
  if (hasInvalidMarker(parsed)) return { kind: "unavailable" };
  return { kind: "governed-external", href: parsed.toString() };
}

export function safeOfficialUrl(value: string): string | null {
  const url = parseSafeHttpsUrl(value);
  return url && !hasInvalidMarker(url) ? url.toString() : null;
}

export function isInvalidHostname(hostname: string): boolean {
  const normalized = hostname.toLowerCase().replace(/\.$/, "");
  return normalized === "invalid" || normalized.endsWith(".invalid");
}

function parseSafeHttpsUrl(value: string): URL | null {
  try {
    const url = new URL(value);
    if (url.protocol !== "https:" || url.username || url.password) return null;
    return url;
  } catch {
    return null;
  }
}

function hasInvalidMarker(url: URL): boolean {
  return isInvalidHostname(url.hostname) || url.toString().toLowerCase().includes(".invalid");
}
