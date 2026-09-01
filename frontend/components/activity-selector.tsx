import { useMemo, useState } from "react";

import type { Activity, ActivityCode } from "@/lib/api/types";
import type { Dictionary, Locale } from "@/lib/i18n";

const activityOrder: ActivityCode[] = ["coffee_shop", "restaurant", "cloud_kitchen"];

export function ActivitySelector({
  activities,
  locale,
  copy,
  loading,
  warming,
  error,
  onRetry,
  onSelect,
}: {
  activities: Activity[];
  locale: Locale;
  copy: Dictionary;
  loading: boolean;
  warming: boolean;
  error: string | null;
  onRetry: () => void;
  onSelect: (activity: Activity) => void;
}) {
  const [selectedCode, setSelectedCode] = useState<ActivityCode | null>(null);
  const supportedActivities = useMemo(
    () => activityOrder
      .map((code) => activities.find((activity) => activity.code === code))
      .filter((activity): activity is Activity => activity !== undefined),
    [activities],
  );
  const selected = supportedActivities.find((activity) => activity.code === selectedCode);

  return (
    <section className="activity-panel" aria-labelledby="activity-title" aria-busy={loading}>
      <div className="section-heading">
        <p className="stage-label">{copy.workflow.activity}</p>
        <h2 id="activity-title">{copy.activities.title}</h2>
        <p>{copy.activities.body}</p>
      </div>
      {loading ? (
        <div role={warming ? undefined : "status"} aria-live={warming ? undefined : "polite"}>
          <span className="sr-only">{copy.activities.loading}</span>
          <div className="activity-grid" aria-hidden="true">
            {[1, 2, 3].map((item) => <div className="activity-choice skeleton" key={item} />)}
          </div>
        </div>
      ) : error ? (
        <div className="inline-error" role="alert">
          <strong>{copy.error.title}</strong>
          <p>{error}</p>
          <button className="button secondary" type="button" onClick={onRetry}>{copy.activities.retry}</button>
        </div>
      ) : supportedActivities.length === 0 ? (
        <p className="empty-state">{copy.activities.empty}</p>
      ) : (
        <>
          <div className="activity-grid" role="group" aria-label={copy.activities.title}>
            {supportedActivities.map((activity) => {
              const active = activity.code === selectedCode;
              const primaryName = locale === "ar" ? activity.name_ar : activity.name_en;
              return (
                <button
                  className={`activity-choice${active ? " selected" : ""}`}
                  type="button"
                  key={activity.code}
                  aria-label={primaryName}
                  aria-pressed={active}
                  onClick={() => setSelectedCode(activity.code)}
                >
                  <span className="activity-choice-heading">
                    <strong>{primaryName}</strong>
                    {active && <span className="activity-selected-mark">✓ {copy.activities.selected}</span>}
                  </span>
                </button>
              );
            })}
          </div>
          <button
            className="button primary activity-start"
            type="button"
            disabled={!selected}
            onClick={() => selected && onSelect(selected)}
          >
            {copy.activities.start}
          </button>
        </>
      )}
    </section>
  );
}
