# SharePoint-first management demonstration runbook

<<<<<<< HEAD
Target recording: Friday, November 20, 2026. Synthetic-only discussion prototype
for management, IT and legal; not a production deployment or approval request
to process real records in this repository.

=======
Target presentation: Thursday, November 19, 2026. Synthetic-only discussion prototype
for management, IT and legal; not a production deployment or approval request
to process real records in this repository.

For the value proposition, decisions and NASWA schedule, see the
[stakeholder briefing](./management_presentation_briefing.md).

## Codespaces and Teams: quick start

**Before the call:** Open the repository on GitHub, select
`presentation/2026-11-19`, then choose **Code > Codespaces**. Create a codespace
on that branch or open a clean existing one. In **Terminal > New Terminal**,
run `git status --short --branch` to confirm the branch and
`git pull --ff-only` to get the final commit. If the branch is wrong or there
are changes you need to keep, use a fresh codespace instead of resetting it.

From the repository root in the Codespaces Bash terminal:

```bash
source "$HOME/.venvs/jvsg/bin/activate"
python -m jvsg_triage.demo rehearse
```

Wait for `verification` to say **All hashes, reconciliation and TOON round
trips passed**. Expect 18 fictional people in the baseline and 19 in the
refresh. The default run is offline and has no AI copy; Copilot Chat is not
needed. Prepare the [presentation ZIP](#download-a-laptop-ready-copy) before
the call. Use it for the VS Code preview or keep a copy on the laptop in case
Codespaces is unavailable.

### Start the HTML preview in VS Code

After creating `temp/management-presentation.zip` below, run this from the
repository root in the active Bash terminal:

```bash
preview_dir=$(mktemp -d) && \
  python -m zipfile -e temp/management-presentation.zip "$preview_dir" && \
  python -m http.server 8765 --bind 127.0.0.1 --directory "$preview_dir"
```

- **Codespaces:** In the terminal panel, open **Ports**. If port `8765` is
  missing, choose **Forward a Port** and enter `8765`. Check that visibility
  is **Private**. Use **Open in Preview** if offered, or **Open in Browser**
  to open the forwarded address in a browser tab.
- **Local VS Code:** Open `http://127.0.0.1:8765/` using **Simple Browser: Show**
  in the Command Palette, or open the same address in your regular browser.

Keep the terminal running while you present. Press **Ctrl+C** to stop the
server. Serve only the extracted synthetic ZIP, never the workspace or full
rehearsal folder. If port forwarding is blocked by policy, use the downloaded
laptop copy instead.

### Download a laptop-ready copy

After a successful run, use this Bash block from the repository root. It
packs only the named presentation files, not the full rehearsal directory:

```bash
(
  set -eu
  cd temp/management-demo
  python - <<'PY'
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from jvsg_triage.demo.pipeline import verify_batch

status = json.loads(Path("status.json").read_text())
rehearsal = json.loads(Path("rehearsal.json").read_text())
if status["state"] != "success" or status["batch_id"] != Path(rehearsal["refreshed"]["path"]).name:
    raise SystemExit("Rehearsal is not current. Rerun it before packaging.")
files = [Path("index.html"), Path("rehearsal.json")]
for name in ("baseline", "refreshed"):
    batch = Path(rehearsal[name]["path"])
    verify_batch(batch)
    files.extend(batch / filename for filename in (
        "dashboard.html", "dashboard.xlsx", "reviewed_profiles.xlsx", "profiles.json", "profiles.toon",
    ))
    for kind, suffix in (("anti_join", "203_205_anti_join.synthetic.csv"),
                         ("case_notes", "case_notes.synthetic.xlsx")):
        source = Path(f"simulated_sharepoint/{name}_{suffix}")
        expected = rehearsal["native_intake"][name]["source_sha256"][kind]
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise SystemExit("Synthetic source file changed. Rerun rehearsal before packaging.")
        files.append(source)

with ZipFile("../management-presentation.zip", "w", ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path)
print("Ready to download: temp/management-presentation.zip")
PY
)
```

In the Codespaces **Explorer**, right-click
`temp/management-presentation.zip` and choose **Download**, if allowed by
laptop policy. On the laptop, right-click the ZIP and choose **Extract All**.
Open the extracted `index.html` in Edge or another approved browser. Click
**Updated report: 19 fictional people** for HTML or **Download the updated
Excel report** for Excel. Keep the extracted folder structure intact. Have the
Excel Dashboard and the HTML page open before the call. In Teams, share only
the presentation window, switch to Excel when needed, and avoid showing the
raw note text, restricted outputs, or account and terminal information.

Treat the ZIP as **synthetic meeting material**, not an external-release
package. Review it before showing or sharing it. Do not copy `restricted/`,
open a public port, or serve the workspace or full rehearsal folder.

### If something goes wrong

| What you see | What to do |
|---|---|
| Codespace is starting or `activate` is missing | Wait for container setup. If setup failed, run `bash .devcontainer/scripts/setup.sh` from the repository root, then activate again. Use the already downloaded copy if setup cannot finish before the meeting. |
| `No module named jvsg_triage` or dependency errors | Activate the Codespaces environment, then run `python -m pip install -r requirements-demo.txt` and retry. If installation is blocked, use the downloaded copy. |
| Rehearsal exits with an error or the counts are wrong | Read the terminal error and `temp/management-demo/status.json`. Do not present an older run as a fresh refresh. Rerun the default `rehearse` with no custom inputs; if it still fails, use the verified laptop copy and describe it as a saved rehearsal. |
| Preview says `Address already in use` | Stop your old preview with Ctrl+C, or change `8765` to `8766` in the command and open the matching port. |
| Browser opens raw HTML or linked files are missing | Extract the whole ZIP first, then open the extracted `index.html` in Edge, not in the VS Code editor or inside the ZIP. |
| Excel prompts for repair or charts do not fit | Re-download the current workbook rather than opening a repaired copy. Lower Excel zoom until column Q is visible. If Excel is blocked or still fails, show the HTML dashboard. |
| Codespaces or downloads are blocked | Use the verified copy prepared before the call. If no approved copy is available, present the stakeholder briefing and explain that the demo could not be opened; do not bypass device policy. |
| Copilot Chat is blank or returns `null` | Continue with this runbook. No step requires chat or a model. |

>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
## What actually works

```text
Simulated SharePoint raw report-pair upload (anti-join CSV + case-notes XLSX)
  -> native layout/footer validation, cohort matching, HMAC tokenization and scrubbing
  -> separate synthetic human-review profile input (not derived from case notes)
  -> deterministic aging and closed-vocabulary profile validation
<<<<<<< HEAD
  -> generated Excel/HTML dashboards and lossless @TOON demo-1 package
=======
  -> generated Excel/HTML dashboards and lossless standard TOON export
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
  -> verified immutable batch
```

The demonstration represents the paired native report upload using local,
synthetic-only snapshots in `temp/management-demo/simulated_sharepoint/`. It
does not authenticate to Microsoft 365 or download/upload a tenant file.
Processing validates the native contracts, matches notes to the supplied
anti-join cohort, tokenizes identifiers with a fixed synthetic-only demo key,
and writes scrubbed notes under `temp/management-demo/restricted/`.

The native reports do **not** supply the office, aging, or four-domain fields in
the current dashboard. Those come from a separate invented human-review profile
workbook under `reviewed_profiles/`; they are not extracted or classified from
case notes. The demo makes this boundary visible. Production would need approved
source/profile contracts, a qualified review process, and an approved TOON
contract before those steps could be joined.

<<<<<<< HEAD
The Gemini references are visual inspiration only. No reference workbook data,
embedded logos, baseline figures, infrastructure details or claimed validation
results are redistributed in the implementation. All distributions are invented.
=======
Do not use third-party visual references, old workbooks, or unreviewed local
copies as presentation inputs. All distributions in this rehearsal are invented.
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88

## Install and run

From the repository root, in an activated Python 3.11 virtual environment:

```bash
python -m pip install -r requirements-demo.txt
python -m jvsg_triage.demo rehearse --output temp/management-demo
```

Open `temp/management-demo/index.html` in a browser. It starts with links to the
raw synthetic anti-join CSV and paired case-notes workbook, then shows validation
and privacy-processing counts, the separate synthetic review input, and the
generated baseline/refreshed dashboards and TOON files. The HTML has no remote
dependencies, fonts, assets, requests or backend. The **Demo files** section and
each report link to the Excel report, reviewed-profile input and TOON file.
Each report shows its actual folder and file locations from the page address.
For local files this is the filesystem path; when served over HTTP it is the URL
path. On disk, expand `temp/management-demo/batches/` in VS Code and select the
matching report folder. Excel links may download; check the browser Downloads list.
Open the Excel workbook in desktop Excel or an approved Excel browser viewer;
there is no requirement to host a web application.
<<<<<<< HEAD

If Excel reports that it removed `AutoFilter` and `Table` from
`/xl/tables/table1.xml`, an older generator defined overlapping worksheet and
table filters on the Watchlist. The corrected generator keeps only the native
table's filter, preserving the filter dropdowns and table styling. Rerun the
rehearsal with the corrected code, reopen the landing page and download the
newly linked workbook. Batches are immutable: old downloads and old batch links
remain unchanged. Do not use Excel's repaired copy as the verified demo artifact.
Confirm the new workbook opens without a repair prompt in desktop Excel before
presentation; Python/XML checks alone do not establish Excel compatibility.

If a remote VS Code browser cannot open the local file, either download the
generated folder to your recording computer or serve **only this synthetic
output directory**, on loopback, while rehearsing:

```bash
python -m http.server 8765 --bind 127.0.0.1 --directory temp/management-demo
```

Open `http://127.0.0.1:8765/`; stop the server with Ctrl+C afterward. Do not serve
the repository root or expose a development port publicly.
=======
The Dashboard tab uses columns A through Q, with a spacer between the two
charts. If Q is off-screen, lower the Excel zoom before screen sharing.
If an older download prompts Excel to repair the Watchlist table, rerun
`rehearse` and download a fresh workbook from the refreshed landing page.
Check that Excel opens it without a repair prompt and that the Watchlist
column filters are visible before recording.

If a remote browser cannot open the local file, download only the dashboard or
prepare a reviewed synthetic presentation copy on the recording computer.
Preserve relative paths for the files you intend to open from the landing page.
Do not include `restricted/`; do not serve the workspace or rehearsal folder
over HTTP. Hiding a link is not access control.
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88

For code validation, install the development extra and run:

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m mypy src
```

### Prepare and rehearse the paired workflow

```bash
python -m jvsg_triage.demo prepare --output temp/management-demo
python -m jvsg_triage.demo rehearse --output temp/management-demo
```

`latest.json` identifies the last successfully verified batch. For explicit
verification, substitute the printed batch ID (no angle brackets):

```bash
python -m jvsg_triage.demo verify --batch temp/management-demo/batches/BATCH_ID
```

`prepare` creates the raw synthetic report pairs and reviewed-profile inputs.
`rehearse` validates and scrubs both native report snapshots, then generates and
verifies their corresponding dashboard/profile batches. Its `rehearsal.json`
contains only file hashes and aggregate counts; the scrubbed note files are
restricted outputs and are not linked from the presentation page. The HMAC key
is a public synthetic-demo constant, not a credential; never use it for real
records. No model download, network service or cloud account is needed.

<<<<<<< HEAD
=======
### Optional: show the AI-assisted management briefing

The standard run displays **Verified snapshot changes only (no AI copy)**.
The [starter AI draft](../data/synthetic/management_briefing.draft.json) is based
only on the invented aggregate comparison. To see the exact facts, or prepare a
fresh prompt for an approved model, run `python -m jvsg_triage.demo briefing-prompt`.
Do not supply the full `rehearsal.json`, workbooks, identifiers or notes to a model.

1. Copy the draft JSON to `temp/management-demo/briefing.reviewed.json`. Compare
   each point against the prompt facts and verified snapshots. Edit or reject
   any unsupported claim; no person-level inference or recommendation is allowed.
2. Only after a person completes that review, set `review_status` to `reviewed`.
   Keep the version and facts fingerprint unchanged. This is an operator
   attestation, not an authenticated approval mechanism or a truth check.
3. Generate and open the landing page:

   ```bash
   python -m jvsg_triage.demo rehearse --output temp/management-demo \
     --reviewed-briefing temp/management-demo/briefing.reviewed.json
   ```

The renderer accepts exactly three short points and rejects drafts, malformed
files and fingerprints for different facts. The landing page makes no model
call. `rehearsal.json` records the rendered wording and its SHA-256 alongside
the baseline and refreshed batch references; the immutable dashboard/TOON
batches are unchanged. If the opt-in run is rejected, do not show an older
landing page as current: rerun `rehearse` without `--reviewed-briefing` and
confirm the fallback label before presenting.

>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
## Expected results

| Metric | Baseline | Refreshed |
|---|---:|---:|
| Invented participants | 18 | 19 |
| Recent contact: 0-14 days | 6 | 8 |
| Follow-up due: 15-29 days | 6 | 6 |
| Extended gap in contact: 30 or more days | 6 | 5 |
| Awaiting staff review | 16 | 17 |

- The synthetic native pair contains 18/19 cohort members and the same number
  of matched notes in each snapshot.
<<<<<<< HEAD
- `DEMO-0005`: contact date changes to November 20; days since contact change from
=======
- `DEMO-0005`: contact date changes to November 19; days since contact change from
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
  30 to 0; the housing barrier changes from critical to partly addressed.
  Other barriers may still need review.
- `DEMO-0019`: added to the South demonstration office.
- Existing source review values remain unchanged, including Reviewed records.
- `rehearsal.json` records both snapshots and the exact changed/added IDs.
<<<<<<< HEAD
- Nothing is sent to Teams, GeoSol, SharePoint, a partner or a model.
=======
- Rehearsal sends nothing to Teams, GeoSol, SharePoint, a partner or a model.
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88

## Synthetic human-review profile contract and demo assumptions

The separate human-review input contains exactly one worksheet, `Demo Intake`. Row 1 is
`JVSG_SYNTHETIC_DEMO_V1`; row 2 contains these human-readable column headings:

```text
Demonstration participant, Demonstration office, Assessment date,
Last recorded contact, Transportation, Housing, Health, Legal, Staff review status
```

Participant numbers are `DEMO-` plus four digits, not real identifiers. Office
names are North, Central and South demonstration office. Dates appear as
<<<<<<< HEAD
"Nov 20, 2026" in reports and date-formatted Excel cells; the loader also accepts
=======
"Nov 19, 2026" in reports and date-formatted Excel cells; the loader also accepts
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
YYYY-MM-DD text. Source dropdowns use full descriptions, not codes.
Earlier code-based profile headers and values remain accepted for compatibility;
the normalized JSON and compact TOON keep their stable machine-readable fields.
Contact may be empty; assessment is required. Reject duplicates, missing/extra
columns, unknown state/office/review values, formula cells, empty batches,
contact before assessment, future dates, additional sheets and oversized files.

Aging uses calendar days since last contact, or assessment if contact is absent.
The 15/30 boundaries are presentation assumptions, not approved follow-up policy.
The explicit `--as-of` date avoids a dashboard changing with the recording date.
Never infer the meaning of native MIS `Date1`-style fields from this demo.

Transportation, housing, health and legal needs are displayed as Critical barrier,
Needs support, Partly addressed, Resolved or Not yet assessed. The "Most pressing
recorded need" summary selects critical, needs support, not assessed, partly
addressed, then resolved, and names the relevant support area(s).
It is an explanatory demo rollup, not an eligibility,
clinical or referral score. Barrier states and review status are supplied synthetic human-review inputs, not
AI classification or fields extracted from the native reports. Review state is
passed through; it is not independently verified authorization. A refresh never
writes back to the profile workbook. Make demo edits in that synthetic input,
not in a generated dashboard.

## TOON and reproducibility

<<<<<<< HEAD
`profiles.toon` uses the reference-inspired **custom @TOON demo-1 dialect**,
not the general Token-Oriented Object Notation standard or an approved federal
VOMA contract. Its fixed fields preserve every normalized profile attribute:
identity, office, assessment/contact/as-of dates, four independent domain states,
review status, idle days and alert. `~` encodes a missing contact date. The parser
rejects unknown versions, reordered/extra fields and noncanonical values.
Round-trip equality is verified for every record before publication.
=======
`profiles.toon` is a [standard TOON tabular array](https://toonformat.dev/guide/format-overview#arrays-of-objects-tabular-form)
with one header and one row per profile. Its columns match `profiles.json`;
a missing contact date stays `null` and days since contact stays a number.
The offline verifier checks the row count, column order, canonical form and exact
round-trip equality before publication. This is a demo profile, not an approved
federal VOMA contract.

Use the current batch linked from `temp/management-demo/index.html`; older
downloads may still contain the custom `@TOON|V:demo-1` format. To check an
export independently, the
[reference TOON CLI](https://toonformat.dev/cli/) can decode it to JSON for
comparison with the accompanying `profiles.json`. The CLI is not a dependency
of the offline demo.
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88

Each immutable `batches/<SHA-256>/` directory contains:

| File | Purpose |
|---|---|
| `reviewed_profiles.xlsx` | Exact synthetic human-review profile input |
| `profiles.json` / `profiles.toon` | Equivalent normalized profiles |
| `summary.json` | Reconciled aggregate counts |
| `dashboard.xlsx` | Plain-language charts/list and definitions; technical sheets hidden |
| `dashboard.html` | Plain-language filters, contact counts, support details and overview |
| `manifest.json` | Source/output hashes, execution date, version and dependency versions |

`verify` checks hashes, source-to-profile reconciliation, all TOON round trips,
summary and HTML equivalence, row counts and serialized byte counts. Hashes
detect accidental alteration; they are not signatures or authorization controls.
The manifest reports UTF-8 bytes against equivalent compact JSON, **not tokens,
real-data accuracy or a promised compression percentage**.

The normal presentation does not require reading machine codes or a glossary.
The HTML has explanations next to the measures and a plain-language support
breakdown for each person. Technical encodings and fingerprints are tucked into
closed "for IT review" sections. In Excel, TOON and Provenance are hidden sheets
(a presentation choice, not a security control); Dashboard, Watchlist and
Definitions remain visible. Contact frequency and support needs are deliberately
separate: recent contact does not imply a person's barriers are resolved.

Repeated rehearsals in separate output roots produce byte-identical artifacts
with the same inputs, date, code and pinned runtime set. Workbook ZIP metadata
and timestamps are normalized. Tests explicitly change the writer clock.
Dependency upgrades can change output bytes; runtime versions are included in
batch identity. This is not a claim of byte stability across every Python,
operating-system or library release.

The publisher stages and verifies a batch before advancing `latest.json`.
Failed refreshes exit nonzero, leave the prior batch/pointer intact, and write
`status.json` with `state: failed`. A previously opened static dashboard does
not poll status: an operator must check status before presenting it as current.
Runs are single-operator; concurrent writers and a managed scheduler are not
implemented. Rerunning `prepare`/`rehearse` resets their generated source fixtures;
use a separately named copy for manual experiments.

## Public-review and production boundary

Use only generated fixtures. The marker and schema are not an anonymizer or
proof that a user-supplied workbook has no personal information in metadata,
comments or other embedded content. Never feed live exports or agency workbooks
to this demo. All generated outputs stay under Git-ignored `temp/`,
`data/private/` or an explicitly chosen external directory. Review recordings
and artifacts before sharing; do not capture terminals with secrets, file lists
outside the demo, real Teams chats or browser account information.

The native MIS intake/scrubber is exercised in the rehearsal using paired
synthetic reports. Its scrubbed notes are not used to populate the barrier
profile: that is a separate synthetic human-review input. Unstructured
production case notes still require the privacy protocol and qualified review
before any inference. No real-world scrubber efficacy is claimed here.

Before any live pilot, IT/legal/domain owners must approve the actual workbook
contract and ownership, refresh/receipt/version rules, least-privilege site/file
access, identity and secret management, appropriate hosting, retention, access
separation, audit/error handling and operational definitions. Direct Graph
ingestion, production schema mapping, access control, durable staff edits,
automated triggers, notifications, inference and VOMA integration remain future
work. SharePoint does not execute this Python by storing it in a document library;
HTML hosting/embedding also requires tenant-specific review.

See [SECURITY.md](../SECURITY.md), the
<<<<<<< HEAD
[SharePoint proposal](./sharepoint_data_visualization_proposal.md) and
=======
[MVP scope and approval checklist](./deliverables_and_required_inputs.md) and
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
[recording script](./management_demo_script.md). Public review is not licensing,
deployment, security-settings or live-data approval.
