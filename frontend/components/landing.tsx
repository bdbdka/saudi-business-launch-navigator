import type { Dictionary, Locale } from "@/lib/i18n";

export function Hero({ copy }: { copy: Dictionary }) {
  return (
    <section className="hero section-shell" id="home">
      <h1>{copy.heroTitle}</h1>
      <p className="hero-body">{copy.heroBody}</p>
      <ol className="simple-stages" aria-label={copy.workflow.label}>
        <li>{copy.workflow.activity}</li>
        <li>{copy.workflow.questions}</li>
        <li>{copy.workflow.landingChecklist}</li>
      </ol>
      <p className="landing-coverage">{copy.landingCoverage}</p>
      <p className="landing-disclaimer">{copy.landingDisclaimer}</p>
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
  return (
    <footer className={`site-footer${quiet ? " workflow-footer" : ""}`} id="coverage-info">
      <div className="section-shell footer-inner">
        <div className="footer-brand">
          <strong>{copy.productNameShort}</strong>
          <p>{copy.footer.disclaimer}</p>
        </div>
        <nav className="footer-nav" aria-label={copy.footer.details}>
          <a href={`/${locale}`}>{copy.footer.home}</a>
          <a href={`/${locale}/about`}>{copy.footer.about}</a>
          <a href={`/${locale}/about#methodology`}>{copy.footer.methodology}</a>
          <a href={`/${locale}/about#privacy`}>{copy.footer.privacy}</a>
        </nav>
      </div>
    </footer>
  );
}
