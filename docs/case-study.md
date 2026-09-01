# Technical case study

## The challenge

Business-launch guidance is not a simple content-search problem. Information
can span several official services, change over time, and apply differently
according to structured facts about the planned business. A fluent answer can
still be unsupported, stale, or based on an unanswered question.

The product therefore needed to do two things at once:

1. give a beginner a short, understandable Arabic-first experience; and
2. keep source evidence, applicability, uncertainty, and AI responsibility
   inside explicit technical boundaries.

## Product approach

The Navigator uses a guided sequence:

```text
activity selection
  -> minimum relevant questions
  -> validated business facts
  -> deterministic condition evaluation
  -> explained launch guidance
```

The current research scope covers coffee shops, restaurants, and cloud
kitchens in Riyadh and Jeddah. Other Saudi cities have not yet been fully
reviewed. The product neither assumes that city rules differ nor claims that
nationwide equivalence has been verified.

## Key engineering decisions

### Keep regulatory authority outside the language model

Python and SQL decide applicability. OpenAI is optional and limited to
structured text interpretation, clarification, or explanation of a result that
has already been computed. Pydantic validates model output, and the guided
questionnaire remains fully usable without an API key.

### Preserve unknown as a real state

Conditions use true, false, and unknown. When a missing answer matters, the
result becomes `NEEDS_INFORMATION` and links the user back to the exact
question. Unknown is never silently converted to no.

### Separate stable identities from versions

Requirements and sources have stable identities, while changing legal meaning
or reviewed evidence belongs to versions. Many-to-many relationships connect
requirement versions to activities and source versions. This preserves history
and avoids duplicating one requirement for each activity or city.

### Fail closed at the publication and runtime boundaries

Unapproved, stale, conflicting, or ineligible evidence cannot support an active
published requirement. The public deployment also verifies its catalog mode,
database name and identity, migration, schema, dataset fingerprint, graph, and
read-only runtime role before serving traffic.

### Isolate the public demonstration

The portfolio release uses a dedicated synthetic catalog. It exercises the
same web, API, database, rules, and deployment shape without publishing the
governed research catalog or presenting fictional checklist records as Saudi
regulation. The results show one separate, allowlisted Balady activity page for
the selected activity.

## Implementation

- Next.js and TypeScript provide Arabic RTL and English LTR routes, responsive
  questionnaire interaction, plain-language help, missing-information re-entry,
  progress tracking, and safe source presentation.
- FastAPI and Pydantic expose typed activity, questionnaire, checklist, optional
  interpretation, and health endpoints.
- SQLAlchemy and PostgreSQL implement the versioned catalog and restrictive
  relationships; Alembic manages schema evolution.
- Docker and Render run separate web and API services with managed PostgreSQL,
  explicit CORS and trusted hosts, environment-managed secrets, health checks,
  and no public database listener.

## Validation

The final release validation on 2026-09-01 included:

- 64 backend tests against disposable PostgreSQL 18;
- 89 frontend tests, with 3 environment-gated tests skipped;
- 5 real-browser Playwright scenarios against the full local stack;
- external Chrome checks against the deployed Arabic, English, About, mobile,
  questionnaire, result, link, and AI-unavailable paths;
- Ruff, formatting, mypy, ESLint, TypeScript, and production builds;
- dependency audits with no known vulnerabilities; and
- manual review of all portfolio screenshots.

Negative tests cover catalog identity mismatch, altered structure, governed
data contamination, elevated database privileges, request-size limits, unsafe
configuration, synthetic source suppression, and invalid external links.

## Result

The deployed product provides:

- Arabic-first and English experiences;
- 7-, 8-, and 7-question paths for the three supported activities;
- deterministic `APPLIES`, `DOES_NOT_APPLY`, and `NEEDS_INFORMATION` outcomes;
- distinct beginner-oriented review topics;
- one correct Balady activity reference per selected activity; and
- an inspectable public architecture with a strict synthetic-data boundary.

The result is a portfolio demonstration, not evidence of regulatory
completeness, compliance, licensing approval, or government affiliation.

## What comes next

Future expansion should continue in small official-source-backed batches. Good
candidates include additional activities, additional cities after verified
research, source-change monitoring, clearer launch stages, and privacy-aware
saved journeys. City or site logic should be introduced only when official
evidence supports it.
