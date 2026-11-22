# Engineering process, scalability path and MVP sprint

**Status: November 18, 2026.** Supporting material for the November 19
presentation. Everything described here runs on invented data. No live
records, SharePoint access or Azure resources are involved. The sprint and test
counts below are a dated proposal and snapshot, not evidence of current completion.

## 1. Continuous integration (CI)

Every push and pull request runs `.github/workflows/ci.yml` on a clean
Ubuntu runner with Python 3.11, read-only repository permissions and no
secrets. The job installs the project with `pip install -e ".[dev]"` and runs
three gates in order:

| Gate | Command | What it catches |
|---|---|---|
| Lint | `ruff check .` | Syntax errors, unused code, import order, common bug patterns (rules `E`, `F`, `I`, `UP`, `B`; 100-column lines). |
| Type check | `mypy src` | Type mistakes in the `jvsg_triage` package under `strict` mode. |
| Tests | `pytest` | Behavior regressions across the unit tests described below. |

A red check means the change is not ready to merge. Example from this
sprint: a merge accidentally committed unresolved conflict markers; the lint
gate failed immediately, and the branch was restored to the last verified
state before anything reached `main`.

## 2. Unit-test process

Tests live in `tests/` and use only synthetic fixtures; they make no network
calls and need no credentials. About 79 test functions cover:

| Area | File | Focus |
|---|---|---|
| MIS intake | `test_mis_intake.py` | Paired-report format validation, roster matching, rejection of malformed input. |
| Privacy scrubbing | `test_privacy_scrubber.py` | Local note scrubbing behavior and boundary cases. |
| Synthetic pipeline | `test_synthetic_pipeline.py` | Reproducible generated data and processing. |
| Management demo | `test_management_demo.py` | Follow-up bands, Excel/HTML publishing, TOON round trip, rehearsal status, last-good-output preservation. |
| Settings | `test_settings.py` | Environment-based configuration. |

Working rule: each module ships with focused tests for expected behavior and
boundary conditions, and processing is deterministic so a rerun on the same
inputs gives the same outputs. Passing tests show the code behaves as
specified on invented data. They do not validate scrubber effectiveness or
accuracy on real notes; that needs an authorized pilot.

Run locally with `pytest` (or the VS Code Testing panel, which the dev
container pre-configures).

## 3. Local development to Codespaces

One definition of the environment is used everywhere:

- `.devcontainer/devcontainer.json` pins a Python 3.11 image, installs the
  Python, Pylance, Ruff and Azure Functions extensions, enables pytest in VS
  Code and formats with Ruff on save.
- `.devcontainer/scripts/setup.sh` creates the virtual environment
  (`~/.venvs/jvsg`), installs the project with `.[dev,data]` and runs
  `pip check`.
- `.devcontainer/windows-wsl/devcontainer.json` gives Windows laptops the same
  container locally through WSL.
- `pyproject.toml` holds the single source of truth for dependencies, Ruff,
  mypy and pytest settings, so a laptop, a Codespace and CI run identical
  checks.

Result: open the repository in Codespaces or a local dev container, wait for
setup, and run the same lint, type check and test commands that CI runs. "Works
on my machine" differences are limited to the container image. The
[runbook](../operations/management_demo_runbook.md) covers previewing the demo in a
browser from Codespaces. Codespaces must never hold live records; see
[SECURITY.md](../../SECURITY.md).

## 4. Scalability to SharePoint and Azure

Today the pipeline reads and writes local folders that simulate a SharePoint
library. The design keeps storage, processing and delivery separate so each can
be swapped without rewriting the core logic.

| Stage | Today (implemented) | Possible later step (not built or approved) |
|---|---|---|
| Intake | Paired synthetic CSV/XLSX in a local folder; validation and local scrubbing. | Manual upload to an approved SharePoint library first; later an automated trigger. |
| Processing | Deterministic Python and Polars in the demo CLI. | The same package run in an Azure Functions host (`azure_functions/` is reserved; no function exists yet). |
| Output | Excel snapshot, HTML landing page and standard TOON export. | Excel in an approved library; HTML, Power BI or Power Automate only after separate review. |
| Identity and secrets | None needed. | Managed identity and approved Azure configuration; least-privilege processor, staff and reader groups. |

Important boundaries: SharePoint stores files and does not run this Python
pipeline. Hosting, tenant permissions, licensing, retention and privacy each
need their own IT, security and legal approval before live data is considered
(see the [MVP scope and approval checklist](./deliverables_and_required_inputs.md)).
Integrations stay optional and no network calls happen on import or in tests,
so the demo and CI keep working with no cloud dependency.

## 5. Next steps to MVP before the December 4 submission

The NASWA deadline is **Friday, December 4, 2026, 11:59 p.m. Eastern**. The
approval milestones (Nov 19 owners, Nov 23 form review, Nov 30 packet, Dec 2
administrator decision, Dec 3 submission) are in the
[briefing](./management_presentation_briefing.md#path-to-submission). The
engineering sprint below fits inside them. MVP here means the offline,
synthetic, manually operated demo described in the checklist, not a live
deployment.

| By | Engineering work | Done when |
|---|---|---|
| Thu Nov 19 | Present the demo; confirm CI is green on `main` and the presentation branch. | Both branches pass lint, type check and tests. |
| Fri Nov 20 | Triage feedback from the presentation into a short backlog; freeze scope to the manual paired-upload workflow. | Backlog agreed with the JVSG review lead. |
| Mon Nov 23 - Tue Nov 24 | Close known gaps: clearer failure messages, review-status preservation edge cases, added boundary tests. | New behavior has tests; CI green. |
| Wed Nov 25 | Evidence for the packet: screenshots or short demo clip, verified before/after counts, data-flow diagram, one-page limitations note, timed manual-vs-prototype rehearsal on invented inputs. | Artifacts reviewed for disclosure; results labeled as rehearsal. |
| Thu Nov 26 - Sun Nov 29 | Buffer and holiday weekend: documentation pass, reproducibility check from a fresh Codespace using only the runbook. | A new contributor can reproduce the demo from the README. |
| Mon Nov 30 | Feature freeze; only fixes for reviewer findings. Evidence packet handed to reviewers. | Every claim traced to a source or test. |
| Tue Dec 1 | Tag a release candidate; final CI and fresh-environment run. | Tagged commit is green. |
| Wed Dec 2 | Support the administrator's submit-or-defer decision. | Decision recorded. |
| Thu Dec 3 | Technical support for submission; archive the cleared synthetic demo. | Confirmation saved; if deferred, demo retained. |

Risks and mitigations:

- **Form requires operational results.** Defer rather than present rehearsal
  results as live impact.
- **Approvals slip.** Engineering work does not depend on them; the demo stays
  offline and synthetic.
- **Late changes break the demo.** Feature freeze on Nov 30 and CI gates on
  every change.
- **Scope creep toward live data, case-note AI or referrals.** Out of scope
  for this MVP; model output stays draft text for qualified human review.

Beyond MVP, and only after approvals, a small authorized pilot would measure
preparation time, data corrections and timely follow-up against the current
process before any Azure or SharePoint automation is designed.
