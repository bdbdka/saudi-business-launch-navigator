import { useEffect, useRef } from "react";

import { useCatalogPresentation } from "@/components/catalog-mode-context";
import { QuestionHelp } from "@/components/question-help";
import type {
  Activity,
  Question,
  QuestionnaireAnswers,
  QuestionFactCode,
} from "@/lib/api/types";
import { formatNumber, type Dictionary, type Locale } from "@/lib/i18n";
import { getQuestionGuidance } from "@/lib/question-guidance";

export function Questionnaire({
  activity,
  questions,
  answers,
  currentIndex,
  locale,
  copy,
  submitting,
  onAnswer,
  onBack,
  onNext,
  onSubmit,
  onChangeActivity,
}: {
  activity: Activity;
  questions: Question[];
  answers: QuestionnaireAnswers;
  currentIndex: number;
  locale: Locale;
  copy: Dictionary;
  submitting: boolean;
  onAnswer: (code: QuestionFactCode, value: boolean | string | null) => void;
  onBack: () => void;
  onNext: () => void;
  onSubmit: () => void;
  onChangeActivity: () => void;
}) {
  const { policy } = useCatalogPresentation();
  const titleRef = useRef<HTMLLegendElement>(null);
  const question = questions[currentIndex];

  useEffect(() => {
    if (question) titleRef.current?.focus();
  }, [currentIndex, question]);

  const activityName = locale === "ar" ? activity.name_ar : activity.name_en;
  if (!question) {
    return (
      <section className="workflow-card empty-questionnaire" aria-labelledby="empty-question-title">
        <h2 id="empty-question-title">{copy.questionnaire.emptyTitle}</h2>
        <p>
          {policy.isPortfolioDemo
            ? policy.text.questionnaireEmptyBody
            : copy.questionnaire.emptyBody}
        </p>
        <div className="question-actions">
          <button className="button secondary" type="button" onClick={onChangeActivity}>{copy.questionnaire.changeActivity}</button>
          <button className="button primary" type="button" onClick={onSubmit} disabled={submitting}>
            {submitting ? copy.results.loading : copy.questionnaire.evaluate}
          </button>
        </div>
      </section>
    );
  }

  const hasAnswer = Object.prototype.hasOwnProperty.call(answers, question.fact_code);
  const answer = answers[question.fact_code];
  const last = currentIndex === questions.length - 1;
  const helpContent = getQuestionGuidance(question.fact_code, locale);
  const questionText = helpContent.prompt
    ?? (locale === "ar" ? question.question_ar : question.question_en);
  const answerLabels = question.answer_labels;
  const unknownLabel = locale === "ar" ? question.unknown_label_ar : question.unknown_label_en;
  const hasShortBooleanChoices = question.data_type !== "enum" && answerLabels
    ? (locale === "ar"
      ? answerLabels.true_ar === copy.questionnaire.yes && answerLabels.false_ar === copy.questionnaire.no
      : answerLabels.true_en === copy.questionnaire.yes && answerLabels.false_en === copy.questionnaire.no)
    : false;
  const progressText = `${copy.questionnaire.question} ${formatNumber(currentIndex + 1, locale)} ${copy.questionnaire.of} ${formatNumber(questions.length, locale)}`;
  const selectedAnswer = selectedAnswerLabel(question, answer, hasAnswer, locale);

  return (
    <section className="question-card" aria-labelledby="question-title" aria-busy={submitting}>
      <h1 className="sr-only">{copy.workflow.questions} — {activityName}</h1>
      <div className="question-topline">
        <p className="activity-context"><span>{copy.workflow.questions}</span><strong>{activityName}</strong></p>
        <button className="text-button change-activity" type="button" onClick={onChangeActivity} disabled={submitting}>
          <span aria-hidden="true">{locale === "ar" ? "→" : "←"}</span>
          <span>{copy.questionnaire.changeActivity}</span>
        </button>
      </div>

      <div className="progress-row">
        <span>{progressText}</span>
        <div
          className="progress-track"
          role="progressbar"
          aria-label={copy.questionnaire.progressLabel}
          aria-valuemin={1}
          aria-valuemax={questions.length}
          aria-valuenow={currentIndex + 1}
          aria-valuetext={progressText}
        >
          <span style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }} />
        </div>
      </div>

      {currentIndex === 0 && (
        <p className="questionnaire-intro">
          {policy.isPortfolioDemo ? policy.text.questionnaireIntro : copy.questionnaire.intro}
        </p>
      )}

      <fieldset disabled={submitting}>
        <legend id="question-title" ref={titleRef} tabIndex={-1}>
          <QuestionHelp
            key={question.fact_code}
            content={helpContent}
            label={copy.questionnaire.helpLabel}
            labels={{
              meaning: copy.questionnaire.meaningLabel,
              why: copy.questionnaire.whyLabel,
              example: copy.questionnaire.exampleLabel,
            }}
          >
            {questionText}
          </QuestionHelp>
        </legend>
        <div className={`answer-grid ${hasShortBooleanChoices ? "short-options" : "long-options"}`}>
          {question.data_type === "enum" ? (
            question.options.map((option) => (
              <AnswerButton
                key={option.value}
                label={locale === "ar" ? option.label_ar : option.label_en}
                selected={hasAnswer && answer === option.value}
                onClick={() => onAnswer(question.fact_code, option.value)}
              />
            ))
          ) : answerLabels ? (
            <>
              <AnswerButton
                label={locale === "ar" ? answerLabels.true_ar : answerLabels.true_en}
                selected={hasAnswer && answer === true}
                onClick={() => onAnswer(question.fact_code, true)}
              />
              <AnswerButton
                label={locale === "ar" ? answerLabels.false_ar : answerLabels.false_en}
                selected={hasAnswer && answer === false}
                onClick={() => onAnswer(question.fact_code, false)}
              />
            </>
          ) : null}
          <AnswerButton label={unknownLabel} selected={hasAnswer && answer === null} onClick={() => onAnswer(question.fact_code, null)} />
        </div>
        <p className="selected-answer-feedback" aria-live="polite">
          {selectedAnswer
            ? copy.questionnaire.selectedTemplate.replace("{answer}", selectedAnswer)
            : "\u00a0"}
        </p>
      </fieldset>

      <div className="question-actions">
        <button className="button secondary" type="button" onClick={onBack} disabled={currentIndex === 0 || submitting}>
          {copy.questionnaire.back}
        </button>
        <button className="button primary" type="button" onClick={last ? onSubmit : onNext} disabled={!hasAnswer || submitting}>
          {submitting ? copy.results.loading : last ? copy.questionnaire.evaluate : copy.questionnaire.next}
        </button>
      </div>
    </section>
  );
}

function selectedAnswerLabel(
  question: Question,
  answer: boolean | string | null | undefined,
  hasAnswer: boolean,
  locale: Locale,
): string | null {
  if (!hasAnswer) return null;
  if (answer === null) {
    return locale === "ar" ? question.unknown_label_ar : question.unknown_label_en;
  }
  if (typeof answer === "string") {
    const option = question.options.find((item) => item.value === answer);
    return option ? (locale === "ar" ? option.label_ar : option.label_en) : null;
  }
  if (!question.answer_labels) return null;
  if (answer) {
    return locale === "ar"
      ? question.answer_labels.true_ar
      : question.answer_labels.true_en;
  }
  return locale === "ar"
    ? question.answer_labels.false_ar
    : question.answer_labels.false_en;
}

function AnswerButton({
  label,
  selected,
  onClick,
}: {
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button className={`answer-button${selected ? " selected" : ""}`} type="button" aria-pressed={selected} onClick={onClick}>
      <span>{label}</span>
      {selected && <span className="answer-selected-mark" aria-hidden="true">✓</span>}
    </button>
  );
}
