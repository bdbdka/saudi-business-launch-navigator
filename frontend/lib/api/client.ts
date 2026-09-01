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
const SERVICE_RECOVERY_LIMIT_MS = 70_000;
const READY_PROBE_TIMEOUT_MS = 6_000;
const READY_PROBE_DELAYS_MS = [1_500, 2_500, 4_000, 5_000] as const;

type ServiceWarmingListener = (warming: boolean) => void;

const warmingListeners = new Set<ServiceWarmingListener>();
let serviceWarming = false;
let recoveryPromise: Promise<boolean> | null = null;
let warmPromise: Promise<void> | null = null;

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

async function executeRequest<T>(
  path: string,
  init: RequestInit | undefined,
  timeoutMs: number,
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  const headers = new Headers(init?.headers);
  if (init?.body !== undefined && init.body !== null && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      cache: "no-store",
      credentials: "omit",
      signal: controller.signal,
      headers,
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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const deadline = Date.now() + SERVICE_RECOVERY_LIMIT_MS;
  try {
    return await executeRequest<T>(path, init, REQUEST_TIMEOUT_MS);
  } catch (error) {
    if (!isTransientAvailabilityError(error)) throw error;
    const ready = await recoverService(deadline);
    const remainingMs = deadline - Date.now();
    if (!ready || remainingMs <= 0) throw error;
    return executeRequest<T>(path, init, Math.min(REQUEST_TIMEOUT_MS, remainingMs));
  }
}

async function warmService(): Promise<void> {
  if (warmPromise) return warmPromise;
  const deadline = Date.now() + SERVICE_RECOVERY_LIMIT_MS;
  warmPromise = (async () => {
    if (await probeReadiness(Math.min(REQUEST_TIMEOUT_MS, SERVICE_RECOVERY_LIMIT_MS))) return;
    if (!(await recoverService(deadline))) {
      throw new NavigatorAPIError(
        "BACKEND_UNAVAILABLE",
        "The Navigator service did not become ready in time.",
        null,
        null,
      );
    }
  })().finally(() => {
    warmPromise = null;
  });
  return warmPromise;
}

async function recoverService(deadline: number): Promise<boolean> {
  if (recoveryPromise) return recoveryPromise;
  setServiceWarming(true);
  recoveryPromise = pollUntilReady(deadline).finally(() => {
    recoveryPromise = null;
    setServiceWarming(false);
  });
  return recoveryPromise;
}

async function pollUntilReady(deadline: number): Promise<boolean> {
  let attempt = 0;
  while (Date.now() < deadline) {
    const delay = READY_PROBE_DELAYS_MS[Math.min(attempt, READY_PROBE_DELAYS_MS.length - 1)];
    const delayMs = Math.min(delay, Math.max(0, deadline - Date.now()));
    if (delayMs > 0) await sleep(delayMs);
    const remainingMs = deadline - Date.now();
    if (remainingMs <= 0) return false;
    if (await probeReadiness(Math.min(READY_PROBE_TIMEOUT_MS, remainingMs))) return true;
    attempt += 1;
  }
  return false;
}

async function probeReadiness(timeoutMs: number): Promise<boolean> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_BASE_URL}/health/ready`, {
      cache: "no-store",
      credentials: "omit",
      signal: controller.signal,
    });
    return response.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timeout);
  }
}

function isTransientAvailabilityError(error: unknown): boolean {
  if (!(error instanceof NavigatorAPIError)) return false;
  if (error.code.startsWith("AI_")) return false;
  return error.code === "TIMEOUT"
    || error.code === "BACKEND_UNAVAILABLE"
    || error.status === 502
    || error.status === 503
    || error.status === 504;
}

function setServiceWarming(warming: boolean): void {
  if (serviceWarming === warming) return;
  serviceWarming = warming;
  for (const listener of warmingListeners) listener(warming);
}

function sleep(delayMs: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, delayMs));
}

export function subscribeServiceWarming(listener: ServiceWarmingListener): () => void {
  warmingListeners.add(listener);
  listener(serviceWarming);
  return () => warmingListeners.delete(listener);
}

export const navigatorAPI = {
  warm(): Promise<void> {
    return warmService();
  },
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
