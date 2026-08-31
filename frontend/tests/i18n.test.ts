import { describe, expect, it } from "vitest";

import { getDictionary, isLocale } from "@/lib/i18n";

describe("locale dictionaries", () => {
  it("provides Arabic-first product copy", () => {
    const copy = getDictionary("ar");
    expect(copy.productName).toBe("دليل تأسيس المنشآت في السعودية");
    expect(copy.productNameShort).toBe("دليل تأسيس المنشآت");
    expect(copy.heroTitle).toBe("اعرف خطوات تأسيس مشروعك بوضوح");
    expect(copy.purpose.title).toBe("لماذا أنشأنا هذا الدليل؟");
    expect(copy.purpose.body).toContain("تنظيمها حول وضع مشروعك الفعلي");
    expect(copy.beforeStart.title).toBe("قبل أن نبدأ");
    expect(copy.beforeStart.items).toEqual([
      "خطوات تبدأ بها",
      "معلومات نحتاج معرفتها منك",
      "أمور تراجعها رسميًا",
    ]);
    expect(copy.workflow.landingChecklist).toBe("احصل على قائمة واضحة بالمتطلبات والخطوات");
    expect(copy.activities.title).toBe("اختر النشاط الأقرب لمشروعك");
    expect(copy.activities.start).toBe("ابدأ الأسئلة");
    expect(copy.activities.descriptions.cloud_kitchen).toContain("من دون صالة جلوس");
    expect(copy.questionnaire.evaluate).toBe("عرض النتيجة");
    expect(copy.questionnaire.intro).toContain("لا تخمّن");
    expect(copy.questionnaire.intro).toContain("لست متأكدًا");
    expect([
      copy.questionnaire.meaningLabel,
      copy.questionnaire.whyLabel,
      copy.questionnaire.exampleLabel,
    ]).toEqual(["ما المقصود؟", "لماذا نسألك؟", "مثال بسيط"]);
    expect(copy.results.missing).toBe("نحتاج منك معلومة");
    expect(copy.results.required).toBe("ابدأ بهذه الخطوات");
    expect(copy.results.notRequired).toBe("خطوات لا تنطبق على إجاباتك الحالية");
    expect(copy.results.verify).toBe("راجع هذه الأمور");
    expect(copy.results.introTitle).toBe("رتبنا لك النتيجة بناءً على إجاباتك");
    expect(copy.results.activityReferenceTitle).toBe("المصدر الرسمي للنشاط");
    expect(copy.results.openActivityReference).toBe("فتح صفحة النشاط الرسمية");
    expect(copy.questionnaire.unknown).toBe("لست متأكدًا");
    expect(copy.workflow.checklist).toBe("شاهد ما تحتاج إليه");
    expect(copy.results.what).toBe("ما المطلوب؟");
    expect(copy.about.problemTitle).toBe("ما المشكلة التي يحاول حلها؟");
    expect(copy.about.futureTitle).toBe("كيف يمكن أن يتطور الدليل؟");
    expect(copy.about.futureIntro).toContain("رؤية مستقبلية وليست ميزات متاحة الآن");
    expect(copy.about.sourcesPrinciple).toContain("لا تعتمد على بيانات نسخة العرض");
    expect(copy.landingDisclaimer).toBe("نسخة تجريبية مستقلة وليست منصة حكومية.");
    expect(copy.footer.disclaimer).toBe(
      "يعتمد الدليل على بيانات نموذجية في النسخة التجريبية، ولا يمثل جهة حكومية.",
    );
    expect(copy.metadata.homeTitle).toBe("دليل تأسيس المنشآت في السعودية");

    expect(JSON.stringify(copy)).not.toMatch(
      /نسخة عرض تقنية|نسخة المحفظة|القواعد الحتمية|البنية المحكومة|مسار المنتج/,
    );
  });

  it("provides complete English product copy", () => {
    const copy = getDictionary("en");
    expect(copy.productName).toBe("Saudi Business Launch Navigator");
    expect(copy.productNameShort).toBe("Business Launch Guide");
    expect(copy.heroTitle).toBe("Understand your business-launch steps clearly");
    expect(copy.purpose.title).toBe("Why does this guide exist?");
    expect(copy.beforeStart.items).toEqual([
      "Steps you can start",
      "Information we need from you",
      "Things to review officially",
    ]);
    expect(copy.activities.title).toBe("Choose the activity closest to your business");
    expect(copy.activities.start).toBe("Start questions");
    expect(copy.activities.descriptions.cloud_kitchen).toContain("without a customer dining room");
    expect(copy.questionnaire.evaluate).toBe("Show results");
    expect(copy.questionnaire.intro).toContain("do not guess");
    expect(copy.questionnaire.intro).toContain("Not sure");
    expect([
      copy.questionnaire.meaningLabel,
      copy.questionnaire.whyLabel,
      copy.questionnaire.exampleLabel,
    ]).toEqual(["What does this mean?", "Why do we ask?", "Simple example"]);
    expect(copy.results.introTitle).toBe("We organized this result from your answers");
    expect(copy.results.required).toBe("Start with these steps");
    expect(copy.results.activityReferenceTitle).toBe("Official activity reference");
    expect(copy.results.openActivityReference).toBe("Open official activity page");
    expect(copy.coverage.title).toBe("Useful guidance, but not complete regulatory coverage");
    expect(copy.results.source).toBe("What is the source?");
    expect(copy.about.problemTitle).toBe("What problem does it address?");
    expect(copy.about.futureTitle).toBe("How could the guide evolve?");
    expect(copy.about.futureIntro).toContain("future vision, not a list of features available today");
    expect(copy.about.sourcesPrinciple).toContain("do not rely on the demo dataset");
    expect(copy.landingDisclaimer).toBe("Independent portfolio demo. Not a government service.");
    expect(copy.footer.disclaimer).toBe(
      "This demo uses sample data and is not a government service.",
    );
    expect(copy.metadata.homeTitle).toBe("Saudi Business Launch Guide");

    expect(JSON.stringify(copy)).not.toMatch(
      /technical demo|portfolio build|sample rules|deterministic result|governed architecture/i,
    );
  });

  it("keeps the complete Arabic and English dictionary structures in sync", () => {
    expect(keyShape(getDictionary("ar"))).toEqual(keyShape(getDictionary("en")));
  });

  it("accepts only the two route locales", () => {
    expect(isLocale("ar")).toBe(true);
    expect(isLocale("en")).toBe(true);
    expect(isLocale("fr")).toBe(false);
  });
});

function keyShape(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(keyShape);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, nested]) => [key, keyShape(nested)]),
    );
  }
  return typeof value;
}
