# JVSG Non-CM Triage Implementation Plan

## 1. Authority, scope, and document use

This plan decomposes the
[enterprise technical specification](./executive_summary_enterprise_technical_specification_jvsg_non_cm_triage_azure_architecture.md)
into deliverable-based implementation sprints. The specification remains the
requirements authority; this plan does not silently resolve its contradictions
or expand the product scope.

- Use the [sprint TODO](./sprint_todo.md) for executable tasks, dependencies, and
  completion evidence. Task IDs are stable across both documents.
- Keep planning documents in `docs/`. Update this plan and the sprint TODO together
  when an approved requirement changes.
- Preserve the source specification. Record approved clarifications here before
  implementing affected behavior.
- Sprint numbers indicate dependency order, not fixed dates, staffing estimates,
  or commitments. Independent tasks may run concurrently once prerequisites pass.
- This deliverable is planning only: it does not authorize deployment, live-data
  processing, outbound messages, or automatic case/referral decisions.

## 2. Verified starting point

As inspected on November 6, 2026:

| Surface | Present | Remaining |
|---|---|---|
| Developer foundation | Python 3.11+ package, dev container, optional integration dependency groups | Add dependencies only with their implementing modules; verify authorized edge connectivity separately |
| Configuration | Environment-backed settings in [settings.py](../src/jvsg_triage/settings.py), secret-typed HMAC setting | Runtime validation, approved routing, production identity and secret retrieval |
| Quality controls | Pytest settings tests; Ruff, strict mypy, and CI | Domain, integration-contract, property, benchmark, and release evidence |
| Domain packages | ETL, SLM, TOON, M365, and VOMA directories | Actual processing and integration implementations |
| Deployment | Reserved Azure Functions directory | Functions host, packaging, infrastructure, deployment, and operational verification |

The specification calls Phase 1 operational validation completed/current. That
claim is not evidence that the repository implements Phase 1. Existing workbook,
audit, and operational artifacts require separate authorized verification; do
not copy live artifacts into the repository.

## 3. Non-negotiable implementation invariants

1. **Synthetic-only development:** no real veteran identifiers, case notes, or
   GeoSol exports in source control, tests, logs, prompts, or generated development
   artifacts. Production data handling requires explicit agency approval.
2. **Privacy before inference:** scrub identifiers before any model boundary;
   replace raw SID with HMAC-SHA256 using an approved secret. A pseudonymous token
   is still access-controlled data, not proof of anonymity.
3. **Human authority:** every model-generated filter starts as `AI_Draft`.
   Qualified specialists approve case interpretation and referrals. No model or
   deterministic feasibility score is an authoritative referral decision.
4. **Deterministic core:** typed Python, vectorized Polars joins and aging,
   explicit execution dates, strict schemas, and reproducible synthetic inputs.
5. **Optional integrations:** no network calls on import or in ordinary tests.
   Live integration checks are separate, authorized, and opt-in.
6. **Preserved state:** refreshes must not overwrite specialist notes, verified
   contacts, partner tags, manual overrides, or review decisions.
7. **Explicit failure:** malformed inputs, unavailable integrations, rejected
   inference, and failed delivery produce visible, sanitized errors. A fallback
   must be labeled and reviewable, never disguised as successful model output.
8. **Least privilege:** managed identity, approved secret stores, private
   production endpoints, and office/role isolation precede rollout.
9. **Zero double entry:** derive roster identity and assessment data from approved
   exports; ask staff only for operational actions and review, not retyping.

## 4. Decisions that block implementation

All decisions below are **open**. The domain owner supplies operational rules;
the agency platform/security owner approves environment and data boundaries;
the VOMA owner approves the federal contract. Record the decision, approver,
date, and affected tests before closing the corresponding task.

| ID / task | Source conflict or missing rule | Required resolution | Blocks |
|---|---|---|---|
| D01 / S0-02 | Sections 3.3/4.1 request 500 records; Prompt 1 requests 138 assessment rows and 92 IEP rows, including noise | Define a 138-unique-assessment baseline with 90 overlaps, 48 triage, and 2 carryovers; approve where extra noise/duplicates live and a separate 500-record scale fixture. Confirm 40/48 Q4, 34/48 virtual, 8/48 legal rounding | S1, S2 acceptance |
| D02 / S0-02 | Fiscal window end, active/open IEP evidence, composite office/role filtering, and duplicate handling are underspecified | Approve extract columns, fiscal boundaries, active-status rules, SID deduplication, multi-office assignment, verified-touch provenance, and null/future-date rejection policy | S1, S2 |
| D03 / S0-03 | TOON grammar requires numeric SID although privacy requires HMAC; `ST`/`DOM` cannot reconstruct per-domain states or the human filter | Approve a versioned privacy-safe grammar and exact round-trip scope. Define lossless fields/extension if full profile equality remains required; no invented numeric encoding or silent data loss | S3, S4, S7 |
| D04 / S0-03 | TOON EBNF includes `MIN_SHIFT`; schema omits it; transit-distance and legal-tier thresholds are absent | Approve schema/grammar alignment and required feasibility inputs, units, missing/unknown policy, inclusive boundaries, and overnight-shift handling. Do not invent transit limits or infer protected facts | S3, S4, S7 |
| D05 / S0-03 | Executive target is 55% compression; tests require >=50%; examples are not measured results | Retain >=50% as the test gate and 55% as the stated optimization target, subject to owner approval; define equivalent JSON baseline, profile corpus, tokenizer, and identity inclusion | S4-03 |
| D06 / S0-04 | `07:30 CST`, weekday prose, and raw timer cron do not establish DST behavior | Choose fixed UTC-6 or America/Chicago civil time, weekday/holiday policy, hosting support, retry windows, and transition windows; test winter and summer UTC instants | S5, S8 |
| D07 / S0-04 | Section 2.6 requests newly yellow and last-24-hour mitigated handoffs; Prompt 5 requests broader ready queues | Approve initial-run/backlog behavior, yellow transition detection, LVER readiness/review gate, exited-case routing, and repeat-delivery rules | S5, S6 |
| D08 / S0-04 | Azure Government vs Commercial, SQL/SharePoint/Dataverse alternatives, private inference, and workbook identity handling are not selected | Approve tenant/cloud, pilot and production stores, authorized identity mapping, retention, private inference service, Entra roles, Graph permissions, and Teams action mechanism | S6, S8, S9 |
| D09 / S0-04 | Fallback parser and automatic continuation may conceal uncertain inference | Approve fallback labeling, evidence requirements, abstention/error behavior, and who can approve drafts; define readiness vs IEP-conversion review separately | S3, S5 |
| D10 / S0-04 | Roadmap says Phase 2 Q1-Q2 FY27 and includes April 2027, without defining fiscal calendar | Confirm fiscal/calendar milestones, April Stand Down dependencies, rollout owners, and entry/exit approvals without inventing dates | S9 pilot, S10 |
| D11 / S0-03 | `<15 ms`, `<120 ms`, `<85 MB`, and `<45 seconds` lack workload and measurement scope | Approve benchmark hardware, warm/cold state, timing boundaries, dataset, memory measure, latency statistic, caching workload, and whether transport is included | S2-04, S3-05, S7-04, S9-04 |

A blocked decision does not prevent independent work. Do not mark the dependent
task done using guessed defaults or weaken the specification to make tests pass.

## 5. Target data flow and implementation boundaries

| Stage | Implementation surface | Output and boundary |
|---|---|---|
| Extract validation | Synthetic generator, extract schemas, ETL loaders | Validated 203/205 tables, explicit rejected-input diagnostics, office/role provenance |
| Cohort isolation | `etl/anti_join_engine.py` | Unique current-window DVOP assessment SIDs minus active/open DVOP IEP SIDs; separate prior-year carryover audit |
| Aging | `etl/velocity_aging.py` | Latest assessment or verified touch; GREEN 0-14, YELLOW 15-29, RED 30-89, EXITED_90D >=90 |
| Privacy | `etl/pii_scrubber.py` | Sanitized note and HMAC identifier; raw identity stays inside approved operational boundary |
| Classification | `slm/barrier_schema.py`, `slm_classifier.py`, `kappa_evaluator.py` | Validated 4x4 profile, evidence, draft/review metadata, labeled fallback and cached results |
| Compact protocol | `toon/serializer.py`, `validator.py` | Approved versioned TOON, human filter <=60 characters, measured compression |
| Operational state | `m365/excel_watchlist.py`, `graph_sync.py`, approved backing store | Four-tab workbook, persisted review/actions/transitions, protected refresh merge |
| Role digests | `m365/daily_digest.py` | Office-scoped HTML and Teams queues; approved draft/ready gating and verified write-back |
| Feasibility | `voma_skill/` | Shared deterministic evaluator used by FastAPI, FastMCP, and Functions; explanations for suppressed matches |
| Orchestration | `scripts/run_local_pipeline.py`, `azure_functions/function_app.py` | Synthetic dry run locally; authorized scheduled production processing and delivery |
| Oversight/intake | Power BI, approved ADOW web/Bookings surfaces | Scoped aggregates, reviewed front-end changes, and traceable intake-to-203 handoff |

Keep the existing package settings module as the configuration authority rather
than introducing a second settings implementation at the source blueprint's
`config/settings.py` location. Extend the existing CI workflow rather than
creating parallel competing quality gates. Preserve optional dependency groups.
Record any other necessary blueprint-path deviation before implementation.

### Domain and state contract

- Domains: TRN, HSG, MED, LEG. States: CRT, ACT, MIT, RES.
- Derive the worst state and referral-ready flag from validated domain states.
  Readiness requires the approved MIT/RES rule and human review; it is distinct
  from an ACT case becoming suitable for Code 205 assessment.
- Preserve operational constraints: shift end, transit mode, curfew, lifting
  limit, bonding requirement, and partner agency. Resolve D04 before adding
  distance/legal thresholds or minimum-shift semantics.
- Keep cohort membership, aging, barrier severity, disposition, and review
  status separate. A 90-day aging flag is not an automatic GeoSol closure.
- Cache by sanitized content and all approved interpretation dependencies
  (schema/model/prompt/rule versions); changing one invalidates stale output.
- The feasibility multiplier is the product of approved shift, transit,
  lifting, and legal indicators. Return `similarity * multiplier`; a suppressed
  score >=0.80 receives an exact-boundary explanation. Never invent alternative
  jobs: suggest compliant criteria or verified candidate alternatives.

## 6. Sprint sequence and release gates

The full executable breakdown, including per-task dependencies and acceptance
criteria, is in the [sprint TODO](./sprint_todo.md).

| Sprint | Objective / task range | Exit gate | Rollout alignment |
|---|---|---|---|
| 0 | Baseline and decisions, S0-01..S0-04 | Starting point recorded; required D01-D11 decisions approved or explicitly blocking downstream work | Phase 1 evidence reconciliation |
| 1 | Contracts and fixtures, S1-01..S1-04 | Reproducible baseline, noise/boundary fixtures, and separate scale dataset validated offline | Phase 1 / Phase 2 foundation |
| 2 | Cohort and aging, S2-01..S2-04 | Exact 48/2 results, clean office/role scope, all age boundaries, measured throughput | Phase 2 |
| 3 | Privacy and reviewed synthesis, S3-01..S3-06 | Scrub-before-inference, strict taxonomy, visible fallback, cache, >=0.85 kappa on 20 scenarios | Phase 2 |
| 4 | TOON and local pipeline, S4-01..S4-04 | Approved grammar, lossless agreed round-trip, >=50% measured tokens saved, synthetic dry run | Phase 2 |
| 5 | Workbook and digest rendering, S5-01..S5-05 | Four tabs, non-destructive refresh, review-aware role queues, validated HTML/cards | Phase 2 |
| 6 | M365 delivery and action loop, S6-01..S6-05 | Scoped sync, durable delivery state, authenticated/idempotent write-back, authorized synthetic smoke | Phase 2 |
| 7 | VOMA and runtime tools, S7-01..S7-05 | Four constraints, REST/MCP parity, performance evidence, private local tools | Phase 4 prerequisites |
| 8 | Azure hosting and release automation, S8-01..S8-05 | Correct schedule, shared route behavior, gated infrastructure/deploy, synthetic health and rollback proof | Phase 3 readiness |
| 9 | Regional/statewide readiness, S9-01..S9-05 | RLS, manager escalation, routing, performance and governance evidence, signed pilot rollout | Phase 2 exit / Phase 3 |
| 10 | Intake modernization and federal release, S10-01..S10-06 | Approved web/Bookings flows, Stand Down readiness, federal handshake and LVER integration signed off | Phase 2 outreach / Phase 4 |

Sprints 5 and 7 may proceed independently after Sprint 4 and their own decisions
are complete. Web content/QR preparation may proceed independently of Azure,
but intake-to-triage completion requires a working reviewed pipeline. Do not
delay the regional pilot solely for federal co-development.

## 7. Requirements traceability

| Source section | Requirement | Executable tasks |
|---|---|---|
| 1.1-1.3 | Visible triage cohort, zero double entry, synchronized queues, regional insight | S1-02, S2-01..S2-03, S5-01..S5-05, S9-01..S9-05 |
| 2.1 / 3.1-3.3 / 4.1-4.2 | Hybrid foundation, zero-admin development, optional edge connectivity, approved cloud promotion | S0-01, S1-04, S3-03, S8-01..S8-05 |
| 2.2 / Prompt 2 | Filtered anti-joins, carryovers, state-preserving refresh | S1-01..S1-03, S2-01..S2-02, S5-02 |
| 2.3 / Prompt 2 | Verified-contact aging and 90-day flag | S2-03, S5-03, S6-04, S9-02 |
| 2.4 / Prompt 3 | Regex + Presidio privacy, HMAC, strict 4x4 classification, fallback, kappa | S3-01..S3-06 |
| 2.5 / Prompt 4 / 5.1 | Grammar, exact approved round-trip, >=50% gate / 55% target | S0-03, S4-01..S4-03 |
| 2.6 / Prompt 5 | Four-tab watchlist, DVOP/LVER queues, Teams/email, write-back | S5-01..S5-05, S6-01..S6-05 |
| 2.7 / Prompt 6 | Four-indicator VOMA multiplier, explanations, FastAPI/OpenAPI 3.1 and MCP | S7-01..S7-03, S8-02 |
| Prompt 1 / 3.3 | Exact Mobile baseline, 500-record synthetic mode, environment settings | S0-02, S1-01..S1-04 |
| Prompt 7 / 4.1 | Functions timer/HTTP routes, quality gates, deployment | S8-01..S8-05 |
| 5.1-5.2 | Contributor safeguards, local watchlist/synthesis/digest MCP tools, <15 ms skill | S0-01, S7-04..S7-05 |
| 6.1 | Entra, Key Vault, private inference, managed identity, RLS | S0-04, S6-01, S8-03, S9-01 |
| 6.2 | 15,000+ rows <120 ms / <85 MB, change-only inference, <45 s run, quarterly kappa and AI_Draft | S2-04, S3-04..S3-06, S9-04 |
| 6.3 | Four-phase promotion, Region 7, all seven LWDBs, rulebook, Stand Down, federal handshake | S9-03, S9-05, S10-04..S10-06 |
| 6.4 | Homepage welcome video, interactive carousel, trackable Bookings QR intake | S10-01..S10-04 |

## 8. Validation, evidence, and definition of done

Each task closes only when its output is persistent, its stated acceptance
criteria pass, and the sprint TODO links synthetic-safe evidence. Implementation
tasks include focused tests and directly related documentation. No checkbox is
completed merely because a file exists or an external action is proposed.

| Gate | Required proof |
|---|---|
| Functional | Exact unique cohort/carryover counts, role/office exclusion, duplicate/null/boundary tests, preserved user state |
| Privacy/review | Synthetic identifier scrub tests; network spy proving only scrubbed input reaches inference; drafts cannot bypass review; sanitized errors |
| Protocol | Valid/invalid grammar tests, property-based agreed lossless round-trip, exact `cl100k_base` token and UTF-8 byte counts on equivalent payloads |
| Statistical | 20 documented synthetic benchmark scenarios; qualified independent labels; actual kappa >=0.85, with undefined/insufficient-label results surfaced |
| Integration | Mocked contracts for Graph, API, MCP, timer, and actions; separate authorized synthetic smoke tests; no import/test network calls |
| Performance | Actual measurements against D11: 15,000+ service rows <120 ms and <85 MB; VOMA <15 ms; cached daily classification path <45 s |
| Operational | Winter/summer schedule proof, repeated-run safety, scoped routing, failed/partial-delivery visibility, backup/rollback and recovery evidence |
| Release | Ruff, strict mypy, tests with coverage reporting, synthetic end-to-end run, agency approvals and human sign-off |

Use the existing project commands: `ruff check .`, `mypy src`, and `pytest`.
Add `pytest-cov`, tokenization, privacy, and statistical dependencies to the
appropriate groups only when the corresponding tasks implement their use.
CI must generate synthetic data and exercise implemented modules without
external services; coverage is reported, not an invented percentage gate.

If a quantitative target fails, preserve the measurements and keep the task
open. Optimize and rerun, or obtain an explicit requirements decision; do not
claim the source's example compression figures or performance claims as results.

### Phase promotion checklist

- **Phase 1 reconciliation:** verify approved operational evidence and synthetic
  baseline reproduction; no inference that existing code handles live exports.
- **Phase 2 regional pilot:** Bay Minette, Foley, and Mobile routing approved;
  review workflow, workbook preservation, authorized weekday digests, action
  loop, rulebook, and Stand Down readiness demonstrated.
- **Phase 3 statewide:** target Azure environment approved; identity/private
  network/RLS tested; seven-LWDB routing, manager escalations, dashboard,
  performance, quarterly review, and rollback signed off.
- **Phase 4 federal:** USDOL-approved protocol and authenticated handshake;
  privacy-safe constraints, parity/performance proof, reviewed compatible job
  results delivered to the LVER digest; qualified human authority retained.
