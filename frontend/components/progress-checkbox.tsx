import type { Dictionary } from "@/lib/i18n";

export function ProgressCheckbox({
  checked,
  copy,
  onChange,
}: {
  checked: boolean;
  copy: Dictionary;
  onChange: (checked: boolean) => void;
}) {
  return (
    <div className="completion-control">
      <p className={`personal-requirement-status${checked ? " marked" : ""}`}>
        {checked && <span aria-hidden="true">✓</span>}
        {checked ? copy.results.markedCompleteStatus : copy.results.notMarkedComplete}
      </p>
      <label className="completion-check">
        <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
        <span><strong>{copy.results.completed}</strong></span>
      </label>
    </div>
  );
}
