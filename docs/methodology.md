# Regulatory modeling methodology

The Navigator is designed to explain how a requirement was selected, not merely
to display a long generic checklist. Its methodology separates regulatory
identity, changing meaning, evidence, business facts, and applicability so that
each part can be reviewed and tested independently.

The public portfolio edition demonstrates this method with fictional records.
It is not a source of Saudi regulatory guidance.

## Canonical requirements and versions

A requirement has one stable canonical identity. It is not copied for every
activity or city. Activities are linked through a many-to-many relationship, so
one requirement can apply to coffee shops, restaurants, cloud kitchens, or a
combination of them.

Details that may change over time belong to a requirement version, including
its description, scope, responsible authority, effective period, and current or
historical state. When the meaning changes materially, a new version supersedes
the earlier one instead of overwriting it. This preserves the basis of older
checklist results.

## Sources and evidence

A stable source identity is separate from the version of the source that was
reviewed. This allows a page or document to change while preserving the exact
evidence context used for a requirement version.

Requirement versions link to source versions through explicit evidence
relationships. A relationship can describe primary, supporting, clarifying,
conflicting, superseding, or historical evidence. Arabic official content is
treated as canonical when real evidence is used; translations and simplified
explanations remain separate.

The governing principle is simple: no approved official source means no active
requirement. Pending, stale, or conflicting evidence must remain visible and
must not be silently promoted into a verified checklist item.

## Minimum decision-changing questions

Question count is not a measure of completeness. The questionnaire asks only
for facts that can change or resolve the result of a verified conditional
requirement.

- An unconditional requirement creates no question.
- A conditional requirement references a governed fact.
- A question is shown only when its fact is reachable and relevant.
- Dependent questions can be skipped when an earlier answer makes them
  unnecessary.
- Unsupported, descriptive, or duplicate questions are not added simply to
  make the questionnaire longer.

This approach reduces effort for the user while keeping every question tied to
a concrete decision in the rules engine.

## Unknown is not false

Yes, No, and I don't know are stored as `true`, `false`, and `null`. They are
different statements:

- `true` confirms the fact;
- `false` rejects the fact; and
- `null` means the user has not supplied enough information.

Treating unknown as false could incorrectly remove a requirement. Instead, an
unknown fact propagates through the condition and produces a
`NEEDS_INFORMATION` result when the missing answer matters. The checklist then
explains what needs clarification and links back to the corresponding question.

## Deterministic applicability

Applicability is decided by structured, versioned conditions evaluated in
Python. PostgreSQL separately enforces catalog eligibility and critical
integrity constraints. A language model never decides applicability.

For each activity and set of answers, the service:

1. loads current eligible requirement versions for the activity;
2. evaluates their structured conditions with three-valued logic;
3. assigns an explicit outcome;
4. records the reason and the condition version used; and
5. returns evidence, authority, freshness, and coverage metadata.

Duplicate requirement identities are removed before results are returned. A
result therefore represents one canonical obligation with a traceable reason,
not repeated city or activity copies.

## City and activity scope

The current product supports coffee shops, restaurants, and cloud kitchens.
Its stated pilot context is Riyadh and Jeddah, but the public demonstration
does not collect or evaluate city and implements no city-specific logic. A
future city-specific rule would require direct official evidence and additional
reviewed modeling before it could affect a checklist.

Site-dependent applicability is represented through questionnaire facts and
conditions rather than separate copies of a requirement.

## Synthetic public data

All portfolio-demo authorities, sources, evidence excerpts, requirements, and
checklist guidance are fictional. Some bounded navigation questions name real
regulatory categories or authorities, such as VAT and ZATCA, but they do not
state thresholds, decide applicability, or supply official evidence. They ask
the user to record a status confirmed through the relevant official route.

Synthetic source URLs use reserved `.invalid` domains. The demo is useful for
evaluating architecture, accessibility, deterministic behavior, and error
handling, but it must not be used to make a real licensing or compliance
decision.

## Limitations

- The demo catalog is intentionally small and does not claim regulatory
  completeness.
- The application is an informational navigation tool, not a government
  service, legal adviser, or submission portal.
- It does not guarantee compliance, approval, cost, processing time, or licence
  issuance.
- Market demand, competition, rent, and commercial attractiveness are outside
  the regulatory model.
- City-specific regulatory differences are not evaluated in the current
  demonstration.
- Optional AI output remains explanatory and cannot override structured facts,
  evidence status, or deterministic results.
