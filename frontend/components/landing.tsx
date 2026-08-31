import {
  catalogPresentationPolicy,
  configuredCatalogMode,
} from "@/lib/catalog-presentation";
import type { Dictionary, Locale } from "@/lib/i18n";

export function Hero({ copy, locale }: { copy: Dictionary; locale: Locale }) {
  const policy = catalogPresentationPolicy(configuredCatalogMode(), locale);
  return (
    <section className="hero section-shell" id="home">
      <h1>{copy.heroTitle}</h1>
      <p className="hero-body">{copy.heroBody}</p>
      <div className="product-purpose">
        <h2>{copy.purpose.title}</h2>
        <p>{copy.purpose.body}</p>
      </div>
      <ol className="simple-stages" aria-label={copy.workflow.label}>
        <li>{copy.workflow.activity}</li>
        <li>{copy.workflow.questions}</li>
        <li>{policy.isPortfolioDemo ? policy.text.landingChecklist : copy.workflow.landingChecklist}</li>
      </ol>
      <p className="landing-coverage">
        {policy.isPortfolioDemo ? policy.text.landingCoverage : copy.landingCoverage}
      </p>
      <p className="landing-disclaimer">
        {policy.isPortfolioDemo ? policy.text.homepageNotice : copy.landingDisclaimer}
      </p>
      <aside className="before-start" aria-labelledby="before-start-title">
        <h2 id="before-start-title">{copy.beforeStart.title}</h2>
        <p>{copy.beforeStart.body}</p>
        <ul>
          {copy.beforeStart.items.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </aside>
    </section>
  );
}

export function Footer({
  copy,
  locale,
  quiet = false,
}: {
  copy: Dictionary;
  locale: Locale;
  quiet?: boolean;
}) {
  const policy = catalogPresentationPolicy(configuredCatalogMode(), locale);
  return (
    <footer className={`site-footer${quiet ? " workflow-footer" : ""}`} id="coverage-info">
      <div className="section-shell footer-inner">
        <div className="footer-brand">
          <strong>{copy.productNameShort}</strong>
          <p>{policy.isPortfolioDemo ? policy.text.footerNotice : copy.footer.disclaimer}</p>
        </div>
        <nav className="footer-nav" aria-label={copy.footer.details}>
          <a href={`/${locale}`}>{copy.footer.home}</a>
          <a href={`/${locale}/about`}>{copy.footer.about}</a>
          <a href={`/${locale}/about#privacy`}>{copy.footer.privacy}</a>
        </nav>
      </div>
    </footer>
  );
}
