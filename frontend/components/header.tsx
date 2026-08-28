"use client";

import type { Dictionary, Locale } from "@/lib/i18n";

export function Header({
  locale,
  copy,
  onLocaleChange,
  page = "home",
}: {
  locale: Locale;
  copy: Dictionary;
  onLocaleChange?: (locale: Locale) => void;
  page?: "home" | "about";
}) {
  const nextLocale = locale === "ar" ? "en" : "ar";
  const alternateHref = `/${nextLocale}${page === "about" ? "/about" : ""}`;

  return (
    <header className="site-header">
      <div className="header-shell">
        <a className="brand" href={`/${locale}`} aria-label={copy.productName}>
          {copy.productNameShort}
        </a>
        <nav className="header-nav" aria-label={copy.navLabel}>
          <a href={`/${locale}`} aria-current={page === "home" ? "page" : undefined}>
            {copy.nav.home}
          </a>
          <a href={`/${locale}/about`} aria-current={page === "about" ? "page" : undefined}>
            {copy.nav.about}
          </a>
          {onLocaleChange ? (
            <button
              className="language-switch"
              type="button"
              onClick={() => onLocaleChange(nextLocale)}
              aria-label={copy.languageSwitchLabel}
            >
              {copy.languageLabel}
            </button>
          ) : (
            <a className="language-switch" href={alternateHref} aria-label={copy.languageSwitchLabel}>
              {copy.languageLabel}
            </a>
          )}
        </nav>
      </div>
    </header>
  );
}
