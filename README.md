# JVSG-Alabama

Python project scaffold for the Alabama JVSG Non-Case Managed (Non-CM) veteran
triage and VOMA stability-constraints initiative. The intended system includes
synthetic GeoSol data workflows, privacy-preserving processing, operational
digests, and local or Azure-hosted services.

> **Current status:** This is a prototype, not an approved production system.
> Native MIS intake validates the anti-join CSV and
> case-notes XLSX (headers, title rows and the `Total Rows` footer). It matches
> notes to cohort SIDs, scrubs them under the [PII protocol](docs/pii_protocol.md)
> into a private, Git-ignored folder, and ships a seeded synthetic practice
> dataset with PII ground truth. It does not recompute the 203/205 anti-join,
> classify case notes, persist to a database, send Microsoft 365 messages, or
> deploy Azure services.

## Development environments

The Python 3.11 development container can be used in GitHub Codespaces or
locally with VS Code and Docker. Use synthetic data for development and demos.

### GitHub Codespaces

1. Open the repository on GitHub and choose **Code → Codespaces → Create
   codespace**.
2. Wait for the dev container to finish creating and installing dependencies.
3. Open a terminal and activate the container environment:

   ```bash
   source /home/vscode/.venvs/jvsg/bin/activate
   ```

The container installs development and data extras. Azure CLI is not installed
automatically: no Azure deployment is currently implemented. Install it only
when an authorized Azure workflow requires it.
The container environment is `/home/vscode/.venvs/jvsg`; the native WSL
environment remains `.venv`. Keeping them separate prevents a mounted Python
3.12 environment from breaking TLS/package installation in the Python 3.11
container. In the container use `/home/vscode/.venvs/jvsg/bin/python -m pytest`.

### Local development

Prerequisites: Git, Python 3.11 or newer, and either:

- `uv` (recommended), or
- `venv` and `pip`.

```bash
git clone https://github.com/kcbattlejr/JVSG-Alabama.git
cd JVSG-Alabama
uv sync --extra dev
uv run pytest
uv run ruff check .
```

Equivalent standard-library virtual environment setup:

```bash
git clone https://github.com/kcbattlejr/JVSG-Alabama.git
cd JVSG-Alabama
python -m venv .venv
```

Activate the environment (`source .venv/bin/activate` on macOS/Linux, or
`.venv\Scripts\Activate.ps1` in PowerShell), then run:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
ruff check .
```

To open the project in a local VS Code dev container instead, install Docker
Desktop or Docker Engine and the VS Code Dev Containers extension, then use
**Dev Containers: Reopen in Container**.

## Configuration

Copy `.env.example` to `.env` for local overrides. The default configuration
uses local development mode and does not require credentials or external
services. Settings are loaded from environment variables; environment
variables take precedence over `.env`.

Never commit `.env`, credentials, live GeoSol exports, or other sensitive
information. Do not put live veteran data in Codespaces, GitHub, CI artifacts,
or this repository. Use only approved environments and synthetic data until
the applicable agency security and data-handling approvals are in place.

The `azure` runtime mode and integration settings are configuration hooks, not
an implemented or approved production deployment. Azure and Microsoft 365
authentication and Key Vault retrieval must be configured and authorized
separately.

## Synthetic demonstration

In a Codespaces terminal, activate the environment as described above, then
run the following from the repository root. This uses the checked-in fictional
reports and a predictable key **only for this synthetic demonstration**. Do
not reuse the key for real data.

```bash
export SID_HMAC_SECRET='synthetic-only-demonstration-key-0001'
python -m jvsg_triage.etl inspect \
  --anti-join data/synthetic/fy2026_203_205_anti_join.synthetic.csv \
  --case-notes data/synthetic/fy2026_case_notes.synthetic.xlsx
python -m jvsg_triage.etl extract \
  --anti-join data/synthetic/fy2026_203_205_anti_join.synthetic.csv \
  --case-notes data/synthetic/fy2026_case_notes.synthetic.xlsx \
  --output temp/synthetic-demo
python -m jvsg_triage.etl evaluate \
  --anti-join data/synthetic/fy2026_203_205_anti_join.synthetic.csv \
  --case-notes data/synthetic/fy2026_case_notes.synthetic.xlsx \
  --labels data/synthetic/fy2026_case_notes.pii_labels.jsonl
unset SID_HMAC_SECRET
```

The extraction prints aggregate counts and writes synthetic redacted notes and
a manifest to the Git-ignored output folder. Dataset sizes are recorded in
`data/synthetic/manifest.json`. The evaluation reports recall against synthetic
labels, not real-world accuracy; it does not detect unadorned third-party names.
The [PII protocol](docs/pii_protocol.md) explains
this gap and other limits. Do not treat redacted output as anonymous or use
the demo to process live data.

## Public review and licensing

This repository is public for review. The code is currently marked proprietary
pending a licensing decision; public visibility alone does not grant an
open-source license. Apache-2.0 is the proposed license, subject to legal
approval and confirmation of source ownership; it has not been granted.
Legal review should separately confirm rights to included
third-party material and suitability of published aggregate information.
Report suspected vulnerabilities or sensitive material privately to the
maintainers rather than posting details in a public issue. See
[SECURITY.md](SECURITY.md) for reporting and public-release requirements.

## Project layout

```text
.devcontainer/       Shared Python 3.11 Codespaces/local container
.github/             Copilot guidance and CI workflow
azure_functions/     Reserved for the Azure Functions host
config/              Non-secret project configuration and data schemas
data/
  synthetic/         Seeded synthetic MIS downloads + PII labels (versioned)
  private/           Git-ignored scrubbed (T2) extraction outputs
src/jvsg_triage/     Installable Python package
  etl/               Native MIS contract, intake, extraction pipeline, CLI
  privacy/           PII scrubber (protocol v1.0)
  synthetic/         Synthetic dataset generator and recall evaluator
  m365/              Microsoft 365 workbook, Graph, and digest integrations
  slm/               Barrier models and private inference integrations
  toon/              TOON serialization and validation
  voma_skill/        API and MCP integration surfaces
tests/               Automated tests
```

The `etl`, `privacy` and `synthetic` packages are implemented. Other domain
modules remain directory scaffolding; integrations are not implemented.

## Native MIS report intake

Keep the download formats unchanged: **203/205 anti-join CSV, case-notes XLSX**.
Use live downloads only in an agency-approved environment; never put them in
GitHub, Codespaces, or CI. The loader discovers the
actual headers after any title rows and validates a versioned layout: 46 CSV
columns at row 1, and 12 XLSX columns at row 4 with a blank column B, wrapped
header labels and a `Total Rows` footer.

```powershell
$env:SID_HMAC_SECRET = '<32+ byte key>'
python -m jvsg_triage.etl extract --anti-join temp\<file>.csv `
  --case-notes temp\<file>.xlsx --output temp\private
```

The anti-join supplies only the list of SIDs. From the case notes, only the note
text for those SIDs is kept. Notes are scrubbed into `temp\private\redacted_notes.jsonl`;
only aggregate counts are printed. To practice without live data, use the files in
[`data/synthetic/`](data/synthetic/README.md).

See [the intake contract](docs/mis_intake_contract.md) for the typed model and
commands, and [the PII protocol](docs/pii_protocol.md) for data tiers,
redaction rules and known limits.

## Common checks

```bash
pytest
ruff check .
mypy src
```

GitHub Actions runs lint, type checking, and tests for pushes and pull requests.

## Next implementation milestones

Planning documents live in [`docs/`](docs/):

- [Enterprise technical specification](docs/executive_summary_enterprise_technical_specification_jvsg_non_cm_triage_azure_architecture.md)
  - requirements authority and rollout vision.
- [Deliverables and required inputs](docs/deliverables_and_required_inputs.md)
  - report samples, ETL workflow, SharePoint and TOON outcomes, operational
    decisions, and the management input checklist.
- [SharePoint data visualization proposal](docs/sharepoint_data_visualization_proposal.md)
  - phased reporting workflow, visualization options, minimum permissions,
    security boundaries, and management approval decisions.
- [Implementation plan](docs/implementation_plan.md) - architecture boundaries,
  decision gates, source traceability, and release criteria.
- [Sprint TODO](docs/sprint_todo.md) - discrete tasks, dependencies, acceptance
  criteria, and completion evidence.

The plan and sprint TODO expand these milestones; they do not indicate that the
planned functionality has already been implemented.

1. Classify scrubbed notes into reviewed barrier schemas and validate TOON output.
2. Implement the contact-velocity state machine on the SID cohort.
3. Strengthen de-identification for third-party names (local NER plus review)
   before any non-local inference.
4. Add M365 and VOMA interfaces behind explicit configuration and tests.
5. Add Azure Functions and deployment workflows after the target environment,
   identity model, and security approvals are confirmed.

Human specialists retain decision authority over case interpretation and
referrals. AI-generated classifications or filters must remain reviewable and
must not be treated as final case decisions.
