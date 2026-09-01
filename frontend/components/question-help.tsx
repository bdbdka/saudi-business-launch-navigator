"use client";

import { type ReactNode, useEffect, useId, useRef, useState } from "react";

export function QuestionHelp({
  children,
  content,
  label,
  labels,
}: {
  children: ReactNode;
  content: { meaning: string; why: string; example?: string };
  label: string;
  labels: { meaning: string; why: string; example: string };
}) {
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  const rootRef = useRef<HTMLSpanElement>(null);
  const helpId = useId();

  useEffect(() => {
    if (!open) return;

    const closeOutside = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
        setPinned(false);
      }
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
        setPinned(false);
      }
    };

    document.addEventListener("pointerdown", closeOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  return (
    <span
      className="question-help"
      ref={rootRef}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) {
          setOpen(false);
          setPinned(false);
        }
      }}
    >
      <span className="question-legend-row">
        <span className="question-title-text">{children}</span>
        <span className="question-help-trigger">
          <button
            type="button"
            className="question-help-button"
            aria-label={label}
            aria-expanded={open}
            aria-controls={helpId}
            onFocus={() => setOpen(true)}
            onPointerEnter={(event) => {
              if (event.pointerType === "mouse") setOpen(true);
            }}
            onPointerLeave={(event) => {
              if (event.pointerType === "mouse" && !pinned) setOpen(false);
            }}
            onClick={() => {
              setPinned((current) => {
                const next = !current;
                setOpen(next);
                return next;
              });
            }}
          >
            <span aria-hidden="true">ⓘ</span>
          </button>
        </span>
      </span>
      {open && (
        <span className="question-tooltip" id={helpId} role="note">
          <strong>{labels.meaning}</strong>
          <span>{content.meaning}</span>
          <strong>{labels.why}</strong>
          <span>{content.why}</span>
          {content.example && (
            <>
              <strong>{labels.example}</strong>
              <span>{content.example}</span>
            </>
          )}
        </span>
      )}
    </span>
  );
}
