import type { Locale } from "@/lib/i18n";

export function RouteLoading({ locale }: { locale: Locale }) {
  return (
    <main className="centered-page">
      <div role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true" />
        <h1 className="sr-only">{locale === "ar" ? "تحميل الدليل" : "Loading the guide"}</h1>
        <p>{locale === "ar" ? "جارٍ تحميل الدليل…" : "Loading the guide…"}</p>
      </div>
    </main>
  );
}

export function RouteError({ locale, reset }: { locale: Locale; reset: () => void }) {
  const arabic = locale === "ar";
  return (
    <main className="centered-page">
      <div role="alert">
        <h1>{arabic ? "تعذر تحميل الصفحة" : "The page could not be loaded"}</h1>
        <p>{arabic ? "لم نعرض أي معلومات بديلة أو مفترضة." : "No substitute or assumed information has been shown."}</p>
      </div>
      <div className="route-actions">
        <button className="button primary" type="button" onClick={reset}>{arabic ? "حاول مرة أخرى" : "Try again"}</button>
        <a className="button secondary" href={`/${locale}`}>{arabic ? "العودة إلى الدليل" : "Back to the guide"}</a>
      </div>
    </main>
  );
}

export function NotFoundContent({ locale }: { locale: Locale }) {
  const arabic = locale === "ar";
  return (
    <main className="centered-page">
      <p className="stage-label">404</p>
      <h1>{arabic ? "الصفحة غير موجودة" : "Page not found"}</h1>
      <p>{arabic ? "تحقق من الرابط أو عد إلى بداية الدليل." : "Check the link or return to the start of the guide."}</p>
      <div className="route-actions">
        <a className="button primary" href={`/${locale}`}>{arabic ? "العودة إلى الدليل" : "Back to the guide"}</a>
        <a className="button secondary" href={`/${locale}/about`}>{arabic ? "حول الدليل" : "About this guide"}</a>
      </div>
    </main>
  );
}

export function localeFromPath(pathname: string | null): Locale {
  return pathname === "/en" || pathname?.startsWith("/en/") ? "en" : "ar";
}
