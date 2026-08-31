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
    metadata: {
      homeTitle: string;
      homeDescription: string;
      aboutTitle: string;
      aboutDescription: string;
    };
  };
};

export type PresentedSourceLink =
  | { kind: "governed-external"; href: string }
  | { kind: "unavailable" };

const portfolioDemoText: Record<Locale, CatalogPresentationPolicy["text"]> = {
  ar: {
    homepageNotice: "نسخة تجريبية مستقلة وليست منصة حكومية.",
    footerNotice: "يعتمد الدليل على بيانات نموذجية في النسخة التجريبية، ولا يمثل جهة حكومية.",
    landingChecklist: "احصل على خطوات مرتبة بناءً على إجاباتك",
    landingCoverage:
      "يركز نطاق البحث الحالي على المقاهي والمطاعم والمطابخ السحابية في الرياض وجدة. لم تُراجع بقية مدن المملكة مراجعة كاملة بعد، وهذا لا يعني أن قواعدها مختلفة ولا أن تطابقها على مستوى المملكة قد تم التحقق منه. سنضيف مدنًا أخرى بعد بحث المصادر الحكومية الرسمية والتحقق منها.",
    questionnaireIntro:
      "سنطرح عليك أسئلة قصيرة عن مشروعك. إذا لم تعرف إجابة، لا تخمّن؛ اختر «لست متأكدًا» وسنوضح ما يحتاج إلى مراجعة.",
    questionnaireEmptyBody:
      "يمكنك إنشاء قائمة خطواتك مباشرة لأن العناصر النموذجية لا تحتاج إلى إجابات إضافية.",
    resultScopeNote:
      "تعرض هذه القائمة بيانات نموذجية لشرح آلية الدليل. مرجع النشاط الرسمي أدناه مستقل ولا يثبت أن عناصر القائمة النموذجية متطلبات منشورة.",
    resultIntro: "ابدأ بالخطوات الظاهرة، وأكمل أي معلومة ناقصة، ثم راجع الأمور التي تحتاج إلى تحقق رسمي.",
    resultDetermined: "رتبنا هذه النتيجة بناءً على إجاباتك الحالية.",
    applicableGroupExplanation: "هذه الخطوات ظهرت وفق إجاباتك الحالية.",
    missingGroupExplanation: "أكمل المعلومات الناقصة حتى نحدد النتائج المرتبطة بها بدقة.",
    verificationGroupExplanation: "هذه الموضوعات خارج نسبة الإنجاز وقد تحتاج إلى مراجعة رسمية منفصلة.",
    journeyExplanation: "راجع هذا الموضوع ضمن رحلة تأسيس مشروعك قبل اتخاذ قرار نهائي.",
    actionabilityExplanation:
      "راجع خطوات البدء والتفاصيل المساندة قبل متابعة هذا الموضوع.",
    missingNavigationExplanation: "أكمل هذه الإجابة حتى نعرض لك التوجيه الأنسب.",
    noApplicableExplanation:
      "تعني هذه النتيجة أن البيانات النموذجية الحالية لم تُظهر عنصراً منطبقاً؛ وليست حكماً تنظيمياً.",
    completedChecklistExplanation: "وضعت علامة إنجاز على جميع خطوات قائمتك.",
    coverageCompact: "حدود التغطية · اعرف المزيد",
    coverageExplanation: "تعرض القائمة السيناريوهات التي تغطيها النسخة الحالية فقط.",
    checklistItemsTitle: "قائمة خطواتك",
    applicableItemsTemplate: "عدد الخطوات الظاهرة لهذا المشروع: {total}",
    notApplicableItemsTitle: "خطوات لا تنطبق على إجاباتك الحالية",
    noApplicableItems: "لا توجد خطوات منطبقة ضمن نطاق هذا السيناريو.",
    noMissingInformation: "لا نحتاج إلى معلومات إضافية الآن.",
    noVerificationItems: "لا توجد موضوعات إضافية للمراجعة الآن.",
    answersUsed: "إجاباتك المرتبطة بهذه الخطوة",
    unconditionalItem: "تظهر هذه الخطوة في مسار النشاط من دون سؤال إضافي.",
    progressBarLabel: "تقدم إنجاز خطوات القائمة",
    finalInProgressCompletedTemplate: "الخطوات التي حددتها كمنجزة: {completed} من {total}.",
    finalInProgressRemainingTemplate: "الخطوات المتبقية في قائمتك: {remaining}.",
    finalNoApplicableTitle: "لم تظهر خطوة منطبقة ضمن نطاق النسخة الحالية",
    finalMissingInformationTitle:
      "أكملت متابعة العناصر الحالية، لكن قائمة خطواتك لم تُحدد بالكامل بعد",
    finalFollowUpCompleteTitle: "أنهيت متابعة خطوات قائمتك",
    demoDataLink: "عن بيانات النسخة التجريبية",
    metadata: {
      homeTitle: "دليل تأسيس المنشآت في السعودية",
      homeDescription:
        "دليل عربي يساعدك على تنظيم خطوات بدء مقهى أو مطعم أو مطبخ سحابي من خلال أسئلة قصيرة.",
      aboutTitle: "حول دليل تأسيس المنشآت",
      aboutDescription:
        "تعرّف على هدف الدليل وطريقة عمله ومصادره وحدود النسخة التجريبية.",
    },
  },
  en: {
    homepageNotice: "Independent portfolio demo. Not a government service.",
    footerNotice: "This demo uses sample data and is not a government service.",
    landingChecklist: "Get organized steps based on your answers",
    landingCoverage:
      "The current research scope covers coffee shops, restaurants, and cloud kitchens in Riyadh and Jeddah. Other Saudi cities have not yet been fully reviewed; this neither assumes their rules differ nor claims nationwide equivalence has been verified. More cities can be added after official-source research and verification.",
    questionnaireIntro:
      "We will ask a few short questions about your business. If you do not know an answer, do not guess—choose “Not sure” and we will show what needs review.",
    questionnaireEmptyBody:
      "You can build the demo checklist directly because the sample items need no extra answers.",
    resultScopeNote:
      "This checklist uses synthetic data to demonstrate the guide. The official activity reference below is separate and does not make the sample checklist items published requirements.",
    resultIntro: "Start with the steps shown, complete any missing information, then review the topics that need official verification.",
    resultDetermined: "We organized this result from your current answers.",
    applicableGroupExplanation: "These steps appeared based on your current answers.",
    missingGroupExplanation: "Complete missing information so we can determine the related results accurately.",
    verificationGroupExplanation:
      "These items are outside completion progress and need separate review.",
    journeyExplanation: "Review this topic as part of your launch journey before making a final decision.",
    actionabilityExplanation:
      "Review the starting steps and supporting details before following up on this topic.",
    missingNavigationExplanation:
      "Complete this answer so we can show the most relevant guidance.",
    noApplicableExplanation:
      "The current sample data produced no applicable item; this is not a regulatory determination.",
    completedChecklistExplanation: "You marked all your checklist steps as complete.",
    coverageCompact: "Coverage limits · Learn more",
    coverageExplanation:
      "The checklist covers only the scenarios represented in the current version.",
    checklistItemsTitle: "Your step list",
    applicableItemsTemplate: "Steps shown for this project: {total}",
    notApplicableItemsTitle: "Steps that do not apply to your current answers",
    noApplicableItems: "No steps apply within this scenario's current scope.",
    noMissingInformation: "We do not need more information right now.",
    noVerificationItems: "There are no additional topics to review right now.",
    answersUsed: "Your answers connected to this step",
    unconditionalItem: "This step appears in the activity path without another question.",
    progressBarLabel: "Checklist step progress",
    finalInProgressCompletedTemplate: "Steps you marked complete: {completed} of {total}.",
    finalInProgressRemainingTemplate: "Steps remaining in your checklist: {remaining}.",
    finalNoApplicableTitle: "No applicable step appeared within the current scope",
    finalMissingInformationTitle:
      "You have followed up on the current items, but the demo checklist is not fully determined yet",
    finalFollowUpCompleteTitle: "You finished following up on your checklist steps",
    demoDataLink: "About the demo data",
    metadata: {
      homeTitle: "Saudi Business Launch Navigator",
      homeDescription:
        "An Arabic-first guide that organizes launch steps for coffee shops, restaurants, and cloud kitchens through a short questionnaire.",
      aboutTitle: "About | Saudi Business Launch Navigator",
      aboutDescription:
        "Learn what the guide does, how it handles sources, and the limits of the public demo.",
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
): PresentedSourceLink {
  const parsed = parseSafeHttpsUrl(value);
  if (!parsed) return { kind: "unavailable" };

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
