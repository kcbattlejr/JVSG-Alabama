# JVSG Implementation Sprint TODO

Execution companion to the [implementation plan](./implementation_plan.md) and
[source specification](./executive_summary_enterprise_technical_specification_jvsg_non_cm_triage_azure_architecture.md).

## How to execute

- All tasks start unchecked. Existing scaffold is context, not completed domain
  functionality. Verification tasks close only after their own criteria pass.
- `Depends` lists actual prerequisites; `none` means independently startable.
  Decisions D01-D11 are defined in the implementation plan.
- Each task names a concrete output and measurable completion criteria. Include
  focused tests and related documentation with each implementation.
- When closing a task, change `[ ]` to `[x]` and append an evidence link, actual
  result, reviewer/approval where needed, and date. Use synthetic-safe evidence
  only. External approvals may be referenced by an approved non-sensitive record,
  not copied into GitHub.
- If blocked, leave unchecked and record `Blocked: <decision/dependency>`.
  Do not replace missing approvals or unknown business rules with guessed values.
- A sprint exits when its tasks and the corresponding plan exit gate pass.
  Sprint order is not a fixed calendar; independent work may overlap.

## Sprint 0 - Baseline and requirement decisions

### Presentation slice progress (November 14, 2026)

The [SharePoint-first demo runbook](./management_demo_runbook.md) and
[recording script](./management_demo_script.md) describe the separate synthetic
presentation workflow implemented in `jvsg_triage.demo`: strict workbook intake,
vectorized aging, custom lossless TOON demo codec, verified Excel/HTML snapshots,
simulated baseline/refresh delivery and preserved source review values.
Focused evidence is in [test_management_demo.py](../tests/test_management_demo.py),
including exact aging thresholds, closed-schema rejection, TOON round trips,
repeatability, integrity tampering and last-success preservation.
This slice does not close the approval-dependent tasks below, the production
TOON contract, live SharePoint integration or real-world privacy validation.

Goal: establish an honest starting point and resolve implementation contracts.

- [ ] **S0-01 - Verify and record repository/operational baseline**
  - Depends: none.
  - Output: confirmed baseline in the implementation plan, including existing
    settings/CI/dev-container reuse and authorized Phase 1 evidence references.
  - Done when: scaffold vs implemented behavior is explicit; contributor privacy
    rules and optional integrations are retained; missing operational evidence is
    marked unverified rather than treated as code completion.
- [ ] **S0-02 - Approve synthetic and extract contracts**
  - Depends: none.
  - Output: approved D01/D02 decisions with domain-owner sign-off.
  - Done when: baseline vs 500-record/noise modes, unique counts, rounded subgroup
    counts, fiscal bounds, active IEP evidence, duplicates, office assignment,
    touch provenance, and invalid-date handling are specified with examples.
- [ ] **S0-03 - Approve protocol, feasibility, and benchmark contracts**
  - Depends: none.
  - Output: approved D03/D04/D05/D11 decisions.
  - Done when: HMAC identity grammar, lossless round-trip scope, all feasibility
    thresholds/unknown behavior, compression baseline, and reproducible
    performance measurement scopes have named approvers and testable rules.
- [ ] **S0-04 - Approve operational, review, and rollout rules**
  - Depends: none.
  - Output: approved D06/D07/D08/D09/D10 decisions.
  - Done when: timezone, queues, review/fallback policy, cloud/store/identity,
    Graph and Teams mechanism, live-data authorization boundary, rollout
    milestones, and operational approvers are explicit.

## Sprint 1 - Schemas, fixtures, and runtime validation

Goal: make all downstream work reproducible without live data.

- [ ] **S1-01 - Define validated GeoSol extract schemas**
  - Depends: S0-02.
  - Output: machine-readable schemas under `data/schemas/` and typed loading/
    validation code in the ETL package.
  - Done when: required columns, SID types, service codes, roles, office, dates,
    active/open IEP status, and touch provenance are checked; invalid/missing
    fields produce sanitized actionable errors; valid CSV inputs load offline.
  - Partial implementation (November 6, 2026):
    [native MIS intake](./mis_intake_contract.md) defines the observed anti-join
    CSV / case-notes XLSX header contract, title-row discovery, protected models
    and synthetic-tested note matching. Source files were inspected only
    through their headers. Separate 203/205 schemas, ambiguous date/code/role
    meanings and D02 business-rule approval remain open; this task is not done.
  - Contract v1.1 update (November 7, 2026): every column now carries a PII class and handling rule.
    The XLSX `Total Rows` footer is validated, and a seeded native-layout synthetic
    dataset with PII labels is in [`data/synthetic/`](../data/synthetic/README.md).
- [ ] **S1-02 - Generate the deterministic Mobile baseline**
  - Depends: S1-01.
  - Output: `scripts/generate_synthetic_geosol.py` baseline mode and fixture tests.
  - Done when: repeat runs with the same seed yield identical outputs;
    invented assessment/IEP fixtures exercise overlap, triage, carryovers, and
    varied intake/barrier scenarios without reproducing private cohort
    measurements; all names, IDs, contacts, and notes are synthetic.
  - Related progress (November 7, 2026): `python -m jvsg_triage.etl synthesize`
    deterministically generates native-layout FY2026 anti-join/case-note
    practice files with PII ground-truth labels in
    [`data/synthetic/`](../data/synthetic/README.md). The public profile now uses
    invented distributions. It does not implement the separate assessment/IEP
    overlap fixture, so this task remains open.
- [ ] **S1-03 - Add adversarial and scale fixture modes**
  - Depends: S1-02.
  - Output: separate noise/boundary fixtures and 500-record and 15,000+-service-row
    scale inputs.
  - Done when: WP 101/102 and WP-reported 203 rows, wrong-role 205 rows,
    cross-office assignments, duplicates, inactive IEPs, null/future dates, and
    fiscal boundaries are covered without changing baseline expected counts;
    scale counts/seed semantics follow D01 and D11.
- [ ] **S1-04 - Extend existing settings with explicit runtime validation**
  - Depends: S0-01, S0-04.
  - Output: extended package settings, non-secret environment examples, and tests.
  - Done when: local/offline mode needs no credentials; enabled integrations
    reject missing configuration explicitly; secret values do not appear in
    representations/errors; environment precedence is preserved; authorized
    edge connectivity remains opt-in and separate from import/test execution.

## Sprint 2 - Cohort isolation and deterministic aging

Goal: reproduce the baseline and all specified aging boundaries.

- [ ] **S2-01 - Implement current-year DVOP cohort isolation**
  - Depends: S1-01, S1-03.
  - Output: `etl/anti_join_engine.py` cohort function and `test_anti_join.py`.
  - Done when: vectorized Polars filtering honors fiscal window, code, role,
    active/open status, and approved office rules; unique SID anti-join yields
    exactly 48 baseline veterans; noise and duplicate fixtures do not inflate
    the cohort or leak another office's cases.
- [ ] **S2-02 - Implement prior-year carryover audit**
  - Depends: S2-01.
  - Output: separate reverse-anti-join audit result from the cohort function.
  - Done when: exactly 2 baseline active IEPs lacking a current-year assessment
    and dated before FY start appear; same-year IEPs, inactive cases, and cases
    with a qualifying assessment do not; audit records never inflate triage.
- [ ] **S2-03 - Implement verified-contact aging**
  - Depends: S2-01.
  - Output: `etl/velocity_aging.py` and `test_velocity_aging.py`.
  - Done when: latest assessment/verified DVOP or LVER touch drives idle days;
    0/14/15/29/30/89/90-day tests produce GREEN/GREEN/YELLOW/YELLOW/RED/RED/
    EXITED_90D; missing follow-up uses valid assessment; automated touches do not
    reset age; null/future dates follow D02; execution date is injectable.
- [ ] **S2-04 - Measure statewide ETL throughput and memory**
  - Depends: S0-03, S2-02, S2-03.
  - Output: repeatable benchmark and synthetic-safe measurement record.
  - Done when: D11's 15,000+-service-row workload completes in <120 ms with
    <85 MB using the approved measurement scope; record hardware, counts,
    repetitions, memory definition, and exact results; failures remain open.

## Sprint 3 - Privacy, barrier synthesis, and review

Goal: structured, private, auditable classifications rather than opaque decisions.

- [ ] **S3-01 - Implement scrub-before-inference and HMAC identity**
  - Depends: S1-01, S1-04.
  - Output: `etl/pii_scrubber.py`, privacy dependencies, and synthetic tests.
  - Done when: regex plus Presidio NER remove synthetic SSNs, names/name
    components, phones, emails, addresses, and raw SIDs; deterministic HMAC
    uses a required secret and differs with another secret; scrubber failures
    block inference; tests prove no raw identity reaches prompts or logs.
  - Partial implementation (November 7, 2026): [PII protocol v1.0](./pii_protocol.md) is complete.
    The regex and lexicon scrubber is in `privacy/scrubber.py` (not
    `etl/pii_scrubber.py`). HMAC identity, private extraction, residual scan,
    and 100% synthetic recall on all non-third-party labels are done. Presidio/NER
    for third-party names and the inference-blocking gate remain open.
  - Blocked for cloud inference: about 2,200 capitalized word pairs survive in
    the real T2 output. Most are organization names; some are likely untitled
    third-party names. Add local NER and measure `THIRD_PARTY` recall on
    `data/synthetic/` before any non-local use. Review whether the over-redacted
    common-word tokens need an allowlist.
- [ ] **S3-02 - Implement strict barrier and review schemas**
  - Depends: S0-03, S0-04.
  - Output: `slm/barrier_schema.py` and model validation tests.
  - Done when: TRN/HSG/MED/LEG and CRT/ACT/MIT/RES are strict; HHMM, nonnegative
    lifting limits, bonding, partner fields, and approved additional constraints
    validate; worst-state and readiness derivation cannot contradict domains;
    human filter is <=60 characters; `AI_Draft` and reviewer state are explicit.
- [ ] **S3-03 - Add constrained private inference and labeled fallback**
  - Depends: S3-01, S3-02.
  - Output: `slm/slm_classifier.py`, optional inference dependencies, and mocked
    Ollama/Azure client tests.
  - Done when: Instructor/Pydantic decoding uses temperature 0.0 and only
    sanitized text; configured private endpoints are supported; timeout,
    malformed response, and offline behavior are explicit; rule fallback is
    deterministic, labeled, and review-required; uncertain facts are not invented.
- [ ] **S3-04 - Persist human draft review and provenance**
  - Depends: S3-02, S0-04.
  - Output: review-state contract and tested approval/rejection transitions.
  - Done when: model outputs begin as drafts; qualified reviewers can approve,
    correct, or reject with provenance; changed interpretation invalidates stale
    approval; unreviewed output cannot become a placement/referral decision.
- [ ] **S3-05 - Cache only unchanged valid interpretations**
  - Depends: S3-03, S3-04.
  - Output: content-hash cache integrated into classification.
  - Done when: unchanged sanitized notes reuse results without a model call;
    changed notes/model/prompt/schema/rules invalidate cache; incomplete/failed
    output is not cached as success; cached drafts retain review state safely;
    repeated-run tests assert actual inference call counts.
- [ ] **S3-06 - Establish 20-scenario groundedness and kappa audit**
  - Depends: S3-03, S3-04.
  - Output: `slm/kappa_evaluator.py`, synthetic benchmark corpus, and review record.
  - Done when: qualified independent human labels cover 20 scenarios across
    domains/states; actual model-vs-human kappa is >=0.85; unsupported inference
    is separately reviewed; mismatched lengths, undefined kappa, and insufficient
    labels fail explicitly; synthetic unit tests do not masquerade as model audit.

## Sprint 4 - TOON protocol and local end-to-end execution

Goal: approved, measurable protocol behavior and a reproducible dry run.

- [ ] **S4-01 - Implement approved TOON grammar validation**
  - Depends: S0-03, S3-02.
  - Output: versioned grammar/schema under `data/schemas/`, `toon/validator.py`.
  - Done when: HMAC identity, required/optional keys, domain/state values,
    delimiters, duplicate/unknown fields, times, numeric ranges, and readiness
    obey D03/D04; malformed input yields explicit typed validation errors.
- [ ] **S4-02 - Implement deterministic serializer/parser**
  - Depends: S4-01.
  - Output: `toon/serializer.py`, `test_toon_protocol.py`, Hypothesis properties.
  - Done when: canonical ordering and optional omission are stable; approved
    lossless round-trip equality holds across generated profiles; distinct
    domain states/review-relevant fields are not silently discarded; invalid
    strings cannot bypass the validator.
- [ ] **S4-03 - Measure TOON token and byte savings**
  - Depends: S4-02.
  - Output: `benchmark_token_savings`, tokenizer dependency, benchmark tests.
  - Done when: equivalent approved JSON/TOON payloads use `cl100k_base`; exact
    token/UTF-8 byte counts and reduction are reported for the agreed standard
    corpus; >=50% token reduction passes D05's gate; report progress toward the
    55% target without copying the specification's illustrative counts.
- [ ] **S4-04 - Wire the local synthetic pipeline CLI**
  - Depends: S2-02, S2-03, S3-05, S4-02.
  - Output: `scripts/run_local_pipeline.py` and an end-to-end offline test.
  - Done when: one documented command generates/loads synthetic extracts, isolates
    48/2, ages, scrubs, classifies in explicitly labeled offline mode, and emits
    validated draft TOON; no messages/network calls occur; failures return a
    nonzero exit; repeat runs preserve state and produce deterministic core data.

## Sprint 5 - Watchlist and role-segmented digest rendering

Goal: usable operational artifacts without connecting to live M365 yet.

- [ ] **S5-01 - Build the four-tab watchlist workbook**
  - Depends: S2-03, S3-04, S4-02.
  - Output: `m365/excel_watchlist.py` and synthetic workbook tests.
  - Done when: Active_Triage_Roster, Office_Template, Caseload_KPIs, and
    Validation_Lists exist; all Prompt 5 roster fields are present; conditional
    aging colors, protected office template, barrier/partner dropdowns, and
    velocity/barrier KPI formulas are correct; identities follow D08; EXITED_90D
    is visible and distinct from RED.
- [ ] **S5-02 - Implement non-destructive refresh and disposition merge**
  - Depends: S5-01.
  - Output: tested state merge keyed by approved operational identity.
  - Done when: notes, latest verified contact, partner tags, manual overrides,
    next action, and review decisions survive repeated refresh; newer contact
    wins; cohort additions/removals/conversions have explicit disposition;
    spreadsheet formatting/validation and supported slicers are preserved or an
    approved limitation is recorded before use; aging is recomputed after merge.
- [ ] **S5-03 - Build persisted transition-based queue selectors**
  - Depends: S5-02, S0-04.
  - Output: tested DVOP/LVER queue selection logic and transition state.
  - Done when: RED escalation, new YELLOW, reviewed ACT-to-IEP candidates, and
    approved last-24-hour MIT/RES handoffs follow D07; first-run, repeated-run,
    exited-case, stale approval, timezone, and empty-queue cases are covered.
- [ ] **S5-04 - Render safe HTML and Teams Adaptive Cards**
  - Depends: S5-03.
  - Output: `m365/daily_digest.py` HTML/card renderers and contract tests.
  - Done when: office/role queues match selectors, one-line filters display
    correctly, synthetic user text is safely escaped, and contact/conversion/
    referral actions use the D08-approved Teams mechanism; no raw narrative or
    secret appears in card/email output.
- [ ] **S5-05 - Add workbook and digest dry-run outputs to the CLI**
  - Depends: S4-04, S5-04.
  - Output: synthetic end-to-end workbook, HTML, and card preview generation.
  - Done when: one documented command creates/reopens all outputs, preserves a
    synthetic specialist edit on refresh, verifies queue counts and draft
    restrictions, and performs zero deliveries.

## Sprint 6 - M365 synchronization, delivery, and write-back

Goal: close the operational loop with authorized, scoped integrations.

- [ ] **S6-01 - Implement managed-identity Graph access and routing**
  - Depends: S1-04, S0-04.
  - Output: `m365/graph_sync.py` authentication/client boundary and pilot routing.
  - Done when: approved identity and least-privilege Graph scopes are used;
    Bay Minette/Foley/Mobile routes validate against approved office roles;
    unknown office/destination is an explicit error; mocked tests need no tokens.
- [ ] **S6-02 - Synchronize the approved operational store**
  - Depends: S6-01, S5-02.
  - Output: SharePoint/workbook or other D08-approved store adapter.
  - Done when: read/merge/write preserves specialist state and detects concurrent
    edits; schema mismatches, throttling, and write failures are visible and
    retryable under an explicit policy; repeated sync does not duplicate rows.
- [ ] **S6-03 - Deliver digests with durable delivery tracking**
  - Depends: S6-02, S5-04.
  - Output: configured Teams/email delivery and per-office/run/channel records.
  - Done when: approved recipients receive only their role/office content;
    retries do not duplicate successful sends; partial failure remains visible;
    transition watermarks advance only under the approved successful-delivery
    policy; timeouts and throttling have bounded behavior.
- [ ] **S6-04 - Implement authenticated, replay-safe action handling**
  - Depends: S6-02, S5-04.
  - Output: shared handlers for contact, Code 205 conversion, and referral actions.
  - Done when: identity/office/role authorization, action validation, duplicate
    submission, and stale-update tests pass; timestamps persist and update aging;
    conversion/referral requires human authority and does not falsely claim a
    GeoSol write occurred; audit records omit sensitive narratives.
- [ ] **S6-05 - Verify an authorized synthetic M365 loop**
  - Depends: S6-03, S6-04.
  - Output: separate opt-in smoke procedure and synthetic-safe evidence.
  - Done when: in an approved test tenant/store, a synthetic refresh delivers
    both formats, an authorized action persists, and the next refresh reflects
    it; unauthorized access is denied; test resources/messages are cleaned up;
    ordinary CI remains offline.

## Sprint 7 - VOMA feasibility and runtime MCP tools

Goal: one deterministic evaluator across all integration surfaces.

- [ ] **S7-01 - Implement candidate schema and four-constraint evaluator**
  - Depends: S4-02, S0-03.
  - Output: typed CandidateJobOrder/result models, shared evaluator, and
    `test_voma_feasibility.py`.
  - Done when: all Prompt 6 candidate fields validate; shift/transit/lift/legal
    indicators and their product follow D04; score equals MOS similarity times
    feasibility; equality boundaries, overnight/missing data, multiple violations,
    and >=0.80 suppression explanations are tested without invented facts.
- [ ] **S7-02 - Expose FastAPI and OpenAPI 3.1 contract**
  - Depends: S7-01, S1-04.
  - Output: `voma_skill/fastapi_app.py`, POST
    `/v1/voma/evaluate-constraints`, and request/response contract tests.
  - Done when: schema declares OpenAPI 3.1, typed results match the evaluator,
    invalid TOON/jobs return explicit validation errors, office/role access
    follows the approved contract, and model inference is not invoked.
- [ ] **S7-03 - Expose the same evaluator as a FastMCP tool**
  - Depends: S7-01, S1-04.
  - Output: `voma_skill/mcp_server.py` tool
    `evaluate_veteran_stability_constraints`.
  - Done when: MCP and REST return equivalent typed results/explanations for
    identical inputs; malformed/unauthorized requests fail explicitly; neither
    server starts or makes a network call during import.
- [ ] **S7-04 - Verify constraint-skill latency**
  - Depends: S7-02, S7-03, S0-03.
  - Output: repeatable D11 benchmark and measured latency record.
  - Done when: the approved workload/scope/statistic is <15 ms with correctness
    assertions intact; record job counts, hardware, warm/cold state, repetitions,
    and transport scope rather than reporting evaluator-only timing as API timing.
- [ ] **S7-05 - Implement the three private local runtime tools**
  - Depends: S5-05, S3-01, S7-03.
  - Output: `query_non_cm_watchlist`, `synthesize_case_note_to_toon`, and
    `simulate_daily_digest` MCP tools.
  - Done when: queries enforce office/aging scope; synthesis scrubs synthetic
    input before private inference and yields drafts; simulation never sends;
    access is limited to the approved private boundary with no raw-note logging
    or public development exposure.

## Sprint 8 - Azure orchestration and release pipeline

Goal: deployable wrappers, not a second implementation of business logic.

- [ ] **S8-01 - Implement the approved weekday timer orchestration**
  - Depends: S6-03, S0-04.
  - Output: Azure Functions v2 host and timer in
    `azure_functions/function_app.py`.
  - Done when: configured hosting supports D06's 07:30 schedule; winter/summer
    UTC, weekdays, missed invocation, and duplicate invocation tests pass;
    timer invokes shared ETL/sync/delivery paths with visible failure records,
    not copied logic.
- [ ] **S8-02 - Add VOMA and digest-action HTTP wrappers**
  - Depends: S7-02, S6-04.
  - Output: Functions `voma-skill` and `digest-action` routes.
  - Done when: shared evaluator/action handlers are reused; authentication,
    authorization, invalid requests, replay, and HTTP result contracts match
    their existing surfaces; wrapper tests do not contact cloud services.
- [ ] **S8-03 - Define approved Azure infrastructure and identity**
  - Depends: S1-04, S0-04.
  - Output: reviewed infrastructure configuration and deployment settings for
    Functions, private inference/API hosting, approved data store, Entra, and
    Key Vault.
  - Done when: cloud/region and service support are verified; private endpoints,
    managed identities, least privilege, secret retrieval/auditing, approved
    retention, and provider data-handling controls are specified/tested; no
    resource is provisioned without explicit agency authorization.
- [ ] **S8-04 - Extend CI for implemented domain quality gates**
  - Depends: S4-03, S5-05, S7-03, S8-01, S8-02.
  - Output: existing CI expanded for synthetic generation, optional dependencies,
    lint/type checks, property tests, domain/integration contracts, and coverage.
  - Done when: clean Python 3.11 environment runs `ruff check .`, `mypy src`,
    `pytest --cov=src`, and synthetic dry run successfully; no live credentials,
    model downloads/calls, or outbound Graph calls are needed; add `pytest-cov`
    explicitly rather than assuming it exists.
- [ ] **S8-05 - Add gated deployment, health verification, and rollback**
  - Depends: S8-03, S8-04.
  - Output: approved `azure_deploy.yml` release workflow and operating procedure.
  - Done when: packaging/identity-based deployment targets only the approved
    environment behind approval gates; authorized synthetic smoke proves timer,
    API, store, private inference connectivity, and action health; tested rollback
    restores a known version/state; failures cannot be marked successful.

## Sprint 9 - Regional pilot and statewide operational readiness

Goal: prove access control, governance, and phased rollout readiness.

- [ ] **S9-01 - Build executive aggregates and Power BI RLS**
  - Depends: S6-02, S8-03.
  - Output: regional velocity/barrier dataset, dashboard definition, and access tests.
  - Done when: office managers see only their office and approved state roles see
    statewide aggregates; all seven LWDBs are representable; synthetic totals
    reconcile to source cohorts; example barrier percentages are not hardcoded;
    unnecessary identifiers and raw notes are excluded.
- [ ] **S9-02 - Add scoped RED manager escalation**
  - Depends: S6-03, S2-03.
  - Output: manager routing/escalation rules and delivery tests.
  - Done when: 30-89-day RED cases reach only approved managers under D07;
    90-day breaches use their separately approved disposition/escalation path;
    duplicate/retry behavior and failure visibility match ordinary digests.
- [ ] **S9-03 - Validate seven-LWDB routing and office templates**
  - Depends: S6-01, S5-01, S0-04.
  - Output: approved `config/lwdb_routing_table.json` structure and synthetic-safe
    routing/template tests.
  - Done when: each LWDB/office/role resolves unambiguously, missing/duplicate
    routes fail validation, cloned templates preserve schema, and rollout lists
    contain no unauthorized recipients or private contact data in source control.
- [ ] **S9-04 - Verify cached morning throughput and audit operations**
  - Depends: S2-04, S3-05, S3-06, S8-05.
  - Output: D11 daily-run benchmark and quarterly calibration/recovery procedure.
  - Done when: approved seven-LWDB change-only inference workload completes in
    <45 seconds with real measured cache hits/misses; model/provider/runtime
    versions are recorded; quarterly >=0.85 kappa, unsupported-inference review,
    sanitized monitoring, retention, backup/restore, and incident ownership have
    named operational approvers.
- [ ] **S9-05 - Publish frontline rulebook and sign off phased rollout**
  - Depends: S6-05, S9-01, S9-02, S9-03, S9-04.
  - Output: approved frontline specialist rulebook and separate regional/statewide
    acceptance records referenced from `docs/`.
  - Done when: Region 7 users validate zero-double-entry refresh, draft review,
    contact actions, IEP/referral disposition, and digests; Bay Minette/Foley/Mobile
    pilot approval and seven-LWDB promotion approval are distinct; Innovation
    Award evidence uses approved aggregates; rollback/pause criteria are explicit.

## Sprint 10 - Outreach intake and federal VOMA release

Goal: complete the specification's web/intake and federal integration surfaces.

- [ ] **S10-01 - Prepare and approve homepage welcome video**
  - Depends: S0-04.
  - Output: approved video content, caption/transcript assets, and ADOW web
    publication change record.
  - Done when: veteran/employer pathways are clear, content is approved for the
    agency site, playback is accessible, and publication is verified by the web
    owner without adding unapproved hosting or collecting sensitive information.
- [ ] **S10-02 - Implement approved interactive homepage carousel**
  - Depends: S0-04.
  - Output: ADOW web change for veteran support, employer/SkillBridge, and
    Stand Down/hiring-fair cards.
  - Done when: links target approved destinations, keyboard/mobile/accessibility
    checks pass, and the agency web owner verifies published behavior; external
    CMS work has evidence, not a placeholder marked complete.
- [ ] **S10-03 - Configure trackable localized QR-to-Bookings intake**
  - Depends: S0-04, S9-03.
  - Output: approved office-specific Bookings destinations, QR assets, and
    privacy-safe campaign routing.
  - Done when: QR scans from signage/web/event material reach the correct office;
    no SID or sensitive data appears in URLs/analytics; links can be updated by
    an authorized owner; localization/routing tests cover pilot offices.
- [ ] **S10-04 - Verify intake handoff and Stand Down readiness**
  - Depends: S10-01, S10-02, S10-03, S5-05, S9-05.
  - Output: documented intake-to-assessment operating path and event readiness sign-off.
  - Done when: synthetic virtual/walk-in/QR scenarios reach assigned staff and
    the approved Code 203 assessment/export/triage process without claiming an
    undocumented GeoSol API integration; April 2027 milestones use D10's approved
    calendar; responsible staff verify follow-up and event materials.
- [ ] **S10-05 - Complete the authorized USDOL VOMA handshake**
  - Depends: S7-04, S8-05, S9-05.
  - Output: USDOL-approved request/response/authentication contract and federated
    synthetic handshake evidence.
  - Done when: federal callers authenticate under approved cross-tenant policy;
    only approved pseudonymous constraints cross the boundary; no raw medical/
    legal notes are shared; invalid/unauthorized requests fail; federal and
    agency owners approve compatibility and performance.
- [ ] **S10-06 - Feed reviewed compatible matches into LVER digests**
  - Depends: S10-05, S6-03, S3-04.
  - Output: VOMA-results-to-LVER integration and Phase 4 acceptance record.
  - Done when: verified compatible candidates enter the correct office's digest,
    suppressed jobs include boundary explanations, duplicates and stale profiles
    are handled, drafts cannot bypass review, and a synthetic end-to-end scenario
    proves human-approved handoff; USDOL/ADOW owners sign off production release.
