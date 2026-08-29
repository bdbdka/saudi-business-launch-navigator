import { Header } from "@/components/header";
import { Footer } from "@/components/landing";
import type { Dictionary, Locale } from "@/lib/i18n";

export function AboutPage({ locale, copy }: { locale: Locale; copy: Dictionary }) {
  return (
    <>
      <a className="skip-link" href="#main-content">
        {locale === "ar" ? "تجاوز إلى المحتوى الرئيسي" : "Skip to main content"}
      </a>
      <Header locale={locale} copy={copy} page="about" />
      <main className="about-page" id="main-content" tabIndex={-1}>
        <div className="section-shell about-shell">
          <header className="about-hero">
            <h1>{copy.about.pageTitle}</h1>
            <p>{copy.about.pageIntro}</p>
          </header>

          <AboutSection title={copy.about.whatTitle}>
            <p>{copy.about.whatBodyOne}</p>
            <p>{copy.about.whatBodyTwo}</p>
          </AboutSection>

          <AboutSection title={copy.about.howTitle}>
            <ol className="about-steps">
              {copy.about.howSteps.map((step) => <li key={step}>{step}</li>)}
            </ol>
            <p>{copy.about.howIntro}</p>
          </AboutSection>

          <AboutSection title={copy.about.sourcesTitle}>
            <p>{copy.about.sourcesBody}</p>
            <p className="about-principle">{copy.about.sourcesPrinciple}</p>
          </AboutSection>

          <AboutSection title={copy.about.limitsTitle}>
            <p>{copy.about.limitsBody}</p>
            <ul>{copy.about.limitsItems.map((item) => <li key={item}>{item}</li>)}</ul>
          </AboutSection>

          <AboutSection title={copy.about.affiliationTitle}>
            <p>{copy.about.affiliationBody}</p>
          </AboutSection>

          <AboutSection title={copy.about.supportedTitle}>
            <p>{copy.about.supportedBody}</p>
            <ul>{copy.about.supportedActivities.map((activity) => <li key={activity}>{activity}</li>)}</ul>
          </AboutSection>

          <AboutSection id="methodology" title={copy.about.methodologyTitle}>
            <ul>{copy.about.methodologyItems.map((item) => <li key={item}>{item}</li>)}</ul>
          </AboutSection>

          <AboutSection id="privacy" title={copy.about.privacyTitle}>
            <p>{copy.about.privacyIntro}</p>
            <ul>{copy.about.privacyItems.map((item) => <li key={item}>{item}</li>)}</ul>
            <p className="privacy-caution">{copy.about.privacyCaution}</p>
          </AboutSection>

          <a className="button primary about-return" href={`/${locale}`}>{copy.about.backToGuide}</a>
        </div>
      </main>
      <Footer copy={copy} locale={locale} />
    </>
  );
}

function AboutSection({
  children,
  id,
  title,
}: {
  children: React.ReactNode;
  id?: string;
  title: string;
}) {
  return (
    <section className="about-section" id={id}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}
