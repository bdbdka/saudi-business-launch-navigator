import { useEffect, useRef } from "react";

import { QuestionHelp } from "@/components/question-help";
import type {
  Activity,
  Question,
  QuestionnaireAnswers,
  QuestionFactCode,
} from "@/lib/api/types";
import { formatNumber, type Dictionary, type Locale } from "@/lib/i18n";

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
        <p>{copy.questionnaire.emptyBody}</p>
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
  const questionText = locale === "ar" ? question.question_ar : question.question_en;
  const helpText = locale === "ar" ? question.help_text_ar : question.help_text_en;
  const answerLabels = question.answer_labels;
  const unknownLabel = locale === "ar" ? question.unknown_label_ar : question.unknown_label_en;
  const progressText = `${formatNumber(currentIndex + 1, locale)} ${copy.questionnaire.of} ${formatNumber(questions.length, locale)}`;

  return (
    <section className="question-card" aria-labelledby="question-title" aria-busy={submitting}>
      <div className="question-topline">
        <p className="activity-context"><span>{copy.workflow.questions}</span><strong>{activityName}</strong></p>
        <button className="text-button change-activity" type="button" onClick={onChangeActivity} disabled={submitting}>
          <span aria-hidden="true">←</span>
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

      {currentIndex === 0 && <p className="questionnaire-intro">{copy.questionnaire.intro}</p>}

      <fieldset disabled={submitting}>
        <legend id="question-title" ref={titleRef} tabIndex={-1}>
          <QuestionHelp key={question.fact_code} text={helpText} label={copy.questionnaire.helpLabel}>
            {questionText}
          </QuestionHelp>
        </legend>
        <div className="answer-grid">
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
      <strong>{label}</strong>
      {selected && <span className="answer-selected-mark" aria-hidden="true">✓</span>}
    </button>
  );
}
