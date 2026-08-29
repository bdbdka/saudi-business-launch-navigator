import { describe, expect, it } from "vitest";

import { getDictionary, isLocale } from "@/lib/i18n";

describe("locale dictionaries", () => {
  it("provides Arabic-first product copy", () => {
    const copy = getDictionary("ar");
    expect(copy.productName).toBe("دليل تأسيس المنشآت في السعودية");
    expect(copy.productNameShort).toBe("دليل تأسيس المنشآت");
    expect(copy.heroTitle).toBe("اعرف ما تحتاج إليه لبدء مشروعك");
    expect(copy.workflow.landingChecklist).toBe("احصل على قائمة واضحة بالمتطلبات والخطوات");
    expect(copy.questionnaire.evaluate).toBe("عرض قائمتي");
    expect(copy.results.missing).toBe("نحتاج منك معلومة");
    expect(copy.results.required).toBe("ما تحتاج إليه");
    expect(copy.results.notRequired).toBe("متطلبات لا تنطبق على حالتك");
    expect(copy.results.verify).toBe("تأكد من هذه الأمور");
    expect(copy.results.introTitle).toBe("هذه قائمتك بناءً على إجاباتك");
    expect(copy.questionnaire.unknown).toBe("لست متأكدًا");
    expect(copy.workflow.checklist).toBe("شاهد ما تحتاج إليه");
    expect(copy.results.what).toBe("ما المطلوب؟");
    expect(copy.about.sourcesPrinciple).toContain("لا تعتمد على بيانات نسخة العرض");
    expect(copy.landingDisclaimer).toBe("نسخة تجريبية مستقلة وليست منصة حكومية.");
    expect(copy.footer.disclaimer).toBe(
      "يعتمد الدليل على بيانات نموذجية في النسخة التجريبية، ولا يمثل جهة حكومية.",
    );
    expect(copy.metadata.homeTitle).toBe("دليل تأسيس المنشآت في السعودية");
  });

  it("provides complete English product copy", () => {
    const copy = getDictionary("en");
    expect(copy.productName).toBe("Saudi Business Launch Navigator");
    expect(copy.productNameShort).toBe("Business Launch Guide");
    expect(copy.questionnaire.evaluate).toBe("See my checklist");
    expect(copy.results.introTitle).toBe("Your checklist based on your answers");
    expect(copy.coverage.title).toBe("Useful guidance, but not complete regulatory coverage");
    expect(copy.results.source).toBe("What is the source?");
    expect(copy.about.sourcesPrinciple).toContain("do not rely on the demo dataset");
    expect(copy.landingDisclaimer).toBe("Independent portfolio demo. Not a government service.");
    expect(copy.footer.disclaimer).toBe(
      "This demo uses sample data and is not a government service.",
    );
    expect(copy.metadata.homeTitle).toBe("Saudi Business Launch Guide");
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
