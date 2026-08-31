import { expect, test, type Page } from "@playwright/test";

type ChecklistEnvelope = {
  metadata: {
    catalog_mode: string;
    publication_state: string;
    data_classification: string;
  };
  result: {
    applies: unknown[];
    does_not_apply: unknown[];
    needs_information: unknown[];
    journey_guidance: unknown[];
    regulatory_snapshot: {
      catalog_mode: string;
      publication_count: number;
    };
  };
};

type RenderedLink = {
  absoluteHref: string;
  rawHref: string;
  text: string;
  target: string | null;
  rel: string | null;
  sourceClassification: string | null;
};

const verifiedRoutes = new Set<string>();
const verifiedFragmentDestinations = new Set<string>();
const officialActivityReferenceURLs = new Set([
  "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=1770",
  "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=1319",
  "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=859397",
]);

const forbiddenDemoText = [
  "example.invalid",
  "رابط تجريبي غير حكومي",
  "جهة نموذجية غير حكومية",
  "صفحة نموذجية غير حكومية لأغراض العرض",
  "مسار نموذجي غير حكومي",
  "استخدم الرابط التجريبي للتحقق",
  "استخدم الرابط النموذجي لفهم طريقة التنقل",
  "demo non-government link",
  "non-government demo link",
  "fictional non-government demo authority",
  "non-government sample page for demonstration",
  "non-government sample route",
  "use the demo link to verify",
  "use the sample link only to understand navigation",
  "we do not need more regulatory information right now",
  "لا نحتاج معلومات تنظيمية إضافية الآن",
  "project requirement completion progress",
  "تقدم إنجاز متطلبات المشروع",
  "checklist requirements remaining",
  "متطلبات في قائمتك",
  "requirements that do not apply",
  "متطلبات لا تنطبق على حالتك",
  "your answers connected to this requirement",
  "إجاباتك المرتبطة بهذا المتطلب",
  "this requirement is unconditional",
  "هذا المتطلب غير مشروط",
  "technical demo",
  "sample rules",
  "deterministic result",
  "نسخة عرض تقنية",
  "نسخة المحفظة",
  "القواعد النموذجية",
  "النتيجة الحتمية",
  "هذا مثال يوضح",
] as const;

const contradictoryCurrentRecordClaims = [
  /this checklist shows the verified requirements .*official sources currently available/i,
  /this result shows the requirements .*verified official sources currently available/i,
  /(?:these|the current) (?:records|requirements).*(?:official government|verified official)/i,
  /تعرض هذه القائمة المتطلبات الموثقة .*المصادر الرسمية المتاحة/,
  /تعرض هذه النتيجة المتطلبات .*المصادر الرسمية الموثقة المتاحة/,
  /هذه (?:السجلات|المتطلبات) الحالية.*(?:حكومية رسمية|رسمية موثقة)/,
] as const;

test.describe.configure({ mode: "serial" });

test("Arabic demo flow uses the real API, preserves unknown, and supports re-entry", async ({
  page,
}) => {
  const faults = collectRuntimeFaults(page);
  await page.goto("/ar");

  await expect(page.locator("html")).toHaveAttribute("lang", "ar");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.getByText("نسخة تجريبية مستقلة وليست منصة حكومية.")).toBeVisible();
  await expect(page.getByTestId("portfolio-demo-notice")).toHaveCount(0);
  await expectDemoDOMIntegrity(page);
  await auditRenderedLinks(page);

  await expect(page.getByRole("heading", { name: "قبل أن نبدأ" })).toBeVisible();
  await expect(page.getByText(/معلومات بدء النشاط بين خدمات ومصادر حكومية متعددة/)).toBeVisible();
  await startActivity(page, "مطعم", "ابدأ الأسئلة");
  await expect(page.getByText("نسخة تجريبية مستقلة وليست منصة حكومية.")).toHaveCount(0);
  await expect(page.getByText(/إذا لم تعرف إجابة، لا تخمّن/)).toBeVisible();
  const progress = page.getByRole("progressbar", { name: "تقدم الأسئلة" });
  await expect(progress).toHaveAttribute("aria-valuemax", "8");
  await expect(page.getByText("السؤال ١ من ٨", { exact: true })).toBeVisible();
  const firstHelp = page.getByRole("button", { name: "توضيح المقصود بالسؤال" });
  await firstHelp.click();
  await expect(page.getByText("ما المقصود؟", { exact: true })).toBeVisible();
  await expect(page.getByText("لماذا نسألك؟", { exact: true })).toBeVisible();
  await expect(page.getByText("مثال بسيط", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expectDemoDOMIntegrity(page);
  await auditRenderedLinks(page);

  for (let question = 1; question <= 8; question += 1) {
    await expect(progress).toHaveAttribute("aria-valuenow", String(question));
    const answerButtons = page.locator(".answer-button");
    await expect(answerButtons.first()).toBeVisible();
    if (question === 3) {
      await chooseAndVerifyCompactOption(page, true);
    } else {
      await (question === 7 ? answerButtons.last() : answerButtons.first()).click();
    }
    if (question < 8) {
      await page.getByRole("button", { name: "التالي", exact: true }).click();
    }
  }

  const firstResponsePromise = waitForChecklist(page);
  await page.getByRole("button", { name: "عرض النتيجة", exact: true }).click();
  const firstChecklist = await firstResponsePromise;

  expect(firstChecklist.metadata).toMatchObject({
    catalog_mode: "PORTFOLIO_DEMO_CATALOG",
    publication_state: "SAMPLE_ONLY",
    data_classification: "SYNTHETIC_PORTFOLIO_DEMO",
  });
  expect(firstChecklist.result.applies).toHaveLength(5);
  expect(firstChecklist.result.does_not_apply).toHaveLength(0);
  expect(firstChecklist.result.needs_information).toHaveLength(1);
  expect(firstChecklist.result.journey_guidance.length).toBeGreaterThan(0);
  expect(firstChecklist.result.regulatory_snapshot).toMatchObject({
    catalog_mode: "PORTFOLIO_DEMO",
    publication_count: 0,
  });

  await expect(page.getByRole("heading", { name: "خطوات بدء مشروعك", level: 1 })).toBeVisible();
  await expect(page.locator(".requirement-item.applicable")).toHaveCount(5);
  await expect(page.locator(".requirement-item.missing")).toHaveCount(1);
  await expectActivityReference(
    page,
    "ar",
    "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=1319",
  );
  await expect(
    page.getByText("حدود التغطية · اعرف المزيد", { exact: true }),
  ).toBeVisible();
  await expect(page.getByTestId("demo-result-scope-note")).toHaveCount(1);
  await expect(page.locator('a[href*=".invalid"]')).toHaveCount(0);
  await expect(page.getByText(/مسار نموذجي غير حكومي/)).toHaveCount(0);
  await expect(page.locator(".final-outcome")).toBeVisible();
  await expectResultsOrder(page);
  await expect(page.locator(".verification-item")).toHaveCount(6);
  const reviewCards = await page.locator(".verification-item").allInnerTexts();
  expect(new Set(reviewCards).size).toBe(reviewCards.length);
  await expectDemoDOMIntegrity(page);
  await auditRenderedLinks(page);

  await page.getByRole("button", { name: "العودة إلى هذا السؤال", exact: true }).first().click();
  await expect(progress).toHaveAttribute("aria-valuenow", "7");
  await expectDemoDOMIntegrity(page);
  await auditRenderedLinks(page);
  await page.locator(".answer-button").first().click();
  await page.getByRole("button", { name: "التالي", exact: true }).click();
  await expect(progress).toHaveAttribute("aria-valuenow", "8");
  const resolvedResponsePromise = waitForChecklist(page);
  await page.getByRole("button", { name: "عرض النتيجة", exact: true }).click();
  const resolvedChecklist = await resolvedResponsePromise;

  expect(resolvedChecklist.result.applies).toHaveLength(6);
  expect(resolvedChecklist.result.does_not_apply).toHaveLength(0);
  expect(resolvedChecklist.result.needs_information).toHaveLength(0);
  await expect(page.locator(".requirement-item.applicable")).toHaveCount(6);
  await expect(page.locator(".requirement-item.missing")).toHaveCount(0);
  await expectActivityReference(
    page,
    "ar",
    "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=1319",
  );
  const arabicCompletionBoxes = page.getByRole("checkbox", { name: "أنجزت هذا" });
  await expect(arabicCompletionBoxes).toHaveCount(6);
  for (let index = 0; index < 6; index += 1) {
    await arabicCompletionBoxes.nth(index).check();
  }
  await expect(page.getByRole("heading", { name: "أنهيت متابعة خطوات القائمة" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "راجع هذه الأمور" })).toBeVisible();
  await expectDemoDOMIntegrity(page);
  await auditRenderedLinks(page);
  expectRuntimeClean(faults);
});

test("English guided flow and AI-unavailable fallback work without an OpenAI key", async ({
  page,
}) => {
  const faults = collectRuntimeFaults(page);
  await page.goto("/en");

  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
  await expect(page.getByText("Independent portfolio demo. Not a government service.")).toBeVisible();
  await expectDemoDOMIntegrity(page);
  await auditRenderedLinks(page);

  const optionalAI = page.locator("details.optional-ai");
  await optionalAI.locator("summary").click();
  await optionalAI.locator("textarea").fill("I want to open a restaurant with delivery.");
  const unavailableResponse = page.waitForResponse(
    (candidate) =>
      candidate.request().method() === "POST"
      && candidate.url().endsWith("/api/v1/navigator"),
  );
  await optionalAI.getByRole("button", { name: "Interpret description" }).click();
  const aiResponse = await unavailableResponse;
  expect(aiResponse.status()).toBe(503);
  const aiBody = (await aiResponse.json()) as { error: { code: string } };
  expect(aiBody.error.code).toBe("AI_UNAVAILABLE");
  await expect(optionalAI.getByText(/AI assistance is unavailable/i)).toBeVisible();
  expect(faults.consoleErrors).toHaveLength(1);
  expect(faults.consoleErrors[0]).toContain(
    "Failed to load resource: the server responded with a status of 503",
  );
  faults.consoleErrors.length = 0;
  await expectDemoDOMIntegrity(page);
  await auditRenderedLinks(page);

  await startActivity(page, "Cloud kitchen", "Start questions");
  await expect(page.getByText(/If you do not know an answer, do not guess/i)).toBeVisible();
  const progress = page.getByRole("progressbar", { name: "Question progress" });
  await expect(progress).toHaveAttribute("aria-valuemax", "7");
  await expectDemoDOMIntegrity(page);
  await auditRenderedLinks(page);
  for (let question = 1; question <= 7; question += 1) {
    await expect(progress).toHaveAttribute("aria-valuenow", String(question));
    await page.locator(".answer-button").first().click();
    if (question < 7) {
      await page.getByRole("button", { name: "Next", exact: true }).click();
    }
  }

  const responsePromise = waitForChecklist(page);
  await page.getByRole("button", { name: "Show results", exact: true }).click();
  const checklist = await responsePromise;
  expect(checklist.result.applies).toHaveLength(5);
  expect(checklist.result.does_not_apply).toHaveLength(0);
  expect(checklist.result.needs_information).toHaveLength(0);
  await expect(page.getByRole("heading", { name: "Your business-launch steps", level: 1 })).toBeVisible();
  await expect(page.locator(".requirement-item.applicable")).toHaveCount(5);
  await expectActivityReference(
    page,
    "en",
    "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=859397",
  );
  await expect(page.getByTestId("demo-result-scope-note")).toHaveCount(1);
  await expect(page.locator('a[href*=".invalid"]')).toHaveCount(0);
  await expect(page.getByText(/non-government sample route/i)).toHaveCount(0);
  const englishCompletionBoxes = page.getByRole("checkbox", { name: "I've completed this" });
  await expect(englishCompletionBoxes).toHaveCount(5);
  for (let index = 0; index < 5; index += 1) {
    await englishCompletionBoxes.nth(index).check();
  }
  await expect(page.getByRole("heading", { name: "You finished following up on the checklist steps" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Review these topics" })).toBeVisible();
  await expectDemoDOMIntegrity(page);
  await auditRenderedLinks(page);
  expectRuntimeClean(faults);
});

test("About and mobile views keep the full bilingual demo boundary without a banner", async ({ page }) => {
  const faults = collectRuntimeFaults(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/ar");
  await expect(page.getByText("نسخة تجريبية مستقلة وليست منصة حكومية.")).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await expectDemoDOMIntegrity(page);
  await auditRenderedLinks(page);

  await page.goto("/ar/about");

  await expect(page.getByTestId("portfolio-demo-notice")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "حول دليل تأسيس المنشآت" })).toBeVisible();
  await expect(page.getByText(/هذا مشروع مستقل غير تابع لأي جهة حكومية/)).toBeVisible();
  await expect(page.getByRole("heading", { name: "كيف يمكن أن يتطور الدليل؟" })).toBeVisible();
  await expect(page.getByText(/هذه رؤية مستقبلية وليست ميزات متاحة الآن/)).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await expectDemoDOMIntegrity(page);
  await auditRenderedLinks(page);

  await page.goto("/en/about");
  await expect(page.getByTestId("portfolio-demo-notice")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "About the Business Launch Guide" })).toBeVisible();
  await expect(page.getByText(/This is an independent project/)).toBeVisible();
  await expect(page.getByRole("heading", { name: "How could the guide evolve?" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await expectDemoDOMIntegrity(page);
  await auditRenderedLinks(page);
  expectRuntimeClean(faults);
});

test("Arabic coffee-shop workflow remains usable throughout a mobile viewport", async ({ page }) => {
  const faults = collectRuntimeFaults(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/ar");

  await expect(page.locator("html")).toHaveAttribute("lang", "ar");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expectNoHorizontalOverflow(page);
  await expectDemoDOMIntegrity(page);
  await auditRenderedLinks(page);

  await startActivity(page, "مقهى", "ابدأ الأسئلة");
  const progress = page.getByRole("progressbar", { name: "تقدم الأسئلة" });
  await expect(progress).toHaveAttribute("aria-valuemax", "7");
  await page.getByRole("button", { name: "توضيح المقصود بالسؤال" }).click();
  await expect(page.getByText("ما المقصود؟", { exact: true })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await page.keyboard.press("Escape");
  await expectDemoDOMIntegrity(page);
  await auditRenderedLinks(page);

  for (let question = 1; question <= 7; question += 1) {
    await expect(progress).toHaveAttribute("aria-valuenow", String(question));
    await expectNoHorizontalOverflow(page);
    const answerButtons = page.locator(".answer-button");
    await expect(answerButtons.first()).toBeVisible();
    if (question === 3) {
      await chooseAndVerifyCompactOption(page, false);
    } else {
      await answerButtons.first().click();
    }
    if (question < 7) {
      await page.getByRole("button", { name: "التالي", exact: true }).click();
    }
  }

  const responsePromise = waitForChecklist(page);
  await page.getByRole("button", { name: "عرض النتيجة", exact: true }).click();
  const checklist = await responsePromise;

  expect(checklist.metadata).toMatchObject({
    catalog_mode: "PORTFOLIO_DEMO_CATALOG",
    publication_state: "SAMPLE_ONLY",
    data_classification: "SYNTHETIC_PORTFOLIO_DEMO",
  });
  expect(checklist.result.applies.length).toBeGreaterThan(0);
  await expect(page.getByRole("heading", { name: "خطوات بدء مشروعك", level: 1 })).toBeVisible();
  await expect(page.locator(".requirement-item.applicable")).toHaveCount(
    checklist.result.applies.length,
  );
  await expectActivityReference(
    page,
    "ar",
    "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=1770",
  );
  await expectNoHorizontalOverflow(page);
  await expectDemoDOMIntegrity(page);
  await auditRenderedLinks(page);
  expectRuntimeClean(faults);
});

async function startActivity(
  page: Page,
  activityName: string,
  startLabel: string,
): Promise<void> {
  await expect(page.locator(".activity-description, .activity-secondary-name, .activity-guidance-label")).toHaveCount(0);
  const activityChoices = page.locator(".activity-choice");
  await expect(activityChoices).toHaveCount(3);
  const activityBoxes = await activityChoices.evaluateAll((elements) => elements.map((element) => {
    const box = element.getBoundingClientRect();
    return { height: box.height, width: box.width };
  }));
  expect(activityBoxes.every((box) => box.height <= 80 && box.width < 240)).toBe(true);

  const card = page.locator(".activity-choice").filter({
    has: page.getByText(activityName, { exact: true }),
  });
  await expect(card).toHaveCount(1);
  await card.click();
  await page.getByRole("button", { name: startLabel, exact: true }).click();
}

async function chooseAndVerifyCompactOption(page: Page, verifyHover: boolean): Promise<void> {
  const grid = page.locator(".answer-grid.short-options");
  await expect(grid).toHaveCount(1);
  const options = grid.locator(".answer-button");
  await expect(options).toHaveCount(3);

  const boxes = await options.evaluateAll((elements) => elements.map((element) => {
    const box = element.getBoundingClientRect();
    return { height: box.height, width: box.width };
  }));
  expect(boxes.every((box) => box.height <= 54 && box.width < 200)).toBe(true);

  const first = options.first();
  if (verifyHover) {
    const defaultStyle = await first.evaluate((element) => {
      const style = getComputedStyle(element);
      return { background: style.backgroundColor, border: style.borderColor };
    });
    await first.hover();
    await page.waitForTimeout(180);
    const hoverStyle = await first.evaluate((element) => {
      const style = getComputedStyle(element);
      return { background: style.backgroundColor, border: style.borderColor };
    });
    expect(hoverStyle).not.toEqual(defaultStyle);
    expect(hoverStyle.background).not.toBe("rgb(11, 90, 71)");
    expect(hoverStyle.background).not.toBe("rgb(7, 69, 54)");
  }

  await first.focus();
  await page.keyboard.press("Tab");
  await page.keyboard.press("Shift+Tab");
  await expect(first).toBeFocused();
  const focusStyle = await first.evaluate((element) => {
    const style = getComputedStyle(element);
    return { outlineStyle: style.outlineStyle, outlineWidth: style.outlineWidth };
  });
  expect(focusStyle.outlineStyle).toBe("solid");
  expect(Number.parseFloat(focusStyle.outlineWidth)).toBeGreaterThanOrEqual(3);

  await first.click();
  await expect(first).toHaveAttribute("aria-pressed", "true");
  await expect(first.locator(".answer-selected-mark")).toBeVisible();
  const selectedBackground = await first.evaluate((element) => getComputedStyle(element).backgroundColor);
  expect(selectedBackground).not.toBe("rgb(11, 90, 71)");
  expect(selectedBackground).not.toBe("rgb(7, 69, 54)");
}

async function expectResultsOrder(page: Page): Promise<void> {
  const order = await page.locator(
    "#required-title, #missing-title, #verification-title, [data-testid='activity-official-reference'], .final-outcome",
  ).evaluateAll((elements) => elements.map((element) => {
    if (element.id) return element.id;
    if (element.getAttribute("data-testid")) return "activity-reference";
    return "final-outcome";
  }));
  expect(order).toEqual([
    "required-title",
    "missing-title",
    "verification-title",
    "activity-reference",
    "final-outcome",
  ]);
}

async function waitForChecklist(page: Page): Promise<ChecklistEnvelope> {
  const response = await page.waitForResponse(
    (candidate) =>
      candidate.request().method() === "POST"
      && candidate.url().endsWith("/api/v1/checklist"),
  );
  expect(response.ok()).toBe(true);
  return (await response.json()) as ChecklistEnvelope;
}

async function expectDemoDOMIntegrity(page: Page): Promise<void> {
  const snapshot = await page.evaluate(() => {
    const visibleBlocks = Array.from(
      document.body.querySelectorAll<HTMLElement>("h1, h2, h3, h4, h5, p, li, dt, dd, strong, span"),
    )
      .filter((element) => {
        const style = window.getComputedStyle(element);
        return style.display !== "none"
          && style.visibility !== "hidden"
          && element.getClientRects().length > 0;
      })
      .map((element) => element.innerText.trim())
      .filter(Boolean);
    return {
      visibleText: document.body.innerText,
      visibleBlocks,
      repeatedCardDestinations: Array.from(
        document.querySelectorAll<HTMLElement>(".requirement-item, .verification-item"),
      ).filter((container) => {
        const destinations = Array.from(container.querySelectorAll<HTMLAnchorElement>("a[href]"))
          .map((anchor) => anchor.href);
        return new Set(destinations).size !== destinations.length;
      }).length,
    };
  });
  const normalizedVisibleText = snapshot.visibleText.toLowerCase();

  for (const forbidden of forbiddenDemoText) {
    expect(
      normalizedVisibleText,
      `visible page contains forbidden demo wording: ${forbidden}`,
    ).not.toContain(forbidden.toLowerCase());
  }

  const visibleText = snapshot.visibleBlocks.join("\n");
  const showsSampleBoundary = /بيانات نموذجية|sample data/i.test(visibleText);
  if (showsSampleBoundary) {
    for (const claim of contradictoryCurrentRecordClaims) {
      expect(visibleText, `sample-data screen contains contradictory official-record claim: ${claim}`).not.toMatch(
        claim,
      );
    }
    await expect(page.locator('[data-source-classification="governed"]')).toHaveCount(0);
  }

  await expect(page.locator('a[href*=".invalid"]')).toHaveCount(0);
  await expect(page.locator('a[href^="javascript:"]')).toHaveCount(0);
  await expect(page.locator('a[href^="data:"]')).toHaveCount(0);
  await expect(page.locator('[data-source-classification="synthetic-demo"]')).toHaveCount(0);
  expect(snapshot.repeatedCardDestinations, "a result card repeats the same destination").toBe(0);
}

async function expectActivityReference(
  page: Page,
  locale: "ar" | "en",
  expectedURL: string,
): Promise<void> {
  const reference = page.getByTestId("activity-official-reference");
  await expect(reference).toHaveCount(1);
  await expect(
    reference.getByRole("heading", {
      name: locale === "ar" ? "المصدر الرسمي للنشاط" : "Official activity reference",
    }),
  ).toBeVisible();
  await expect(reference).toContainText(
    locale === "ar"
      ? "يمكنك مراجعة صفحة النشاط الرسمية في منصة بلدي للاطلاع على وصف النشاط والمتطلبات المنشورة للنشاط."
      : "You can review the official Balady activity page for the activity description and published activity requirements.",
  );
  await expect(reference).toContainText(
    locale === "ar"
      ? "وزارة البلديات والإسكان — منصة بلدي"
      : "Ministry of Municipalities and Housing — Balady",
  );

  const officialLink = reference.getByRole("link", {
    name: locale === "ar" ? /فتح صفحة النشاط الرسمية/ : /Open official activity page/,
  });
  await expect(officialLink).toHaveAttribute("href", expectedURL);
  await expect(officialLink).toHaveAttribute("target", "_blank");
  await expect(officialLink).toHaveAttribute("rel", "noopener noreferrer");
  await expect(officialLink).toHaveAttribute(
    "data-source-classification",
    "official-activity-reference",
  );

  const methodology = page.getByRole("link", {
    name: locale === "ar" ? "عن بيانات النسخة التجريبية" : "About the demo data",
  });
  await expect(methodology).toHaveCount(1);
  await expect(methodology).toHaveAttribute("href", `/${locale}/about#methodology`);
  await expect(page.locator(".requirement-item a[href]")).toHaveCount(0);
  await expect(page.locator(".actionability-details a[href]")).toHaveCount(0);
  await expect(page.locator(".verification-list a[href]")).toHaveCount(0);
  await expect(page.locator(".final-outcome a[href]")).toHaveCount(0);
  await expect(page.locator('[data-source-classification="official-activity-reference"]')).toHaveCount(1);
}

async function auditRenderedLinks(page: Page): Promise<void> {
  const links = await page.locator("a[href]").evaluateAll((anchors): RenderedLink[] =>
    anchors.map((anchor) => {
      const element = anchor as HTMLAnchorElement;
      return {
        absoluteHref: element.href,
        rawHref: element.getAttribute("href") ?? "",
        text: element.textContent?.trim() ?? "",
        target: element.getAttribute("target"),
        rel: element.getAttribute("rel"),
        sourceClassification: element.getAttribute("data-source-classification"),
      };
    }),
  );
  expect(links.length, `no rendered links were found on ${page.url()}`).toBeGreaterThan(0);

  const currentURL = new URL(page.url());
  const uniqueLinks = new Map(links.map((link) => [link.absoluteHref, link]));
  for (const link of uniqueLinks.values()) {
    const normalizedHref = link.rawHref.trim().toLowerCase();
    expect(normalizedHref, `unsafe link text=${JSON.stringify(link.text)}`).not.toContain(".invalid");
    expect(normalizedHref, `unsafe link text=${JSON.stringify(link.text)}`).not.toMatch(
      /^(?:javascript|data):/,
    );

    const target = new URL(link.absoluteHref);
    expect(["http:", "https:"], `unsupported link scheme: ${link.absoluteHref}`).toContain(
      target.protocol,
    );
    expect(target.hostname.toLowerCase(), `placeholder link: ${link.absoluteHref}`).not.toMatch(
      /(?:^|\.)invalid$|(?:^|\.)example\.(?:com|org|net|test)$/,
    );
    if (target.origin !== currentURL.origin) {
      expect(
        officialActivityReferenceURLs.has(link.absoluteHref),
        `public demo emitted an unapproved external destination: ${link.absoluteHref}`,
      ).toBe(true);
      expect(target.protocol).toBe("https:");
      expect(target.hostname).toBe("services.balady.gov.sa");
      expect(link.target).toBe("_blank");
      expect(link.rel?.split(/\s+/)).toEqual(expect.arrayContaining(["noopener", "noreferrer"]));
      expect(link.sourceClassification).toBe("official-activity-reference");
      continue;
    }

    const route = `${target.origin}${target.pathname}${target.search}`;
    if (!verifiedRoutes.has(route)) {
      const response = await page.request.get(route);
      expect(response.status(), `broken rendered link: ${link.absoluteHref}`).toBeLessThan(400);
      verifiedRoutes.add(route);
    }

    if (!target.hash) continue;
    const fragment = decodeURIComponent(target.hash.slice(1));
    expect(fragment, `empty fragment link: ${link.absoluteHref}`).not.toBe("");
    if (target.pathname === currentURL.pathname && target.search === currentURL.search) {
      await expect(page.locator(`[id=${JSON.stringify(fragment)}]`)).toHaveCount(1);
      continue;
    }

    if (!verifiedFragmentDestinations.has(target.href)) {
      const probe = await page.context().newPage();
      try {
        const response = await probe.goto(target.href, { waitUntil: "domcontentloaded" });
        expect(response?.status(), `broken fragment destination: ${link.absoluteHref}`).toBeLessThan(
          400,
        );
        await expect(probe.locator(`[id=${JSON.stringify(fragment)}]`)).toHaveCount(1);
      } finally {
        await probe.close();
      }
      verifiedFragmentDestinations.add(target.href);
    }
  }
}

function collectRuntimeFaults(page: Page): {
  consoleErrors: string[];
  pageErrors: string[];
  failedLocalRequests: string[];
} {
  const faults = {
    consoleErrors: [] as string[],
    pageErrors: [] as string[],
    failedLocalRequests: [] as string[],
  };
  page.on("console", (message) => {
    if (message.type() === "error") faults.consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => faults.pageErrors.push(error.message));
  page.on("requestfailed", (request) => {
    const url = request.url();
    if (url.startsWith("http://127.0.0.1") || url.startsWith("http://localhost")) {
      faults.failedLocalRequests.push(`${request.method()} ${url}`);
    }
  });
  return faults;
}

function expectRuntimeClean(faults: ReturnType<typeof collectRuntimeFaults>): void {
  expect(faults.consoleErrors).toEqual([]);
  expect(faults.pageErrors).toEqual([]);
  expect(faults.failedLocalRequests).toEqual([]);
}

async function expectNoHorizontalOverflow(page: Page): Promise<void> {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);
}
