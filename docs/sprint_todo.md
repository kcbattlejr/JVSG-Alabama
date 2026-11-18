# JVSG Implementation Sprint TODO

Execution companion to the [implementation plan](./implementation_plan.md) and
[source specification](./executive_summary_enterprise_technical_specification_jvsg_non_cm_triage_azure_architecture.md).

## Active short sprint - Friday MVP readiness, November 17-20, 2026

**Goal:** present a reliable, clearly bounded synthetic MVP to ADOW management,
IT and legal on Friday morning, November 20. The branch name
`presentation/2026-11-19` is retained; November 19 is the final rehearsal day,
not the presentation date. Proposed working deadlines below use Central Time;
target technical readiness by 08:00 Friday, before the actual meeting time.
Owners are proposed roles, not confirmed individual assignments.

### Branch assessment and Tuesday execution evidence

Assessed November 17 at commit `67bc646`. The working tree was clean before
this documentation update; the remote branch tip matched local HEAD.
Relative to `main`, the branch adds the synthetic management demo, custom demo
TOON codec, pinned demo requirements, tests and presentation documentation.
It is a working offline presentation slice, not the complete implementation
described by the longer-term sprints below.

| Capability | Verified now | Friday boundary |
|---|---|---|
| Native CSV/XLSX intake | Layout/footer validation, cohort matching, HMAC tokenization, scrubbing and aggregate reconciliation run on generated fixtures | Uses the supplied anti-join; does not calculate the 203/205 cohort from separate reports |
| Reviewed profiles and aging | Separate synthetic workbook, strict fields, deterministic 15/30-day contact bands, preserved input review values | Not derived from case notes; not AI classification, approved policy or durable staff-review storage |
| Reporting | Baseline/refreshed Excel and HTML dashboards, two Excel charts per batch, watchlists and working file links | Static generated snapshots; presentation-machine rendering and usability still need human review |
| TOON and publication | Custom `@TOON demo-1`, hash/reconciliation checks, lossless round trips, verified batch publishing | Not an approved VOMA contract, token-savings benchmark or access-control system |
| Integrations | Local simulated file arrival | No live SharePoint/Graph, Teams, database, model, VOMA or Azure deployment |

Executed successfully before defining this sprint:

```bash
python -m jvsg_triage.demo rehearse --output temp/management-demo
python -m pytest
python -m ruff check .
python -m mypy src
```

The documented Python 3.11 environment was used. Results: **141 tests passed**,
Ruff passed, and strict mypy passed for 28 source files. GitHub
[CI run 19](https://github.com/kcbattlejr/JVSG-Alabama/actions/runs/44118381110)
also passed for the assessed commit. Both generated batches passed the explicit
CLI `verify` command. Additional checks against the actual generated artifacts
confirmed the Excel card/watchlist counts, two charts per workbook, exact changed
profile values, and all 21 local presentation file links. No presentation link
targets the restricted scrubbed-note outputs. Generated outputs are Git-ignored.

| Expected measure, confirmed in Tuesday's run | Baseline | Refreshed |
|---|---:|---:|
| Synthetic participants / matched notes | 18 / 18 | 19 / 19 |
| Recent contact, 0-14 days | 6 | 8 |
| Follow-up due, 15-29 days | 6 | 6 |
| Extended contact gap, 30+ days | 6 | 5 |
| Awaiting staff review | 16 | 17 |
| Cohort participants without notes / unmatched notes | 0 / 0 | 0 / 0 |

`DEMO-0005` changes from 30 to 0 days since contact and from critical to partly
addressed housing; `DEMO-0019` is added. Existing source review values remain
unchanged. The fixture residual scan reported zero findings; this is **not**
evidence of anonymity or real-world scrubber efficacy.

Open the generated [landing page](../temp/management-demo/index.html) first.
It links the baseline/refreshed HTML dashboards, Excel workbooks, reviewed-profile
inputs and TOON. The [rehearsal evidence](../temp/management-demo/rehearsal.json)
contains synthetic aggregate results. These links work after a local run;
generated outputs are intentionally absent from GitHub. See the
[runbook](./management_demo_runbook.md) for local viewing and loopback-only
serving if the remote browser cannot open files.

**Readiness verdict:** technical rehearsal is green. Presentation acceptance is
pending the project owner's output review, target-machine visual checks, final
recording and content review. Repository safeguards, historical-content removal,
licensing and live-pilot approvals remain unverified/open as documented in
[SECURITY.md](../SECURITY.md); passing tests does not close those gates.

### Executable Tuesday-Friday checklist

- [x] **FRI-01 - Establish the runnable baseline** - Tuesday, November 17.
  - Owner: engineering. Depends: none.
  - Done: execute the existing demo before changing behavior; verify both
    batches, exact expected counts, actual Excel outputs and links, tests,
    lint, types and current-commit CI. Evidence: assessment above and local
    rehearsal evidence. No demo behavior changes were made for this assessment.
- [ ] **FRI-02 - Review the output and prioritize changes** - Tuesday, 17:00.
  - Owner: project owner, supported by engineering. Depends: FRI-01.
  - Review the landing page, both dashboards, Excel charts/watchlist, updated
    contact/housing example and visible human-review boundary.
  - Done when: feedback identifies the screen/artifact, observed issue and
    desired result; classify each item as P0 (incorrect/unsafe/misleading or
    blocks the demonstration), P1 (needed for a clear presentation), or deferred.
    Explicitly accept the output or identify bounded changes; silence is not
    acceptance. Do not copy sensitive review material into this public file.
- [ ] **FRI-03 - Apply accepted demo corrections** - Wednesday, November 18, 17:00.
  - Owner: engineering; project owner accepts output. Depends: FRI-02.
  - Done when: agreed P0/P1 changes have focused regression tests where behavior
    changes, related runbook/script updates, a successful full rehearsal and
    passing quality checks. If an intentional fixture change alters expected
    counts, update the documented expectations and tests together, with owner
    acceptance. Defer feature expansion; no changes if output is accepted as-is.
- [ ] **FRI-04 - Finalize the management/IT/legal narrative** - Wednesday, 17:00.
  - Owner: presenter, with designated program/IT/legal reviewers. Depends: none.
  - Use the [recording script](./management_demo_script.md) and capability matrix
    above. Frame the request as agreement on contracts, ownership and next
    review steps, not approval of production readiness.
  - Done when: slides/script distinguish native intake from separate reviewed
    profiles, local simulation from M365, and custom TOON from an approved
    contract; human decision authority and privacy limitations are explicit.
    List source ownership/licensing, hosting/access, retention, repository
    safeguards and historical-content follow-up as approved or still open,
    never presumed complete. Capture actual assignments/approvals privately
    through an approved channel.
- [ ] **FRI-05 - Rehearse on the presentation machine and freeze** - Thursday,
  November 19, 12:00. Owner: presenter and engineering.
  - Depends: FRI-03, FRI-04.
  - Done when: HTML filters and all needed file links work in the target browser;
    Excel opens with readable charts, labels, dates and watchlist at presentation
    zoom; baseline/refreshed totals agree. Time the 8-minute recording and the
    full 45-minute meeting agenda below. Confirm the failure message/last-good
    batch behavior without altering the accepted output; automated regression
    coverage already passes. Record the frozen commit and batch IDs in the
    approved handoff record. No dependency upgrades or new integrations after
    freeze; a blocking fix requires regeneration, tests and another review.
- [ ] **FRI-06 - Record and check the offline fallback** - Thursday, 16:00.
  - Owner: presenter. Depends: FRI-05.
  - Done when: the reviewed recording plays with readable text/audio, and a
    local copy of the complete synthetic output folder opens without network
    access on the presentation machine. Review everything before sharing;
    keep restricted note outputs closed and out of the presentation bundle,
    and exclude secrets, account menus, unrelated files and notifications.
    Keep the generated dashboards/Excel and recording as the fallback; do not
    substitute stale output while claiming a fresh run.
- [ ] **FRI-07 - Perform the morning go/no-go** - Friday, November 20, by 08:00.
  - Owner: presenter and engineering. Depends: FRI-06.
  - Done when: the frozen batches still verify, the latest pointer and success
    status identify the accepted refresh, files/recording open, and the owner
    confirms no unresolved P0/P1 items. Use the reviewed offline fallback if
    live execution/display fails, explicitly identifying it as prerecorded or
    previously verified output. If neither path is verified, stop the demo
    rather than misrepresent success. Do not rerun `rehearse` over manual edits:
    it resets generated source fixtures.

### Meeting scope and finish line

Retain the proposed **45-minute review**: purpose 5 minutes, safeguards 5, live
synthetic walkthrough 15, proposed workflow 5, legal/IT review 10, and decisions
5. The existing approximately 8-minute recording fits inside the walkthrough;
use the balance for opening Excel, refresh comparison and questions. This does
not replace the longer meeting with an 8-minute presentation.

Friday is ready when the owner accepts the visible outputs, no P0/P1 issue is
open, the accepted batches and checks pass, the target-machine rehearsal and
offline fallback pass, and the capability/approval boundaries are clear.
Production approvals may remain open for a clearly labeled synthetic discussion;
they block a live pilot and any release-ready claim, not the offline review.
Do not attempt SharePoint authentication, cloud deployment, AI classification,
third-party-name NER, a production TOON contract or new referral automation in
this short sprint. Those remain separately governed backlog work.

## How to execute

- Longer-term tasks below retain their original status unless their own
  acceptance criteria are verified. The active Friday checklist records only
  presentation-slice evidence; it does not close production sprint gates.
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

Goal: establish an honest starting point, resolve implementation contracts, and
prepare the synthetic-only demonstration.

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
- [ ] **S0-05 - Prepare the synthetic prototype demonstration and review**
  - Depends: none.
  - Target: Friday morning, 2026-11-20; final rehearsal 2026-11-19.
  - Execution: active Friday MVP readiness sprint above; output review and
    presentation sign-off remain open.
  - Output: a rehearsed 45-minute run-of-show, synthetic walkthrough checklist,
    implemented/proposed/production-requirements capability matrix, and legal/
    IT-security decision and next-steps record.
  - Done when: the timed agenda covers purpose and operational need (5 min),
    scope and safeguards (5), synthetic CSV/XLSX layout validation, case-note
    matching, privacy scrubbing, reconciliation and evaluation results (15),
    proposed operational workflow (5), legal and IT/security review (10), and
    decisions/next steps (5); the walkthrough is rehearsed offline using only
    synthetic data; each shown capability is verified as implemented, while
    gaps are identified rather than simulated; residual privacy limits and
    qualified human review are explicit; SharePoint/M365 is labeled proposed;
    source ownership/publication rights, proposed Apache-2.0 licensing, hosting,
    access, retention, repository safeguards, and historical public-content
    removal are listed with unresolved items clearly marked and next steps
    assigned by responsible role. No live records or production-readiness
    claims appear in the demo.

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
