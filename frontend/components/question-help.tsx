"use client";

import { type ReactNode, useEffect, useId, useRef, useState } from "react";

export function QuestionHelp({
  children,
  text,
  label,
}: {
  children: ReactNode;
  text: string;
  label: string;
}) {
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  const rootRef = useRef<HTMLSpanElement>(null);
  const tooltipId = useId();

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

  const closeIfNotPinned = () => {
    if (!pinned) setOpen(false);
  };

  return (
    <span className="question-help" ref={rootRef}>
      <span className="question-legend-row">
        <span className="question-title-text">{children}</span>
        <span
          className="question-help-trigger"
          onMouseEnter={() => setOpen(true)}
          onMouseLeave={closeIfNotPinned}
        >
          <button
            type="button"
            className="question-help-button"
            aria-label={label}
            aria-expanded={open}
            aria-controls={tooltipId}
            aria-describedby={open ? tooltipId : undefined}
            onFocus={() => setOpen(true)}
            onBlur={closeIfNotPinned}
            onClick={() => {
              const nextPinned = !pinned;
              setPinned(nextPinned);
              setOpen(nextPinned);
            }}
          >
            <span aria-hidden="true">ⓘ</span>
          </button>
        </span>
      </span>
      {open && (
        <span className="question-tooltip" id={tooltipId} role="tooltip">
          {text}
        </span>
      )}
    </span>
  );
}
