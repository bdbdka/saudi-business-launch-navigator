import type {
  ActivitiesResponse,
  ActivityCode,
  APIErrorEnvelope,
  ChecklistResponse,
  Locale,
  NavigationAnswers,
  NavigatorResponse,
  QuestionnaireAnswers,
  QuestionnaireResponse,
} from "./types";

export function resolveAPIBaseURL(
  configured = process.env.NEXT_PUBLIC_API_BASE_URL,
  environment = process.env.NODE_ENV,
): string {
  const value = configured?.trim();
  if (!value) {
    if (environment === "production") {
      throw new Error(
        "NEXT_PUBLIC_API_BASE_URL is required for a production frontend build.",
      );
    }
    return "http://127.0.0.1:8000";
  }
  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    throw new Error("NEXT_PUBLIC_API_BASE_URL must be an absolute HTTP(S) URL.");
  }
  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL must be an absolute HTTP(S) URL.");
  }
  if (
    parsed.username ||
    parsed.password ||
    parsed.pathname !== "/" ||
    parsed.search ||
    parsed.hash
  ) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL must be an origin without credentials or a path.");
  }
  if (
    environment === "production" &&
    parsed.protocol !== "https:" &&
    !isLoopbackHostname(parsed.hostname)
  ) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL must use HTTPS outside loopback rehearsal.");
  }
  return parsed.origin;
}

function isLoopbackHostname(hostname: string): boolean {
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "[::1]";
}

const API_BASE_URL = resolveAPIBaseURL();
const REQUEST_TIMEOUT_MS = 10_000;

export class NavigatorAPIError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly status: number | null,
    readonly requestId: string | null,
  ) {
    super(message);
    this.name = "NavigatorAPIError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      cache: "no-store",
      credentials: "omit",
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
    const requestId = response.headers.get("X-Request-ID");
    if (!response.ok) {
      let body: APIErrorEnvelope | null = null;
      try {
        body = (await response.json()) as APIErrorEnvelope;
      } catch {
        // The controlled fallback below intentionally ignores an invalid error body.
      }
      throw new NavigatorAPIError(
        body?.error.code ?? "SERVICE_ERROR",
        body?.error.message ?? "The Navigator service could not complete the request.",
        response.status,
        body?.error.request_id ?? requestId,
      );
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof NavigatorAPIError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new NavigatorAPIError("TIMEOUT", "The Navigator request timed out.", null, null);
    }
    throw new NavigatorAPIError("BACKEND_UNAVAILABLE", "The Navigator backend is unavailable.", null, null);
  } finally {
    clearTimeout(timeout);
  }
}

export const navigatorAPI = {
  activities(): Promise<ActivitiesResponse> {
    return request("/api/v1/activities");
  },
  questionnaire(activityCode: ActivityCode): Promise<QuestionnaireResponse> {
    return request("/api/v1/questionnaire", {
      method: "POST",
      body: JSON.stringify({ activity_code: activityCode }),
    });
  },
  checklist(activityCode: ActivityCode, answers: QuestionnaireAnswers): Promise<ChecklistResponse> {
    const facts: Record<string, boolean | null> = {};
    const navigationFacts: NavigationAnswers = {};
    for (const [code, value] of Object.entries(answers)) {
      if (code === "ownership_investor_route") {
        navigationFacts.ownership_investor_route = value as NavigationAnswers["ownership_investor_route"];
      } else if (code === "planned_legal_form") {
        navigationFacts.planned_legal_form = value as NavigationAnswers["planned_legal_form"];
      } else if (code === "has_selected_business_premises") {
        navigationFacts.has_selected_business_premises = value as boolean | null;
      } else {
        facts[code] = value as boolean | null;
      }
    }
    return request("/api/v1/checklist", {
      method: "POST",
      body: JSON.stringify({
        activity_code: activityCode,
        facts,
        navigation_facts: navigationFacts,
      }),
    });
  },
  navigate(text: string, language: Locale): Promise<NavigatorResponse> {
    return request("/api/v1/navigator", {
      method: "POST",
      body: JSON.stringify({ text, language }),
    });
  },
};

export { API_BASE_URL };
