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

test.describe.configure({ mode: "serial" });

test("Arabic demo flow uses the real API, preserves unknown, and supports re-entry", async ({
  page,
}) => {
  const faults = collectRuntimeFaults(page);
  await page.goto("/ar");

  await expect(page.locator("html")).toHaveAttribute("lang", "ar");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.getByTestId("portfolio-demo-notice")).toContainText(
    "نسخة عرض تجريبية",
  );
  await expect(page.getByTestId("portfolio-demo-notice")).toContainText(
    "بيانات نموذجية",
  );

  await startActivity(page, "مطعم", "ابدأ");
  const progress = page.getByRole("progressbar", { name: "تقدم الأسئلة" });
  await expect(progress).toHaveAttribute("aria-valuemax", "8");

  for (let question = 1; question <= 8; question += 1) {
    await expect(progress).toHaveAttribute("aria-valuenow", String(question));
    const answerButtons = page.locator(".answer-button");
    await expect(answerButtons.first()).toBeVisible();
    await (question === 7 ? answerButtons.last() : answerButtons.first()).click();
    if (question < 8) {
      await page.getByRole("button", { name: "التالي", exact: true }).click();
    }
  }

  const firstResponsePromise = waitForChecklist(page);
  await page.getByRole("button", { name: "عرض قائمتي", exact: true }).click();
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

  await expect(page.getByRole("heading", { name: "قائمة بدء مشروعك" })).toBeVisible();
  await expect(page.locator(".requirement-item.applicable")).toHaveCount(5);
  await expect(page.locator(".requirement-item.missing")).toHaveCount(1);
  await expect(
    page.getByText("حدود بيانات العرض النموذجية · اعرف المزيد", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: /رابط تجريبي غير حكومي/ }).first(),
  ).toHaveAttribute("href", "https://example.invalid/portfolio-demo");
  await expect(page.locator(".final-outcome")).toBeVisible();

  await page.getByRole("button", { name: "أجب الآن", exact: true }).first().click();
  await expect(progress).toHaveAttribute("aria-valuenow", "7");
  await page.locator(".answer-button").first().click();
  await page.getByRole("button", { name: "التالي", exact: true }).click();
  await expect(progress).toHaveAttribute("aria-valuenow", "8");
  const resolvedResponsePromise = waitForChecklist(page);
  await page.getByRole("button", { name: "عرض قائمتي", exact: true }).click();
  const resolvedChecklist = await resolvedResponsePromise;

  expect(resolvedChecklist.result.applies).toHaveLength(6);
  expect(resolvedChecklist.result.does_not_apply).toHaveLength(0);
  expect(resolvedChecklist.result.needs_information).toHaveLength(0);
  await expect(page.locator(".requirement-item.applicable")).toHaveCount(6);
  await expect(page.locator(".requirement-item.missing")).toHaveCount(0);
  expectRuntimeClean(faults);
});

test("English guided flow and AI-unavailable fallback work without an OpenAI key", async ({
  page,
}) => {
  const faults = collectRuntimeFaults(page);
  await page.goto("/en");

  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
  await expect(page.getByTestId("portfolio-demo-notice")).toContainText("Portfolio demo");

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
  expect(faults.consoleErrors).toEqual([
    "Failed to load resource: the server responded with a status of 503 (Service Unavailable)",
  ]);
  faults.consoleErrors.length = 0;

  await startActivity(page, "Cloud kitchen", "Start");
  const progress = page.getByRole("progressbar", { name: "Question progress" });
  await expect(progress).toHaveAttribute("aria-valuemax", "7");
  for (let question = 1; question <= 7; question += 1) {
    await expect(progress).toHaveAttribute("aria-valuenow", String(question));
    await page.locator(".answer-button").first().click();
    if (question < 7) {
      await page.getByRole("button", { name: "Next", exact: true }).click();
    }
  }

  const responsePromise = waitForChecklist(page);
  await page.getByRole("button", { name: "See my checklist", exact: true }).click();
  const checklist = await responsePromise;
  expect(checklist.result.applies).toHaveLength(5);
  expect(checklist.result.does_not_apply).toHaveLength(0);
  expect(checklist.result.needs_information).toHaveLength(0);
  await expect(page.getByRole("heading", { name: "Your business launch checklist" })).toBeVisible();
  await expect(page.locator(".requirement-item.applicable")).toHaveCount(5);
  await expect(
    page.getByRole("link", { name: /Non-government demo link/ }).first(),
  ).toHaveAttribute("href", "https://example.invalid/portfolio-demo");
  expectRuntimeClean(faults);
});

test("About and mobile views retain the bilingual demo boundary", async ({ page }) => {
  const faults = collectRuntimeFaults(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/ar/about");

  await expect(page.getByTestId("portfolio-demo-notice")).toContainText(
    "نسخة عرض تجريبية",
  );
  await expect(page.getByRole("heading", { name: "حول دليل تأسيس المنشآت" })).toBeVisible();
  await expectNoHorizontalOverflow(page);

  await page.goto("/en/about");
  await expect(page.getByTestId("portfolio-demo-notice")).toContainText("Portfolio demo");
  await expect(page.getByRole("heading", { name: "About the Business Launch Guide" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  expectRuntimeClean(faults);
});

async function startActivity(
  page: Page,
  activityName: string,
  startLabel: string,
): Promise<void> {
  await page.getByRole("button", { name: activityName, exact: true }).click();
  await page.getByRole("button", { name: startLabel, exact: true }).click();
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
