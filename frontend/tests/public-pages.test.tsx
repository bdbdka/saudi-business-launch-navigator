import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AboutPage } from "@/components/about-page";
import {
  NotFoundContent,
  RouteError,
  RouteLoading,
  localeFromPath,
} from "@/components/route-feedback";
import { getDictionary } from "@/lib/i18n";

describe("localized public information pages", () => {
  it("explains the Arabic guide, scope, methodology, privacy, and limits in plain language", () => {
    const { container } = render(<AboutPage locale="ar" copy={getDictionary("ar")} />);

    expect(screen.getByRole("heading", { level: 1, name: "حول دليل تأسيس المنشآت" })).toBeInTheDocument();
    for (const heading of [
      "ما هو دليل تأسيس المنشآت؟",
      "كيف يعمل؟",
      "من أين تأتي المعلومات؟",
      "ما الذي لا يفعله الدليل؟",
      "هل الدليل منصة حكومية؟",
      "ما الأنشطة المدعومة حاليًا؟",
      "منهجية الدليل",
      "ماذا يحدث لإجاباتي؟",
    ]) {
      expect(screen.getByRole("heading", { level: 2, name: heading })).toBeInTheDocument();
    }

    const supported = screen.getByRole("heading", { name: "ما الأنشطة المدعومة حاليًا؟" }).closest("section")!;
    expect(within(supported).getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      "مقهى",
      "مطعم",
      "مطبخ سحابي",
    ]);

    const how = screen.getByRole("heading", { name: "كيف يعمل؟" }).closest("section")!;
    expect(within(how).getAllByRole("listitem")).toHaveLength(4);
    expect(how).toHaveTextContent("راجع الأدلة ومعلومات التوجيه المعروضة");
    expect(how).toHaveTextContent("العناصر التي تنطبق");
    expect(how).toHaveTextContent("المعلومات التي ما زلنا نحتاجها");
    expect(how).toHaveTextContent("الأمور التي يجب مراجعتها");
    expect(how).toHaveTextContent("المتطلبات السابقة والمستندات والرسوم والخطوات");

    const methodology = screen.getByRole("heading", { name: "منهجية الدليل" }).closest("section")!;
    expect(methodology).toHaveAttribute("id", "methodology");
    expect(methodology).toHaveTextContent("بيانات نموذجية فقط");
    expect(methodology).toHaveTextContent("النص العربي الرسمي المرجع الأساسي");
    expect(methodology).toHaveTextContent("لا تنشر نسخة العرض البحث التنظيمي الخاص المحكوم");

    const privacy = screen.getByRole("heading", { name: "ماذا يحدث لإجاباتي؟" }).closest("section")!;
    expect(privacy).toHaveAttribute("id", "privacy");
    expect(privacy).toHaveTextContent("لا تحتاج إلى إنشاء حساب");
    expect(privacy).toHaveTextContent("ذاكرة الصفحة فقط");
    expect(privacy).toHaveTextContent("لا يستخدم هذا الإصدار التخزين المحلي أو ملفات تعريف الارتباط");
    expect(privacy).toHaveTextContent("يُرسل النص عند اختيارك الإرسال فقط");
    expect(privacy).toHaveTextContent("سياسة خصوصية الجهة");

    expect(container).toHaveTextContent("هذا مشروع مستقل غير تابع لأي جهة حكومية ولا يمثلها");
    expect(container).toHaveTextContent("لا تعتمد على بيانات نسخة العرض");
    expect(container).toHaveTextContent("لا يقدم استشارة قانونية");
    expect(container).toHaveTextContent("لا يحسب وضعك الضريبي تلقائيًا");
    expect(container).toHaveTextContent("لا يحسم مسألة عندما لا تكفي الأدلة الرسمية");
    expect(container).toHaveTextContent("قد تتغير الأنظمة والخدمات");
    expect(container.textContent).not.toMatch(
      /deterministic engine|Pydantic|PostgreSQL|rule evaluator|APPLIES|NEEDS_INFORMATION|UUID/i,
    );
  });

  it("provides the same public explanation and locale-safe navigation in English", () => {
    const { container } = render(<AboutPage locale="en" copy={getDictionary("en")} />);

    expect(screen.getByRole("heading", { level: 1, name: "About the Business Launch Guide" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Where does the information come from?" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "What does the guide not do?" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "What happens to my answers?" })).toBeInTheDocument();

    const primaryNavigation = screen.getByRole("navigation", { name: "Primary navigation" });
    expect(within(primaryNavigation).getByRole("link", { name: "Home" })).toHaveAttribute("href", "/en");
    expect(within(primaryNavigation).getByRole("link", { name: "About" })).toHaveAttribute(
      "href",
      "/en/about",
    );
    expect(within(primaryNavigation).getByRole("link", { name: "Switch to Arabic" })).toHaveAttribute(
      "href",
      "/ar/about",
    );
    expect(screen.getByRole("link", { name: "Back to the guide" })).toHaveAttribute("href", "/en");
    expect(container).toHaveTextContent("not a government service");
    expect(container).toHaveTextContent("not affiliated with or representative of any government authority");
    expect(container).toHaveTextContent("does not publish the private governed regulatory research");
    expect(container).toHaveTextContent("does not issue licences for you, guarantee approval");
  });

  it("links the minimal footer to the localized About, Methodology, and Privacy sections", () => {
    render(<AboutPage locale="ar" copy={getDictionary("ar")} />);

    const footer = screen.getByRole("contentinfo");
    const footerNavigation = within(footer).getByRole("navigation", { name: "حدود استخدام الدليل" });
    expect(within(footerNavigation).getByRole("link", { name: "الرئيسية" })).toHaveAttribute(
      "href",
      "/ar",
    );
    expect(within(footerNavigation).getByRole("link", { name: "حول الدليل" })).toHaveAttribute(
      "href",
      "/ar/about",
    );
    expect(within(footerNavigation).getByRole("link", { name: "المنهجية" })).toHaveAttribute(
      "href",
      "/ar/about#methodology",
    );
    expect(within(footerNavigation).getByRole("link", { name: "الخصوصية" })).toHaveAttribute(
      "href",
      "/ar/about#privacy",
    );
    expect(footer).toHaveTextContent(
      "يعتمد الدليل على بيانات نموذجية في النسخة التجريبية، ولا يمثل جهة حكومية.",
    );
  });
});

describe("localized route feedback", () => {
  it("renders honest Arabic and English loading states", () => {
    const { rerender } = render(<RouteLoading locale="ar" />);
    expect(screen.getByRole("status")).toHaveTextContent("جارٍ تحميل الدليل");

    rerender(<RouteLoading locale="en" />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading the guide");
  });

  it("renders a sanitized error state and invokes only the supplied retry callback", async () => {
    const reset = vi.fn();
    render(<RouteError locale="en" reset={reset} />);

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("The page could not be loaded");
    expect(alert).toHaveTextContent("No substitute or assumed information has been shown");
    expect(alert).not.toHaveTextContent("stack");
    expect(within(alert).getByRole("link", { name: "Back to the guide" })).toHaveAttribute("href", "/en");

    await userEvent.click(within(alert).getByRole("button", { name: "Try again" }));
    expect(reset).toHaveBeenCalledTimes(1);
  });

  it("renders localized 404 actions without calling the application API", () => {
    const { rerender } = render(<NotFoundContent locale="ar" />);
    expect(screen.getByRole("heading", { name: "الصفحة غير موجودة" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "العودة إلى الدليل" })).toHaveAttribute("href", "/ar");
    expect(screen.getByRole("link", { name: "حول الدليل" })).toHaveAttribute("href", "/ar/about");

    rerender(<NotFoundContent locale="en" />);
    expect(screen.getByRole("heading", { name: "Page not found" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to the guide" })).toHaveAttribute("href", "/en");
    expect(screen.getByRole("link", { name: "About this guide" })).toHaveAttribute("href", "/en/about");
  });

  it("derives only the supported locale from a route path", () => {
    expect(localeFromPath("/en/about")).toBe("en");
    expect(localeFromPath("/en")).toBe("en");
    expect(localeFromPath("/ar/about")).toBe("ar");
    expect(localeFromPath("/unexpected")).toBe("ar");
    expect(localeFromPath(null)).toBe("ar");
  });
});
