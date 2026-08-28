import type { ActivityCode } from "@/lib/api/types";

type IconProps = { className?: string; size?: number };

const common = {
  fill: "none",
  stroke: "currentColor",
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  strokeWidth: 1.8,
};

export function CompassIcon({ className, size = 24 }: IconProps) {
  return (
    <svg aria-hidden="true" className={className} height={size} viewBox="0 0 24 24" width={size} {...common}>
      <circle cx="12" cy="12" r="9" />
      <path d="m15.5 8.5-2.2 4.8-4.8 2.2 2.2-4.8 4.8-2.2Z" />
    </svg>
  );
}

export function CheckIcon({ className, size = 20 }: IconProps) {
  return (
    <svg aria-hidden="true" className={className} height={size} viewBox="0 0 24 24" width={size} {...common}>
      <path d="m5 12.5 4.2 4.2L19 7" />
    </svg>
  );
}

export function MinusIcon({ className, size = 20 }: IconProps) {
  return (
    <svg aria-hidden="true" className={className} height={size} viewBox="0 0 24 24" width={size} {...common}>
      <path d="M5 12h14" />
    </svg>
  );
}

export function ArrowIcon({ className, size = 18 }: IconProps) {
  return (
    <svg aria-hidden="true" className={className} height={size} viewBox="0 0 24 24" width={size} {...common}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

export function ExternalLinkIcon({ className, size = 17 }: IconProps) {
  return (
    <svg aria-hidden="true" className={className} height={size} viewBox="0 0 24 24" width={size} {...common}>
      <path d="M14 5h5v5M10 14 19 5M19 14v5H5V5h5" />
    </svg>
  );
}

export function ShieldIcon({ className, size = 24 }: IconProps) {
  return (
    <svg aria-hidden="true" className={className} height={size} viewBox="0 0 24 24" width={size} {...common}>
      <path d="M12 3 5.5 5.5v5.8c0 4.4 2.7 7.7 6.5 9.7 3.8-2 6.5-5.3 6.5-9.7V5.5L12 3Z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

export function DocumentIcon({ className, size = 24 }: IconProps) {
  return (
    <svg aria-hidden="true" className={className} height={size} viewBox="0 0 24 24" width={size} {...common}>
      <path d="M7 3h7l4 4v14H7zM14 3v5h4M10 12h5M10 16h5" />
    </svg>
  );
}

export function QuestionIcon({ className, size = 24 }: IconProps) {
  return (
    <svg aria-hidden="true" className={className} height={size} viewBox="0 0 24 24" width={size} {...common}>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.8 9.5a2.4 2.4 0 1 1 3.3 2.2c-.9.4-1.1 1-1.1 1.8M12 17h.01" />
    </svg>
  );
}

export function ActivityIcon({ activity, className, size = 32 }: IconProps & { activity: ActivityCode }) {
  if (activity === "coffee_shop") {
    return (
      <svg aria-hidden="true" className={className} height={size} viewBox="0 0 32 32" width={size} {...common}>
        <path d="M6 11h17v7a8 8 0 0 1-8 8h-1a8 8 0 0 1-8-8v-7Z" />
        <path d="M23 14h2a3 3 0 0 1 0 6h-2M10 7c0-2 2-2 2-4M16 7c0-2 2-2 2-4" />
      </svg>
    );
  }
  if (activity === "restaurant") {
    return (
      <svg aria-hidden="true" className={className} height={size} viewBox="0 0 32 32" width={size} {...common}>
        <path d="M9 4v9M6 4v5a3 3 0 0 0 6 0V4M9 13v15M23 4c-3 2-4 6-4 10h4v14M23 4v10" />
      </svg>
    );
  }
  return (
    <svg aria-hidden="true" className={className} height={size} viewBox="0 0 32 32" width={size} {...common}>
      <path d="M5 14h22v13H5zM9 14a7 7 0 0 1 14 0M16 7V4M11 8 9 5M21 8l2-3M9 20h5M18 20h5" />
    </svg>
  );
}
