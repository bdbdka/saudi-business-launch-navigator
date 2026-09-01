import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NavigatorApp } from "@/components/navigator-app";
import { NavigatorAPIError, navigatorAPI } from "@/lib/api/client";
import {
  activities,
  activitiesResponse,
  checklistResponse,
  navigatorResponse,
  questionnaireResponse,
  questionsByActivity,
} from "@/tests/fixtures";

vi.mock("@/lib/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/client")>("@/lib/api/client");
  return {
    ...actual,
    navigatorAPI: {
      warm: vi.fn(),
      activities: vi.fn(),
      questionnaire: vi.fn(),
      checklist: vi.fn(),
      navigate: vi.fn(),
    },
  };
});

const api = vi.mocked(navigatorAPI);

beforeEach(() => {
  vi.clearAllMocks();
  api.warm.mockResolvedValue();
  api.activities.mockResolvedValue(activitiesResponse);
  api.questionnaire.mockImplementation(async (code) => {
    const activity = activities.find((item) => item.code === code);
    if (!activity) throw new Error("test fixture activity missing");
    return questionnaireResponse(activity);
  });
  api.checklist.mockResolvedValue(checklistResponse(activities[1], { applies: 7, doesNotApply: 0, needs: 0 }));
});

async function startAndSelect(activityName: string) {
  const user = userEvent.setup();
  await waitFor(() => expect(api.activities).toHaveBeenCalled());
  await user.click(await screen.findByRole("button", {
    name: (accessibleName) => accessibleName.startsWith(activityName),
  }));
  await user.click(screen.getByRole("button", { name: "ابدأ الأسئلة" }));
  await screen.findByText("من سيملك المشروع؟");
  for (const label of [
    "فرد سعودي أو منشأة مملوكة سعودياً",
    "مؤسسة فردية",
    "نعم",
  ]) {
    await user.click(screen.getByRole("button", { name: label }));
    await user.click(screen.getByRole("button", { name: "التالي" }));
  }
  await screen.findByText("هل ستوظف المنشأة موظفين أو عمالًا؟");
  return user;
}

async function answerSequence(labels: string[]) {
  const user = userEvent.setup();
  for (let index = 0; index < labels.length; index += 1) {
    await user.click(screen.getByRole("button", { name: labels[index] }));
    await user.click(screen.getByRole("button", { name: index === labels.length - 1 ? "عرض النتيجة" : "التالي" }));
  }
}

describe("Arabic-first simplified shell", () => {
  it("keeps demo disclosure concise across homepage, questionnaire, and results", async () => {
    vi.stubEnv("NEXT_PUBLIC_CATALOG_MODE", "PORTFOLIO_DEMO_CATALOG");
    const demoMetadata = {
      catalog_mode: "PORTFOLIO_DEMO_CATALOG",
      publication_state: "SAMPLE_ONLY",
      data_classification: "SYNTHETIC_PORTFOLIO_DEMO",
      public_catalog_approved: false,
      warning_ar: "نسخة تجريبية ببيانات نموذجية ولا تستخدم لقرار تنظيمي.",
      warning_en: "Portfolio demo with sample data; not for regulatory decisions.",
    } as const;
    api.activities.mockResolvedValue({
      ...activitiesResponse,
      metadata: demoMetadata,
    });
    api.questionnaire.mockImplementation(async (code) => {
      const activity = activities.find((item) => item.code === code)!;
      return { ...questionnaireResponse(activity), metadata: demoMetadata };
    });
    api.checklist.mockResolvedValue({
      ...checklistResponse(activities[1], { applies: 7, doesNotApply: 0, needs: 0 }),
      metadata: demoMetadata,
    });
    render(<NavigatorApp initialLocale="ar" />);

    await waitFor(() => expect(api.activities).toHaveBeenCalled());
    expect(screen.getByText("نسخة تجريبية مستقلة وليست منصة حكومية.")).toBeInTheDocument();
    expect(screen.getByText("احصل على خطوات مرتبة بناءً على إجاباتك")).toBeInTheDocument();
    expect(screen.getByText(/تغطي النسخة الحالية المقاهي والمطاعم والمطابخ السحابية/)).toBeInTheDocument();
    expect(screen.queryByText(/النطاق الحالي هو المقاهي/)).not.toBeInTheDocument();
    expect(screen.queryByText(demoMetadata.warning_ar)).not.toBeInTheDocument();
    expect(screen.queryByTestId("portfolio-demo-notice")).not.toBeInTheDocument();

    await startAndSelect("مقهى");
    expect(screen.queryByText("نسخة تجريبية مستقلة وليست منصة حكومية.")).not.toBeInTheDocument();
    expect(screen.queryByText(demoMetadata.warning_ar)).not.toBeInTheDocument();
    expect(screen.getAllByText("يعتمد الدليل على بيانات نموذجية في النسخة التجريبية، ولا يمثل جهة حكومية.")).toHaveLength(1);

    await answerSequence(["نعم", "نعم", "نعم", "تأكدت عبر الهيئة أنه إلزامي"]);
    await screen.findByRole("heading", { level: 1, name: "خطوات بدء مشروعك" });
    expect(screen.getAllByTestId("demo-result-scope-note")).toHaveLength(1);
    expect(screen.getByTestId("demo-result-scope-note")).toHaveTextContent(
      "تستخدم هذه النسخة بيانات نموذجية لشرح طريقة عمل الدليل، ولا تمثل خطوات القائمة متطلبات رسمية منشورة. راجع مرجع النشاط الرسمي أدناه للمعلومات المنشورة عن النشاط.",
    );
    expect(
      screen.getByRole("heading", { name: "رتّبنا لك الخطوات بناءً على إجاباتك" }).compareDocumentPosition(
        screen.getByTestId("demo-result-scope-note"),
      ) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(screen.getByText("تقدمك في خطوات القائمة")).toBeInTheDocument();
    const activityReference = screen.getByTestId("activity-official-reference");
    expect(within(activityReference).getByRole("heading", { name: "المصدر الرسمي للنشاط" })).toBeInTheDocument();
    expect(activityReference).toHaveTextContent("وزارة البلديات والإسكان — منصة بلدي");
    const officialActivityLink = within(activityReference).getByRole("link", {
      name: /فتح صفحة النشاط الرسمية/,
    });
    expect(officialActivityLink).toHaveAttribute(
      "href",
      "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=1770",
    );
    expect(officialActivityLink).toHaveAttribute("target", "_blank");
    expect(officialActivityLink).toHaveAttribute("rel", "noopener noreferrer");
    expect(screen.getAllByRole("link", { name: "عن بيانات النسخة التجريبية" })).toHaveLength(1);
    expect(screen.getByRole("link", { name: "عن بيانات النسخة التجريبية" })).toHaveAttribute(
      "href",
      "/ar/about#methodology",
    );
    expect(screen.getByText("لا نحتاج إلى إجابة إضافية لتحديد الخطوات الآن.")).toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: "تقدم إنجاز خطوات القائمة" })).toBeInTheDocument();
    const outcome = screen.getByRole("region", { name: "ما زالت لديك خطوات لم تحددها كمنجزة" });
    expect(within(outcome).getByText(
      "وضعت علامة إنجاز على ٠ من أصل ٧ خطوة.",
    )).toBeInTheDocument();
    expect(within(outcome.querySelector(".final-outcome-state")!).queryByText(
      "وضعت علامة إنجاز على ٠ من أصل ٧ خطوة.",
    )).not.toBeInTheDocument();
    expect(screen.queryByText(/متطلبات تنطبق على مشروعك/)).not.toBeInTheDocument();
    expect(screen.queryByText("جهة افتراضية")).not.toBeInTheDocument();
    expect(screen.queryByText("جهة رسمية اختبارية")).not.toBeInTheDocument();
    expect(screen.queryByText(/صفحة حكومية رسمية/)).not.toBeInTheDocument();
    expect(screen.queryByText("هذا مثال يوضح كيف يعرض الدليل أمراً يحتاج إلى تحقق إضافي.")).not.toBeInTheDocument();
    expect(document.querySelectorAll(".requirement-item a[href]")).toHaveLength(0);
    expect(document.querySelectorAll(".actionability-details a[href]")).toHaveLength(0);
    expect(document.querySelectorAll(".verification-list a[href]")).toHaveLength(0);
    expect(document.querySelectorAll('a[href*=".invalid"]')).toHaveLength(0);
    expect(document.querySelectorAll('a[href*="official.example.gov.sa"]')).toHaveLength(0);
    expect(document.querySelectorAll('a[href^="https://"]')).toHaveLength(1);
    const completionBoxes = screen.getAllByRole("checkbox", { name: /أنجزت هذه الخطوة/ });
    for (const checkbox of completionBoxes) await userEvent.click(checkbox);
    expect(screen.getByRole("region", { name: "حددت جميع خطوات القائمة كمنجزة" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Switch to English" }));
    expect(screen.getByRole("region", { name: "You finished following up on the checklist steps" })).toBeInTheDocument();
    expect(screen.getByText("We do not need another answer to select the steps right now.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Official activity reference" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Open official activity page/ })).toHaveAttribute(
      "href",
      "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=1770",
    );
    expect(screen.getAllByRole("link", { name: "About the demo data" })).toHaveLength(1);
    expect(screen.queryByText(/checklist requirements remaining/i)).not.toBeInTheDocument();
    expect(document.querySelector('a[href*=".invalid"]')).not.toBeInTheDocument();
  });

  it("renders the focused Arabic landing page with activities as the immediate action", async () => {
    render(<NavigatorApp initialLocale="ar" />);
    expect(screen.getByRole("link", { name: "دليل تأسيس المنشآت في السعودية" })).toHaveTextContent("دليل تأسيس المنشآت");
    expect(screen.getByRole("link", { name: "دليل تأسيس المنشآت في السعودية" })).toHaveAttribute("href", "/ar");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("اعرف خطوات تأسيس مشروعك بوضوح");
    expect(screen.getByText(/أجب عن أسئلة قصيرة عن مشروعك/)).toBeInTheDocument();
    const stages = screen.getByRole("list", { name: "ثلاث خطوات بسيطة" });
    expect(within(stages).getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      "اختر نشاطك",
      "أجب عن أسئلة قصيرة",
      "احصل على قائمة واضحة بالمتطلبات والخطوات",
    ]);
    expect(
      screen.getByText(
        "تغطي النسخة الحالية المقاهي والمطاعم والمطابخ السحابية في جدة والرياض فقط. لم نراجع بعد المتطلبات المحلية لبقية مدن المملكة، لذلك لا نفترض أن النتائج تنطبق عليها تلقائيًا. وإذا وُجدت فروقات محلية، فلن نعرضها إلا بعد التحقق من مصدر رسمي.",
      ),
    ).toBeInTheDocument();
    const coffeeShop = await screen.findByRole("button", { name: "مقهى" });
    expect(coffeeShop).toBeInTheDocument();
    expect(coffeeShop).not.toHaveAttribute("aria-describedby");
    expect(document.querySelector(".activity-description")).not.toBeInTheDocument();
    expect(document.querySelector(".activity-secondary-name")).not.toBeInTheDocument();
    expect(document.querySelector(".activity-guidance-label")).not.toBeInTheDocument();
    expect(screen.getByText("نسخة تجريبية مستقلة وليست منصة حكومية.")).toBeInTheDocument();
    await waitFor(() => expect(document.documentElement).toHaveAttribute("dir", "rtl"));
    expect(document.documentElement).toHaveAttribute("lang", "ar");
  });

  it("renders the complete English landing page with LTR direction", async () => {
    render(<NavigatorApp initialLocale="en" />);
    expect(screen.getByRole("link", { name: "Saudi Business Launch Navigator" })).toHaveTextContent("Business Launch Guide");
    expect(screen.getByRole("link", { name: "Saudi Business Launch Navigator" })).toHaveAttribute("href", "/en");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Understand your business-launch steps clearly");
    expect(screen.getByText(/Answer a few short questions about your business/)).toBeInTheDocument();
    expect(screen.getByText(/The current version covers coffee shops, restaurants, and cloud kitchens/)).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: /Coffee shop/ })).toBeInTheDocument();
    await waitFor(() => expect(document.documentElement).toHaveAttribute("dir", "ltr"));
    expect(document.documentElement).toHaveAttribute("lang", "en");
  });

  it("keeps the header minimal while exposing locale-safe About navigation", async () => {
    render(<NavigatorApp initialLocale="ar" />);
    await waitFor(() => expect(api.activities).toHaveBeenCalled());
    const navigation = screen.getByRole("navigation", { name: "التنقل الرئيسي" });
    expect(within(navigation).getByRole("link", { name: "الرئيسية" })).toHaveAttribute("href", "/ar");
    expect(within(navigation).getByRole("link", { name: "حول الدليل" })).toHaveAttribute("href", "/ar/about");
    expect(within(navigation).getByRole("button", { name: "Switch to English" })).toBeInTheDocument();
    expect(within(navigation).queryByText("كيف يعمل")).not.toBeInTheDocument();
  });

  it("switches language without resetting the active question or selected answer", async () => {
    render(<NavigatorApp initialLocale="ar" />);
    const user = await startAndSelect("مطعم");
    await user.click(screen.getByRole("button", { name: "نعم" }));
    await user.click(screen.getByRole("button", { name: "Switch to English" }));
    expect(document.documentElement).toHaveAttribute("dir", "ltr");
    expect(screen.getByText("Will the business employ staff or workers?")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Yes" })).toHaveAttribute("aria-pressed", "true");
    expect(window.location.pathname).toBe("/en");
  });

  it("preserves the VAT selection while switching between exact Arabic and English labels", async () => {
    render(<NavigatorApp initialLocale="ar" />);
    const user = await startAndSelect("مقهى");
    for (let index = 0; index < 3; index += 1) {
      await user.click(screen.getByRole("button", { name: "نعم" }));
      await user.click(screen.getByRole("button", { name: "التالي" }));
    }
    expect(
      screen.getByText(
        "هل أكدت عبر هيئة الزكاة والضريبة والجمارك أن التسجيل الإلزامي في ضريبة القيمة المضافة ينطبق على منشأتك؟",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "نعم" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "تأكدت عبر الهيئة أنه إلزامي" }));
    await user.click(screen.getByRole("button", { name: "Switch to English" }));
    expect(
      screen.getByText(
        "Have you confirmed through ZATCA whether mandatory VAT registration applies to your business?",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: "I confirmed through ZATCA that it is mandatory",
      }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(screen.queryByRole("button", { name: "Yes" })).not.toBeInTheDocument();
  });
});

describe("API-driven guided workflow", () => {
  it("requires an explicit activity choice before the simple Start action", async () => {
    render(<NavigatorApp initialLocale="ar" />);
    await waitFor(() => expect(api.activities).toHaveBeenCalled());
    const start = screen.getByRole("button", { name: "ابدأ الأسئلة" });
    expect(start).toBeDisabled();
    expect(api.questionnaire).not.toHaveBeenCalled();
    const coffeeShop = screen.getByRole("button", { name: /^مقهى/ });
    expect(coffeeShop).toHaveAttribute("aria-pressed", "false");
    await userEvent.click(coffeeShop);
    expect(coffeeShop).toHaveAttribute("aria-pressed", "true");
    expect(start).toBeEnabled();
    expect(api.questionnaire).not.toHaveBeenCalled();
    await userEvent.click(start);
    expect(await screen.findByText("من سيملك المشروع؟")).toBeInTheDocument();
    expect(screen.getByText(/سنطرح عليك أسئلة قصيرة عن مشروعك/)).toBeInTheDocument();
    expect(api.questionnaire).toHaveBeenCalledWith("coffee_shop");
  });

  it("keeps progress, answer selection, and navigation semantics explicit", async () => {
    render(<NavigatorApp initialLocale="ar" />);
    await waitFor(() => expect(api.activities).toHaveBeenCalled());
    await userEvent.click(await screen.findByRole("button", { name: /^مقهى/ }));
    await userEvent.click(screen.getByRole("button", { name: "ابدأ الأسئلة" }));

    const group = await screen.findByRole("group", { name: "من سيملك المشروع؟" });
    const progress = screen.getByRole("progressbar", { name: "تقدم الأسئلة" });
    expect(progress).toHaveAttribute("aria-valuemin", "1");
    expect(progress).toHaveAttribute("aria-valuemax", "7");
    expect(progress).toHaveAttribute("aria-valuenow", "1");
    expect(progress).toHaveAttribute("aria-valuetext", "السؤال ١ من ٧");
    expect(screen.getByRole("button", { name: "السابق" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "التالي" })).toBeDisabled();

    const unknown = within(group).getByRole("button", { name: "لست متأكدًا" });
    await userEvent.click(unknown);
    expect(unknown).toHaveAttribute("aria-pressed", "true");
    expect(unknown).toHaveClass("selected");
    expect(unknown.querySelector(".answer-selected-mark")).toHaveAttribute("aria-hidden", "true");
    expect(
      within(group)
        .getAllByRole("button")
        .filter((button) => button !== unknown && button.classList.contains("answer-button"))
        .every((button) => button.getAttribute("aria-pressed") === "false"),
    ).toBe(true);
    expect(screen.getByRole("button", { name: "التالي" })).toBeEnabled();
  });

  it("shows labelled loading and honest empty activity states", async () => {
    api.activities.mockReturnValue(new Promise(() => undefined));
    const { unmount } = render(<NavigatorApp initialLocale="ar" />);
    expect(screen.getByRole("status")).toHaveTextContent("جارٍ تحميل الأنشطة المدعومة");
    unmount();

    api.activities.mockResolvedValue({ ...activitiesResponse, activities: [] });
    render(<NavigatorApp initialLocale="ar" />);
    await waitFor(() => expect(api.activities).toHaveBeenCalled());
    expect(await screen.findByText("لا توجد أنشطة متاحة حالياً.")).toBeInTheDocument();
  });

  it("loads clean activity cards from the API with project-authored descriptions", async () => {
    render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مقهى");
    expect(api.activities).toHaveBeenCalledTimes(1);
    expect(api.questionnaire).toHaveBeenCalledWith("coffee_shop");
    expect(screen.getByText("مقهى")).toBeInTheDocument();
  });

  it("provides bilingual help for every active question", () => {
    for (const question of Object.values(questionsByActivity).flat()) {
      expect(question.help_text_ar.trim()).not.toBe("");
      expect(question.help_text_en.trim()).not.toBe("");
    }
  });

  it("opens question help by focus, hover, and tap and closes it by Escape or outside tap", async () => {
    render(<NavigatorApp initialLocale="ar" />);
    const user = await startAndSelect("مطعم");
    const helpButton = screen.getByRole("button", { name: "توضيح المقصود بالسؤال" });
    const helpText = "المقصود أشخاص ستوظفهم المنشأة للعمل لديها. لا يشمل ذلك سائقي منصات التوصيل أو المقاولين الخارجيين الذين لا توظفهم المنشأة.";

    expect(helpButton).toHaveAttribute("aria-controls");
    expect(helpButton).toHaveAttribute("aria-expanded", "false");

    fireEvent.focus(helpButton);
    const focusedNote = screen.getByRole("note");
    expect(focusedNote).toHaveTextContent(helpText);
    expect(helpButton).toHaveAttribute("aria-expanded", "true");
    expect(helpButton).toHaveAttribute("aria-controls", focusedNote.id);
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
    expect(helpButton).toHaveAttribute("aria-expanded", "false");
    expect(helpButton).not.toHaveAttribute("aria-describedby");

    const helpRoot = helpButton.closest(".question-help")!;
    fireEvent.pointerEnter(helpRoot, { pointerType: "mouse" });
    expect(screen.getByRole("note")).toHaveTextContent(helpText);
    fireEvent.pointerLeave(helpRoot, { pointerType: "mouse" });
    expect(screen.queryByRole("note")).not.toBeInTheDocument();

    await user.click(helpButton);
    expect(screen.getByRole("note")).toHaveTextContent(helpText);
    fireEvent.pointerDown(document.body);
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
    expect(helpButton).toHaveAttribute("aria-expanded", "false");
    expect(helpButton).not.toHaveAttribute("aria-describedby");
  });

  it("maps three Yes answers and the VAT confirmation to true", async () => {
    api.checklist.mockResolvedValue(checklistResponse(activities[1], { applies: 7, doesNotApply: 0, needs: 0 }));
    render(<NavigatorApp initialLocale="ar" />);
    const user = await startAndSelect("مقهى");
    for (let index = 0; index < 3; index += 1) {
      await user.click(screen.getByRole("button", { name: "نعم" }));
      await user.click(screen.getByRole("button", { name: "التالي" }));
    }
    expect(screen.queryByRole("button", { name: "التالي" })).not.toBeInTheDocument();
    const evaluate = screen.getByRole("button", { name: "عرض النتيجة" });
    expect(evaluate).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "تأكدت عبر الهيئة أنه إلزامي" }));
    expect(evaluate).toBeEnabled();
    await user.click(evaluate);
    await screen.findByRole("heading", { level: 1, name: "خطوات بدء مشروعك" });
    expect(api.checklist).toHaveBeenCalledTimes(1);
    expect(api.checklist).toHaveBeenCalledWith("coffee_shop", {
      ownership_investor_route: "saudi_person_or_saudi_owned_entity",
      planned_legal_form: "individual_establishment",
      has_selected_business_premises: true,
      has_employees: true,
      has_food_establishment_workers: true,
      offers_home_delivery: true,
      zatca_confirmed_mandatory_vat_registration_applies: true,
    });
    expect(screen.getAllByText(/متطلب اختباري/)).toHaveLength(7);
    expect(screen.getByText(/٧ متطلبات تنطبق على مشروعك/)).toBeInTheDocument();
  });

  it("preserves generic and VAT-specific values across the restaurant flow", async () => {
    api.checklist.mockResolvedValue(checklistResponse(activities[2], { applies: 4, doesNotApply: 2, needs: 2 }));
    render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مطعم");
    await answerSequence([
      "نعم",
      "لا",
      "لست متأكدًا",
      "لست متأكدًا",
      "تأكدت عبر الهيئة أنه إلزامي",
    ]);
    await screen.findByRole("heading", { level: 1, name: "خطوات بدء مشروعك" });
    expect(api.checklist).toHaveBeenCalledWith("restaurant", {
      ownership_investor_route: "saudi_person_or_saudi_owned_entity",
      planned_legal_form: "individual_establishment",
      has_selected_business_premises: true,
      has_employees: true,
      has_food_establishment_workers: false,
      offers_home_delivery: null,
      uses_public_sidewalk_for_customer_service: null,
      zatca_confirmed_mandatory_vat_registration_applies: true,
    });
    expect(screen.getByText(/عدد الإجابات التي ما زلنا نحتاجها لتحديد النتائج المرتبطة بها: ٢/)).toBeInTheDocument();
    const collapsed = screen.getByText(/خطوات لا تنطبق على إجاباتك الحالية \([٢2]\)/).closest("details");
    expect(collapsed).not.toHaveAttribute("open");
  });

  it("keeps required items first and returns from missing information to the exact question", async () => {
    api.checklist.mockResolvedValue(checklistResponse(activities[0], { applies: 2, doesNotApply: 0, needs: 4 }));
    render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مطبخ سحابي");
    await answerSequence([
      "لست متأكدًا",
      "لست متأكدًا",
      "لست متأكدًا",
      "لم أتأكد عبر الهيئة بعد",
    ]);
    await screen.findByRole("heading", { level: 1, name: "خطوات بدء مشروعك" });
    const missing = screen.getByRole("heading", { name: "نحتاج منك معلومة" }).closest("section")!;
    const required = screen.getByRole("heading", { name: "ابدأ بهذه الخطوات" }).closest("section")!;
    expect(required.compareDocumentPosition(missing) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    await userEvent.click(screen.getAllByRole("button", { name: "أجب الآن" })[0]);
    expect(screen.getByText("هل ستوظف المنشأة موظفين أو عمالًا؟")).toBeInTheDocument();
  });

  it("shows a concise default card and keeps evidence details available on request", async () => {
    render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مقهى");
    await answerSequence(["نعم", "نعم", "نعم", "تأكدت عبر الهيئة أنه إلزامي"]);
    await screen.findByRole("heading", { level: 1, name: "خطوات بدء مشروعك" });
    const requiredSection = screen.getByRole("heading", { name: "ابدأ بهذه الخطوات" }).closest("section")!;
    const firstCard = within(requiredSection).getAllByRole("article")[1];
    expect(within(firstCard).getByText("جهة رسمية اختبارية")).toBeInTheDocument();
    const link = within(firstCard).getAllByRole("link", { name: /المصدر الرسمي/ })[0];
    expect(link).toHaveClass("official-source-link");
    expect(link).toHaveAttribute("href", "https://official.example.gov.sa/official-source");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(within(firstCard).getByText(/إجاباتك المرتبطة/)).not.toBeVisible();
    await userEvent.click(within(firstCard).getByText("عرض التفاصيل"));
    expect(within(firstCard).getByText("إجاباتك المرتبطة بهذا المتطلب")).toBeVisible();
    expect(within(firstCard).getByText("نعم")).toBeVisible();
    expect(within(firstCard).getByText(/صفحة حكومية رسمية/)).toBeVisible();
  });

  it("humanizes source review details and keeps coverage limits visible", async () => {
    render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مقهى");
    await answerSequence(["نعم", "نعم", "نعم", "تأكدت عبر الهيئة أنه إلزامي"]);
    const coverage = await screen.findByText("التغطية الحالية جزئية · اعرف المزيد");
    expect(coverage.closest("details")).not.toHaveAttribute("open");
    fireEvent.click(coverage);
    expect(screen.getByText(/نعرض فقط المتطلبات/)).toBeVisible();
    expect(screen.queryByText("approved")).not.toBeInTheDocument();
  });

  it("renders applicability, navigation guidance, and actionability sections", async () => {
    const { container } = render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مقهى");
    await answerSequence(["نعم", "نعم", "نعم", "تأكدت عبر الهيئة أنه إلزامي"]);
    await screen.findByRole("heading", { level: 1, name: "خطوات بدء مشروعك" });

    const groups = container.querySelectorAll(".result-group");
    expect(groups).toHaveLength(3);
    expect(groups[0]).toHaveTextContent("ابدأ بهذه الخطوات");
    expect(groups[0]).toHaveTextContent("هذه الخطوات ظهرت وفق إجاباتك الحالية");
    expect(groups[1]).toHaveTextContent("نحتاج منك معلومة");
    expect(groups[1]).toHaveTextContent("لا نحتاج معلومات تنظيمية إضافية الآن");
    expect(groups[2]).toHaveTextContent("راجع هذه الأمور");
    expect(groups[2]).toHaveTextContent("هذه موضوعات إرشادية لا تدخل في نسبة الإنجاز");

    expect(screen.getByRole("heading", { name: "رتبنا لك النتيجة بناءً على إجاباتك" })).toBeInTheDocument();
    expect(screen.getByText(/ابدأ بالخطوات الظاهرة، وأكمل أي معلومة ناقصة/)).toBeInTheDocument();

    const required = screen.getByRole("heading", { name: "ابدأ بهذه الخطوات" }).closest("section")!;
    expect(within(required).getByRole("link", { name: /ابدأ من هنا/ })).toHaveAttribute(
      "href",
      "https://official.example.gov.sa/service",
    );
    expect(within(required).getByText("قبل البدء")).toBeInTheDocument();
    expect(within(required).getByText("المستندات المطلوبة")).toBeInTheDocument();
    expect(within(required).getAllByText("الرسوم").length).toBeGreaterThan(0);
    expect(within(required).getByText("٦٠ ر.س")).toBeInTheDocument();
    expect(within(required).getByText("مجانًا")).toBeInTheDocument();
    expect(within(required).getAllByText("الخطوات").length).toBeGreaterThan(0);
    expect(within(required).getByText("سجّل المنشأة ضمن التسلسل الرسمي.")).toBeInTheDocument();
    expect(within(required).queryByText("المدة")).not.toBeInTheDocument();
    const applicableItems = within(required).getAllByRole("article");
    expect(within(applicableItems[1]).getByText("الرسوم")).toBeInTheDocument();
    expect(within(applicableItems[1]).queryByText("قبل البدء")).not.toBeInTheDocument();
    expect(within(applicableItems[1]).queryByText("المستندات المطلوبة")).not.toBeInTheDocument();

    const verification = screen.getByRole("heading", { name: "راجع هذه الأمور" }).closest("section")!;
    expect(within(verification).getByRole("heading", { name: "الفوترة الإلكترونية" })).toBeInTheDocument();
    expect(within(verification).getByRole("heading", { name: "الزكاة" })).toBeInTheDocument();
    expect(within(verification).getAllByRole("link", { name: /التحقق عبر الجهة الرسمية/ }).length).toBeGreaterThan(0);
    expect(container).not.toHaveTextContent("REQUIRES_OFFICIAL_CONFIRMATION");
    expect(container).not.toHaveTextContent("ownership_investment_route");
    expect(container).not.toHaveTextContent("actionability");
  });

  it("keeps regulatory uncertainty and missing navigation visibly separate with re-entry", async () => {
    api.checklist.mockResolvedValue(
      checklistResponse(
        activities[2],
        { applies: 2, doesNotApply: 1, needs: 1 },
        { missingNavigation: ["planned_legal_form"] },
      ),
    );
    render(<NavigatorApp initialLocale="ar" />);
    await waitFor(() => expect(api.activities).toHaveBeenCalled());
    await userEvent.click(screen.getByRole("button", { name: /^مطعم/ }));
    await userEvent.click(screen.getByRole("button", { name: "ابدأ الأسئلة" }));
    await userEvent.click(await screen.findByRole("button", { name: "فرد سعودي أو منشأة مملوكة سعودياً" }));
    await userEvent.click(screen.getByRole("button", { name: "التالي" }));
    await userEvent.click(screen.getByRole("button", { name: "لم أحدد بعد" }));
    await userEvent.click(screen.getByRole("button", { name: "التالي" }));
    await userEvent.click(screen.getByRole("button", { name: "نعم" }));
    await userEvent.click(screen.getByRole("button", { name: "التالي" }));
    await answerSequence(["لست متأكدًا", "نعم", "نعم", "لا", "لم أتأكد عبر الهيئة بعد"]);

    const regulatory = await screen.findByRole("heading", { name: "نحتاج منك معلومة" });
    const verification = screen.getByRole("heading", { name: "راجع هذه الأمور" });
    const summary = document.querySelector<HTMLElement>(".result-introduction")!;
    expect(within(summary).getByText("قائمتك تحتاج معلومات إضافية")).toBeInTheDocument();
    expect(within(summary).getByText(/عدد الإجابات التي ما زلنا نحتاجها لتحديد النتائج المرتبطة بها: ١/)).toBeInTheDocument();
    expect(within(summary).getByRole("button", { name: "تعديل الإجابات" })).toBeInTheDocument();
    expect(regulatory.closest("section")).toHaveTextContent("نحتاج إلى هذه المعلومة حتى نحدد النتيجة المرتبطة بها بشكل أدق");
    expect(regulatory.closest("section")).toHaveTextContent("هل ستوظف موظفين");
    expect(verification.closest("section")).toHaveTextContent("لم تحدد الشكل القانوني بعد");
    expect(verification.closest("section")).toHaveTextContent("هذه موضوعات إرشادية لا تدخل في نسبة الإنجاز");
    expect(regulatory.closest("section")).not.toHaveTextContent("لم تحدد الشكل القانوني بعد");

    const verificationSection = verification.closest("section")!;
    await userEvent.click(within(verificationSection).getByRole("button", { name: "أجب الآن" }));
    expect(screen.getByText("ما الشكل القانوني الذي تنوي استخدامه؟")).toBeInTheDocument();
  });

  it("counts only applicable requirements in React-memory personal progress", async () => {
    const localSet = vi.spyOn(Storage.prototype, "setItem");
    api.checklist.mockResolvedValue(
      checklistResponse(
        activities[1],
        { applies: 4, doesNotApply: 2, needs: 2 },
        { missingNavigation: ["planned_legal_form"] },
      ),
    );
    render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مقهى");
    await answerSequence(["نعم", "نعم", "نعم", "تأكدت عبر الهيئة أنه إلزامي"]);
    const required = (await screen.findByRole("heading", { name: "ابدأ بهذه الخطوات" })).closest("section")!;
    const checkboxes = within(required).getAllByRole("checkbox", { name: /أنجزت هذه الخطوة/ });
    expect(checkboxes).toHaveLength(4);
    expect(screen.getByText("٤ متطلبات تنطبق على مشروعك")).toBeInTheDocument();
    expect(screen.getByText("أنجزت ٠ من ٤")).toBeInTheDocument();
    expect(screen.getByText("متبقي ٤")).toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: "تقدم إنجاز متطلبات المشروع" })).toHaveAttribute(
      "aria-valuenow",
      "0",
    );
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuemin", "0");
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuemax", "4");
    expect(screen.getByText(/خطوات لا تنطبق على إجاباتك الحالية \([٢2]\)/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "نحتاج منك معلومة" }).closest("section")).toHaveTextContent(
      "نحتاج إلى هذه المعلومة حتى نحدد النتيجة المرتبطة بها بشكل أدق",
    );
    expect(screen.getByRole("heading", { name: "راجع هذه الأمور" }).closest("section")).toHaveTextContent(
      "هذه موضوعات إرشادية لا تدخل في نسبة الإنجاز",
    );
    expect(screen.getAllByText(/حالة الإنجاز هنا للمتابعة الشخصية فقط/)).toHaveLength(1);

    await userEvent.click(checkboxes[0]);
    await userEvent.click(checkboxes[1]);
    expect(checkboxes[0]).toBeChecked();
    expect(checkboxes[1]).toBeChecked();
    expect(screen.getByText("أنجزت ٢ من ٤")).toBeInTheDocument();
    expect(screen.getByText("متبقي ٢")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "2");
    expect(checkboxes[0].closest("article")).toHaveTextContent("منجزة");
    expect(checkboxes[2].closest("article")).toHaveTextContent("غير منجزة");
    const partialOutcome = screen.getByRole("region", { name: "قائمتك ما زالت قيد المتابعة" });
    expect(within(partialOutcome).getByText("أنجزت ٢ من ٤ متطلبات.")).toBeInTheDocument();
    expect(within(partialOutcome).getByText("بقي لديك ٢ متطلبات في قائمتك.")).toBeInTheDocument();
    expect(within(partialOutcome).queryByText("أنهيت متابعة متطلبات قائمتك")).not.toBeInTheDocument();
    expect(within(partialOutcome).queryByText("بقي عليك التحقق من هذه الأمور")).not.toBeInTheDocument();
    expect(within(partialOutcome).getByText(/قبل اعتبار إجراءاتك منتهية/)).toBeInTheDocument();

    await userEvent.click(checkboxes[0]);
    expect(screen.getByText("أنجزت ١ من ٤")).toBeInTheDocument();
    expect(screen.getByText("متبقي ٣")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "1");
    expect(localSet).not.toHaveBeenCalled();
    expect(api.checklist).toHaveBeenCalledTimes(1);
    localSet.mockRestore();
  });

  it("shows the bounded final outcome and governed official verification routes at 100%", async () => {
    api.checklist.mockResolvedValue(
      checklistResponse(activities[1], { applies: 2, doesNotApply: 1, needs: 0 }),
    );
    render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مقهى");
    await answerSequence(["نعم", "نعم", "نعم", "تأكدت عبر الهيئة أنه إلزامي"]);

    expect(
      await screen.findByText("تم تحديد قائمتك بناءً على إجاباتك الحالية والمعلومات الموثقة المتاحة في الدليل."),
    ).toBeInTheDocument();
    const checkboxes = screen.getAllByRole("checkbox", { name: /أنجزت هذه الخطوة/ });
    expect(checkboxes).toHaveLength(2);
    await userEvent.click(checkboxes[0]);
    await userEvent.click(checkboxes[1]);
    expect(screen.getByText("أنجزت ٢ من ٢")).toBeInTheDocument();
    expect(screen.getByText("متبقي ٠")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "2");
    const finalOutcome = screen.getByRole("region", { name: "أنهيت متابعة متطلبات قائمتك" });
    expect(within(finalOutcome).getByText(/وضعت علامة إنجاز على جميع المتطلبات التي حددها الدليل/)).toBeInTheDocument();
    expect(within(finalOutcome).getByRole("heading", { name: "بقي عليك التحقق من هذه الأمور" })).toBeInTheDocument();
    expect(within(finalOutcome).getByRole("heading", { name: "الفوترة الإلكترونية" })).toBeInTheDocument();
    expect(within(finalOutcome).getAllByText(/تحقق من حالتك عبر الجهة الرسمية/).length).toBeGreaterThan(0);
    expect(within(finalOutcome).getAllByText("جهة رسمية اختبارية").length).toBeGreaterThan(0);
    const officialDestination = within(finalOutcome).getAllByRole("link", { name: /التحقق عبر الجهة الرسمية/ })[0];
    expect(officialDestination).toHaveAttribute(
      "href",
      "https://official.example.gov.sa/service",
    );
    expect(officialDestination).toHaveAttribute("target", "_blank");
    expect(officialDestination).toHaveAttribute("rel", "noopener noreferrer");
    expect(within(finalOutcome).getByRole("link", { name: "راجع الأمور التي تحتاج تحققًا" })).toHaveAttribute(
      "href",
      "#verification-title",
    );
    expect(within(finalOutcome).getByText(/تعرض هذه النتيجة المتطلبات والمعلومات التي حددها الدليل/)).toBeInTheDocument();
    expect(within(finalOutcome).getByText(/قد تحتاج بعض الحالات إلى متطلبات أو تأكيدات إضافية/)).toBeInTheDocument();
    expect(within(finalOutcome).getByText(/قبل اعتبار إجراءاتك منتهية/)).toBeInTheDocument();
    for (const forbidden of [
      "أكملت جميع متطلبات تأسيس المشروع",
      "مشروعك جاهز",
      "أصبحت ممتثلًا",
      "هذه جميع متطلبات السعودية",
      "هذه قائمة كاملة قانونيًا",
      "تأكيد جاهزية المشروع",
      "إكمال التأسيس",
      "اعتماد القائمة",
    ]) {
      expect(screen.queryByText(forbidden)).not.toBeInTheDocument();
    }
  });

  it("keeps an all-marked checklist incomplete when regulatory information is missing", async () => {
    api.checklist.mockResolvedValue(
      checklistResponse(activities[1], { applies: 2, doesNotApply: 0, needs: 1 }),
    );
    render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مقهى");
    await answerSequence(["نعم", "نعم", "نعم", "تأكدت عبر الهيئة أنه إلزامي"]);

    const checkboxes = await screen.findAllByRole("checkbox", { name: /أنجزت هذه الخطوة/ });
    await userEvent.click(checkboxes[0]);
    await userEvent.click(checkboxes[1]);

    const finalOutcome = screen.getByRole("region", {
      name: "أكملت متابعة المتطلبات الحالية، لكن قائمتك لم تُحدد بالكامل بعد",
    });
    expect(within(finalOutcome).getByText(/نحتاج منك ١ معلومة إضافية/)).toBeInTheDocument();
    expect(within(finalOutcome).queryByText("أنهيت متابعة متطلبات قائمتك")).not.toBeInTheDocument();
    expect(within(finalOutcome).queryByText("بقي عليك التحقق من هذه الأمور")).not.toBeInTheDocument();
    await userEvent.click(within(finalOutcome).getByRole("button", { name: "تعديل الإجابات" }));
    expect(screen.getByText(/هل أكدت عبر هيئة الزكاة والضريبة والجمارك/)).toBeInTheDocument();
  });

  it("shows a bounded no-verification outcome when the governed verification arrays are empty", async () => {
    const response = checklistResponse(activities[1], { applies: 2, doesNotApply: 0, needs: 0 });
    response.result.journey_guidance = [];
    response.result.missing_navigation_information = [];
    api.checklist.mockResolvedValue(response);
    render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مقهى");
    await answerSequence(["نعم", "نعم", "نعم", "تأكدت عبر الهيئة أنه إلزامي"]);

    const checkboxes = await screen.findAllByRole("checkbox", { name: /أنجزت هذه الخطوة/ });
    await userEvent.click(checkboxes[0]);
    await userEvent.click(checkboxes[1]);

    const finalOutcome = screen.getByRole("region", { name: "أنهيت متابعة متطلبات قائمتك" });
    expect(within(finalOutcome).getByRole("heading", { name: "أنهيت متابعة قائمتك داخل الدليل" })).toBeInTheDocument();
    expect(within(finalOutcome).getByText(/لم يتبقَّ في الدليل حاليًا أي أمر إضافي يحتاج إلى تأكيد/)).toBeInTheDocument();
    expect(within(finalOutcome).queryByRole("heading", { name: "بقي عليك التحقق من هذه الأمور" })).not.toBeInTheDocument();
    expect(within(finalOutcome).queryByRole("list")).not.toBeInTheDocument();
    expect(within(finalOutcome).queryByRole("link", { name: "راجع الأمور التي تحتاج تحققًا" })).not.toBeInTheDocument();
    expect(within(finalOutcome).getByText(/قبل اعتبار إجراءاتك منتهية/)).toBeInTheDocument();
  });

  it("routes missing navigation from the final summary without inventing an authority or link", async () => {
    api.checklist.mockResolvedValue(
      checklistResponse(
        activities[1],
        { applies: 1, doesNotApply: 0, needs: 0 },
        { missingNavigation: ["planned_legal_form"] },
      ),
    );
    render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مقهى");
    await answerSequence(["نعم", "نعم", "نعم", "تأكدت عبر الهيئة أنه إلزامي"]);
    await userEvent.click(await screen.findByRole("checkbox", { name: /أنجزت هذه الخطوة/ }));

    const finalOutcome = screen.getByRole("region", { name: "أنهيت متابعة متطلبات قائمتك" });
    const answerNow = within(finalOutcome).getByRole("button", { name: "أجب الآن" });
    const missingItem = answerNow.closest("li")!;
    expect(within(missingItem).getByRole("heading", { name: "لم تحدد الشكل القانوني بعد" })).toBeInTheDocument();
    expect(within(missingItem).queryByText("الجهة الرسمية")).not.toBeInTheDocument();
    expect(within(missingItem).queryByRole("link")).not.toBeInTheDocument();
    await userEvent.click(answerNow);
    expect(screen.getByText("ما الشكل القانوني الذي تنوي استخدامه؟")).toBeInTheDocument();
  });

  it("does not treat a zero-item checklist as fully marked", async () => {
    api.checklist.mockResolvedValue(
      checklistResponse(activities[1], { applies: 0, doesNotApply: 0, needs: 1 }),
    );
    render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مقهى");
    await answerSequence(["نعم", "نعم", "نعم", "تأكدت عبر الهيئة أنه إلزامي"]);
    expect(await screen.findByText("٠ متطلبات تنطبق على مشروعك")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar", { name: "تقدم إنجاز متطلبات المشروع" })).not.toBeInTheDocument();
    expect(screen.getByRole("region", {
      name: "أكملت متابعة المتطلبات الحالية، لكن قائمتك لم تُحدد بالكامل بعد",
    })).toBeInTheDocument();
    expect(screen.queryByText("أنهيت متابعة متطلبات قائمتك")).not.toBeInTheDocument();
  });

  it("uses a bounded neutral state for zero applicable items with no missing regulatory answer", async () => {
    const response = checklistResponse(activities[1], { applies: 0, doesNotApply: 1, needs: 0 });
    response.result.journey_guidance = [];
    response.result.missing_navigation_information = [];
    api.checklist.mockResolvedValue(response);
    render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مقهى");
    await answerSequence(["نعم", "نعم", "نعم", "تأكدت عبر الهيئة أنه إلزامي"]);

    const finalOutcome = screen.getByRole("region", {
      name: "لم يحدد الدليل متطلبات منطبقة ضمن التغطية الحالية",
    });
    expect(within(finalOutcome).getByText(/لا تعني هذه النتيجة عدم وجود متطلبات أخرى/)).toBeInTheDocument();
    expect(within(finalOutcome).getByText(/قبل اعتبار إجراءاتك منتهية/)).toBeInTheDocument();
    expect(screen.queryByText("أنهيت متابعة متطلبات قائمتك")).not.toBeInTheDocument();
  });

  it("edits answers or starts over using frontend state only", async () => {
    render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مقهى");
    await answerSequence(["نعم", "نعم", "نعم", "تأكدت عبر الهيئة أنه إلزامي"]);
    await screen.findByRole("heading", { name: "ابدأ بهذه الخطوات" });

    await userEvent.click(screen.getByRole("button", { name: "تعديل الإجابات" }));
    expect(screen.getByText(/هل أكدت عبر هيئة الزكاة والضريبة والجمارك/)).toBeInTheDocument();
    expect(api.checklist).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByRole("button", { name: "عرض النتيجة" }));
    await screen.findByRole("heading", { name: "ابدأ بهذه الخطوات" });
    await userEvent.click(screen.getByRole("button", { name: "ابدأ من جديد" }));
    expect(await screen.findByRole("heading", { name: "ما نشاط مشروعك؟" })).toBeInTheDocument();
    expect(api.checklist).toHaveBeenCalledTimes(2);
  });

  it("keeps the final results natural in English and LTR", async () => {
    render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مطبخ سحابي");
    await answerSequence(["نعم", "نعم", "نعم", "تأكدت عبر الهيئة أنه إلزامي"]);
    await screen.findByRole("heading", { name: "ابدأ بهذه الخطوات" });
    await userEvent.click(screen.getAllByRole("checkbox", { name: /أنجزت هذه الخطوة/ })[0]);
    await userEvent.click(screen.getByRole("button", { name: "Switch to English" }));
    expect(document.documentElement).toHaveAttribute("dir", "ltr");
    expect(screen.getByRole("heading", { level: 1, name: "Your business-launch steps" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Start with these steps" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "We need more information" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Things to verify" })).toBeInTheDocument();
    expect(screen.getByText("SAR 60")).toBeInTheDocument();
    expect(screen.getByText("Free")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Start here/ })).toBeInTheDocument();
    expect(screen.getByText("1 of 7 marked complete")).toBeInTheDocument();
    expect(screen.getByText("6 remaining")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getAllByText("Not completed").length).toBeGreaterThan(0);
    expect(screen.getByText(/Completion here is for your personal tracking only/)).toBeInTheDocument();
    expect(screen.getByText(/These guidance topics do not count toward progress/)).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "1");
    const partialOutcome = screen.getByRole("region", { name: "Your checklist is still in progress" });
    expect(within(partialOutcome).getByText("You have marked 1 of 7 requirements complete.")).toBeInTheDocument();
    expect(within(partialOutcome).getByText("You have 6 checklist requirements remaining.")).toBeInTheDocument();

    const englishCheckboxes = screen.getAllByRole("checkbox", { name: /I completed this step/ });
    for (const checkbox of englishCheckboxes.slice(1)) await userEvent.click(checkbox);

    const finalOutcome = screen.getByRole("region", { name: "Checklist follow-up complete" });
    expect(within(finalOutcome).getByRole("heading", { name: "Still verify these items" })).toBeInTheDocument();
    expect(within(finalOutcome).getByRole("heading", { name: "E-invoicing" })).toBeInTheDocument();
    expect(within(finalOutcome).getAllByText("Synthetic official authority").length).toBeGreaterThan(0);
    expect(within(finalOutcome).getAllByRole("link", { name: /Verify with the official authority/ })[0]).toHaveAttribute(
      "href",
      "https://official.example.gov.sa/service",
    );
    expect(within(finalOutcome).getByText(/Before considering your setup process complete/)).toBeInTheDocument();
    expect(within(finalOutcome).getByText(/This result shows the requirements and information/)).toBeInTheDocument();
    expect(screen.queryByText(/fully compliant/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/legally complete/i)).not.toBeInTheDocument();
  });
});

describe("safe failure and secondary AI", () => {
  it("shows backend-offline state and never fabricates activities", async () => {
    api.activities.mockRejectedValue(new NavigatorAPIError("BACKEND_UNAVAILABLE", "offline", null, null));
    render(<NavigatorApp initialLocale="ar" />);
    expect(await screen.findByRole("alert")).toHaveTextContent("خدمة الدليل غير متاحة");
    expect(screen.queryByText("مقهى")).not.toBeInTheDocument();
  });

  it("offers a retry after a questionnaire validation failure", async () => {
    api.questionnaire.mockRejectedValue(new NavigatorAPIError("VALIDATION_ERROR", "invalid", 422, "request-seven"));
    render(<NavigatorApp initialLocale="ar" />);
    await waitFor(() => expect(api.activities).toHaveBeenCalled());
    await userEvent.click(await screen.findByRole("button", { name: /^مطعم/ }));
    await userEvent.click(screen.getByRole("button", { name: "ابدأ الأسئلة" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("راجع المعلومات المدخلة");
    expect(within(alert).getByRole("button", { name: "حاول مرة أخرى" })).toBeInTheDocument();
  });

  it("offers an explicit safe retry when checklist generation fails", async () => {
    api.checklist.mockRejectedValueOnce(
      new NavigatorAPIError("BACKEND_UNAVAILABLE", "database detail must stay hidden", 503, "request-eight"),
    );
    render(<NavigatorApp initialLocale="ar" />);
    await startAndSelect("مقهى");
    await answerSequence(["نعم", "نعم", "نعم", "تأكدت عبر الهيئة أنه إلزامي"]);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("تعذر تجهيز قائمتك الآن");
    expect(alert).not.toHaveTextContent("database detail");
    await userEvent.click(within(alert).getByRole("button", { name: "حاول مرة أخرى" }));

    expect(await screen.findByRole("heading", { name: "ابدأ بهذه الخطوات" })).toBeInTheDocument();
    expect(api.checklist).toHaveBeenCalledTimes(2);
  });

  it("keeps AI collapsed and falls back to the complete guided flow when unavailable", async () => {
    api.navigate.mockRejectedValue(new NavigatorAPIError("AI_UNAVAILABLE", "not configured", 503, "request-ai"));
    render(<NavigatorApp initialLocale="ar" />);
    await waitFor(() => expect(api.activities).toHaveBeenCalled());
    const panel = screen.getAllByText("لست متأكداً؟ صف مشروعك")[0].closest("details")!;
    expect(panel).not.toHaveAttribute("open");
    await userEvent.click(within(panel).getAllByText("لست متأكداً؟ صف مشروعك")[0]);
    await userEvent.type(within(panel).getByRole("textbox"), "أرغب في فتح مطعم");
    await userEvent.click(within(panel).getByRole("button", { name: "فهم الوصف" }));
    expect(await within(panel).findByText(/المساعدة الذكية غير متاحة/)).toBeInTheDocument();
    expect(within(panel).getByRole("textbox")).toHaveValue("أرغب في فتح مطعم");
    expect(await screen.findByText("مطعم")).toBeInTheDocument();
  });

  it("renders optional AI explanation separately from the authoritative checklist", async () => {
    const response = checklistResponse(activities[2], { applies: 4, doesNotApply: 2, needs: 2 });
    api.navigate.mockResolvedValue(navigatorResponse(response));
    render(<NavigatorApp initialLocale="ar" />);
    await waitFor(() => expect(api.activities).toHaveBeenCalled());
    const panel = screen.getAllByText("لست متأكداً؟ صف مشروعك")[0].closest("details")!;
    await userEvent.click(within(panel).getAllByText("لست متأكداً؟ صف مشروعك")[0]);
    await userEvent.type(within(panel).getByRole("textbox"), "أرغب في فتح مطعم ولدي موظفون");
    await userEvent.click(within(panel).getByRole("button", { name: "فهم الوصف" }));
    expect(await screen.findByRole("heading", { level: 1, name: "خطوات بدء مشروعك" })).toBeInTheDocument();
    await waitFor(() => expect(api.questionnaire).toHaveBeenCalledWith("restaurant"));
    expect(screen.getByText("شرح اختياري للنتيجة").closest("details")).toBeInTheDocument();
  });

  it("does not use browser persistence or expose an OpenAI key field", async () => {
    const localSet = vi.spyOn(Storage.prototype, "setItem");
    render(<NavigatorApp initialLocale="ar" />);
    await waitFor(() => expect(api.activities).toHaveBeenCalled());
    expect(localSet).not.toHaveBeenCalled();
    expect(screen.queryByText(/OPENAI_API_KEY/)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/API key/i)).not.toBeInTheDocument();
    localSet.mockRestore();
  });
});
