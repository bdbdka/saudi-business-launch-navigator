import type { Dictionary } from "@/lib/i18n";

export function OptionalAIEntry({
  copy,
  value,
  loading,
  unavailable,
  clarifications,
  onChange,
  onSubmit,
}: {
  copy: Dictionary;
  value: string;
  loading: boolean;
  unavailable: boolean;
  clarifications: string[];
  onChange: (value: string) => void;
  onSubmit: () => void;
}) {
  return (
    <details className="optional-ai">
      <summary>
        <span>
          <strong>{copy.ai.title}</strong>
          <small>{copy.ai.summary}</small>
        </span>
      </summary>
      <div className="optional-ai-content">
        <p>{copy.ai.body}</p>
        <label htmlFor="business-description">{copy.ai.title}</label>
        <textarea
          id="business-description"
          value={value}
          maxLength={2000}
          rows={3}
          placeholder={copy.ai.placeholder}
          onChange={(event) => onChange(event.target.value)}
        />
        <div className="optional-ai-actions">
          <small>{copy.ai.privacy}</small>
          <button className="button secondary" type="button" onClick={onSubmit} disabled={!value.trim() || loading}>
            {loading ? copy.ai.loading : copy.ai.submit}
          </button>
        </div>
        {unavailable && <p className="ai-unavailable" role="status">{copy.ai.unavailable}</p>}
        {clarifications.length > 0 && (
          <div className="clarification-box" role="status">
            <strong>{copy.ai.clarification}</strong>
            {clarifications.map((item) => <p key={item}>{item}</p>)}
          </div>
        )}
      </div>
    </details>
  );
}
