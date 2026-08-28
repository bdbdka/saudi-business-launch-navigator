"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ActivitySelector } from "@/components/activity-selector";
import { CatalogPresentationProvider } from "@/components/catalog-mode-context";
import { ChecklistResults } from "@/components/checklist-results";
import { DemoNotice } from "@/components/demo-notice";
import { Header } from "@/components/header";
import { Footer, Hero } from "@/components/landing";
import { OptionalAIEntry } from "@/components/optional-ai-entry";
import { Questionnaire } from "@/components/questionnaire";
import { NavigatorAPIError, navigatorAPI } from "@/lib/api/client";
import { catalogBoundaryMatchesBuild } from "@/lib/catalog-presentation";
import type {
  Activity,
  CatalogBoundary,
  ChecklistResult,
  Question,
  QuestionFactCode,
  QuestionnaireAnswers,
} from "@/lib/api/types";
import { getDictionary, type Locale } from "@/lib/i18n";

type Stage = "activities" | "questionnaire" | "results";

export function NavigatorApp({ initialLocale }: { initialLocale: Locale }) {
  const [locale, setLocale] = useState<Locale>(initialLocale);
  const [stage, setStage] = useState<Stage>("activities");
  const [activities, setActivities] = useState<Activity[]>([]);
  const [catalogBoundary, setCatalogBoundary] = useState<CatalogBoundary | null>(null);
  const [activitiesLoading, setActivitiesLoading] = useState(true);
  const [activitiesFailed, setActivitiesFailed] = useState(false);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [questionnaireReady, setQuestionnaireReady] = useState(false);
  const [answers, setAnswers] = useState<QuestionnaireAnswers>({});
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [questionnaireLoading, setQuestionnaireLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [checklistFailed, setChecklistFailed] = useState(false);
  const [result, setResult] = useState<ChecklistResult | null>(null);
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [aiText, setAIText] = useState("");
  const [aiLoading, setAILoading] = useState(false);
  const [aiUnavailable, setAIUnavailable] = useState(false);
  const [aiClarifications, setAIClarifications] = useState<string[]>([]);
  const [aiExplanation, setAIExplanation] = useState<string[]>([]);
  const workflowRef = useRef<HTMLDivElement>(null);
  const copy = useMemo(() => getDictionary(locale), [locale]);
  const acceptCatalogBoundary = useCallback((metadata: CatalogBoundary) => {
    if (!catalogBoundaryMatchesBuild(metadata)) {
      throw new Error("catalog presentation boundary mismatch");
    }
    setCatalogBoundary(metadata);
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = locale === "ar" ? "rtl" : "ltr";
  }, [locale]);

  const loadActivities = useCallback(async () => {
    setActivitiesLoading(true);
    setActivitiesFailed(false);
    try {
      const response = await navigatorAPI.activities();
      acceptCatalogBoundary(response.metadata);
      setActivities(response.activities);
    } catch {
      setActivitiesFailed(true);
    } finally {
      setActivitiesLoading(false);
    }
  }, [acceptCatalogBoundary]);

  useEffect(() => {
    let cancelled = false;
    navigatorAPI.activities()
      .then((response) => {
        if (cancelled) return;
        acceptCatalogBoundary(response.metadata);
        setActivities(response.activities);
      })
      .catch(() => {
        if (!cancelled) setActivitiesFailed(true);
      })
      .finally(() => {
        if (!cancelled) setActivitiesLoading(false);
      });
    return () => { cancelled = true; };
  }, [acceptCatalogBoundary]);

  useEffect(() => {
    if (stage !== "activities") workflowRef.current?.focus();
  }, [stage]);

  function changeLocale(nextLocale: Locale) {
    setLocale(nextLocale);
    document.documentElement.lang = nextLocale;
    document.documentElement.dir = nextLocale === "ar" ? "rtl" : "ltr";
    const nextCopy = getDictionary(nextLocale);
    document.title = nextCopy.metadata.homeTitle;
    document.querySelector('meta[name="description"]')?.setAttribute("content", nextCopy.metadata.homeDescription);
    document.querySelector('meta[property="og:title"]')?.setAttribute("content", nextCopy.metadata.homeTitle);
    document.querySelector('meta[property="og:description"]')?.setAttribute("content", nextCopy.metadata.homeDescription);
    document.querySelector('meta[property="og:locale"]')?.setAttribute("content", nextLocale === "ar" ? "ar_SA" : "en_US");
    const suffix = `${window.location.search}${window.location.hash}`;
    window.history.replaceState(window.history.state, "", `/${nextLocale}${suffix}`);
  }

  async function selectActivity(activity: Activity, preservedAnswers: QuestionnaireAnswers = {}) {
    setSelectedActivity(activity);
    setAnswers(preservedAnswers);
    setQuestions([]);
    setQuestionnaireReady(false);
    setCurrentQuestion(0);
    setWorkflowError(null);
    setChecklistFailed(false);
    setQuestionnaireLoading(true);
    setStage("questionnaire");
    try {
      const response = await navigatorAPI.questionnaire(activity.code);
      acceptCatalogBoundary(response.metadata);
      setQuestions(response.questionnaire.questions);
      setQuestionnaireReady(true);
    } catch (error) {
      setWorkflowError(displayError(error, copy.error.backend, copy.error.validation));
    } finally {
      setQuestionnaireLoading(false);
    }
  }

  async function submitChecklist() {
    if (!selectedActivity) return;
    setSubmitting(true);
    setWorkflowError(null);
    setChecklistFailed(false);
    try {
      const response = await navigatorAPI.checklist(selectedActivity.code, answers);
      acceptCatalogBoundary(response.metadata);
      setResult(response.result);
      setAIExplanation([]);
      setStage("results");
    } catch (error) {
      setChecklistFailed(true);
      setWorkflowError(displayError(error, copy.error.backend, copy.error.validation));
    } finally {
      setSubmitting(false);
    }
  }

  async function describeBusiness() {
    const value = aiText.trim();
    if (!value) return;
    setAILoading(true);
    setAIUnavailable(false);
    setAIClarifications([]);
    setWorkflowError(null);
    try {
      const response = await navigatorAPI.navigate(value, locale);
      acceptCatalogBoundary(response.metadata);
      const interpretedAnswers = Object.fromEntries(
        response.interpretation.facts.map((fact) => [fact.code, fact.value]),
      ) as QuestionnaireAnswers;
      setAnswers(interpretedAnswers);
      setAIClarifications(response.clarifications.map((item) => locale === "ar" ? item.question_ar : item.question_en));
      setAIExplanation(response.explanation
        ? [...response.explanation.items.map((item) => item.summary), response.explanation.ai_coverage_summary]
        : []);
      if (response.authoritative_result) {
        setResult(response.authoritative_result);
        setSelectedActivity(response.authoritative_result.activity);
        setStage("results");
        try {
          const questionnaire = await navigatorAPI.questionnaire(response.authoritative_result.activity.code);
          acceptCatalogBoundary(questionnaire.metadata);
          setQuestions(questionnaire.questionnaire.questions);
          setQuestionnaireReady(true);
        } catch {
          setQuestionnaireReady(false);
        }
      } else if (response.interpretation.activity_code) {
        const activity = activities.find((item) => item.code === response.interpretation.activity_code);
        if (activity) await selectActivity(activity, interpretedAnswers);
      }
    } catch (error) {
      if (
        error instanceof NavigatorAPIError &&
        ["AI_UNAVAILABLE", "AI_TIMEOUT", "AI_RATE_LIMITED", "AI_AUTHENTICATION_FAILED"].includes(error.code)
      ) {
        setAIUnavailable(true);
      } else {
        setWorkflowError(displayError(error, copy.error.backend, copy.error.validation));
      }
    } finally {
      setAIText("");
      setAILoading(false);
    }
  }

  async function answerMissing(factCode: QuestionFactCode) {
    let availableQuestions = questions;
    if (!questionnaireReady && selectedActivity) {
      try {
        const response = await navigatorAPI.questionnaire(selectedActivity.code);
        acceptCatalogBoundary(response.metadata);
        availableQuestions = response.questionnaire.questions;
        setQuestions(availableQuestions);
        setQuestionnaireReady(true);
      } catch (error) {
        setWorkflowError(displayError(error, copy.error.backend, copy.error.validation));
        return;
      }
    }
    const index = availableQuestions.findIndex((question) => question.fact_code === factCode);
    if (index >= 0) {
      setCurrentQuestion(index);
      setStage("questionnaire");
      requestAnimationFrame(() => document.getElementById("navigator")?.scrollIntoView());
    }
  }

  function changeActivity() {
    setWorkflowError(null);
    setChecklistFailed(false);
    setStage("activities");
  }

  async function editAnswers() {
    if (!selectedActivity) return;
    if (!questionnaireReady) {
      await selectActivity(selectedActivity, answers);
      return;
    }
    setStage("questionnaire");
  }

  function restart() {
    setSelectedActivity(null);
    setQuestions([]);
    setQuestionnaireReady(false);
    setAnswers({});
    setResult(null);
    setChecklistFailed(false);
    setAIExplanation([]);
    setAIClarifications([]);
    setStage("activities");
  }

  return (
    <CatalogPresentationProvider metadata={catalogBoundary} locale={locale}>
      <a className="skip-link" href="#main-content">{locale === "ar" ? "تجاوز إلى المحتوى الرئيسي" : "Skip to main content"}</a>
      <Header locale={locale} copy={copy} onLocaleChange={changeLocale} />
      <DemoNotice metadata={catalogBoundary} locale={locale} />
      <main id="main-content" tabIndex={-1}>
        {stage === "activities" && <Hero copy={copy} />}
        <section className="navigator-section" id="navigator">
          <div className="section-shell">
            <div className="workflow-focus" ref={workflowRef} tabIndex={-1}>
              {stage === "activities" && (
                <ActivitySelector
                  activities={activities}
                  locale={locale}
                  copy={copy}
                  loading={activitiesLoading}
                  error={activitiesFailed ? copy.error.backend : null}
                  onRetry={() => void loadActivities()}
                  onSelect={(activity) => void selectActivity(activity)}
                />
              )}
              {stage === "questionnaire" && questionnaireLoading && (
                    <div className="loading-card" role="status" aria-live="polite">
                      <span className="spinner" aria-hidden="true" /> {copy.questionnaire.loading}
                    </div>
                  )}
              {stage === "questionnaire" && !questionnaireLoading && questionnaireReady && selectedActivity && (
                    <Questionnaire
                      activity={selectedActivity}
                      questions={questions}
                      answers={answers}
                      currentIndex={currentQuestion}
                      locale={locale}
                      copy={copy}
                      submitting={submitting}
                      onAnswer={(code, value) => setAnswers((current) => ({ ...current, [code]: value }))}
                      onBack={() => setCurrentQuestion((current) => Math.max(0, current - 1))}
                      onNext={() => setCurrentQuestion((current) => Math.min(questions.length - 1, current + 1))}
                      onSubmit={() => void submitChecklist()}
                      onChangeActivity={changeActivity}
                    />
                  )}
              {stage === "results" && result && (
                    <ChecklistResults
                      result={result}
                      locale={locale}
                      copy={copy}
                      aiExplanation={aiExplanation}
                      onAnswerMissing={(factCode) => void answerMissing(factCode)}
                      onEdit={() => void editAnswers()}
                      onRestart={restart}
                    />
                  )}
              {workflowError && (
                    <div className="inline-error workflow-error" role="alert" aria-live="assertive">
                      <strong>{checklistFailed ? copy.error.checklistTitle : copy.error.title}</strong>
                      <p>{workflowError}</p>
                      {stage === "questionnaire" && checklistFailed && (
                        <button className="button secondary" type="button" onClick={() => void submitChecklist()}>
                          {copy.error.retry}
                        </button>
                      )}
                      {stage === "questionnaire" && selectedActivity && !questionnaireReady && (
                        <button className="button secondary" type="button" onClick={() => void selectActivity(selectedActivity, answers)}>
                          {copy.error.retry}
                        </button>
                      )}
                    </div>
              )}
            </div>

            {stage === "activities" && (
              <OptionalAIEntry
                copy={copy}
                value={aiText}
                loading={aiLoading}
                unavailable={aiUnavailable}
                clarifications={aiClarifications}
                onChange={setAIText}
                onSubmit={() => void describeBusiness()}
              />
            )}
          </div>
        </section>
      </main>
      <Footer copy={copy} locale={locale} quiet={stage === "questionnaire"} />
    </CatalogPresentationProvider>
  );
}

function displayError(error: unknown, backendMessage: string, validationMessage: string): string {
  if (error instanceof NavigatorAPIError && (error.status === 400 || error.status === 422)) return validationMessage;
  return backendMessage;
}
