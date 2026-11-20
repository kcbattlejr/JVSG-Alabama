# JVSG-Alabama

A synthetic prototype for helping Alabama Jobs for Veterans State Grant (JVSG)
staff see who may need follow-up and what support needs are already recorded.
It is **not approved for live data, production use, or external release**.

## Open the management demo

From the repository root in an activated Python 3.11+ environment:

```bash
python -m pip install -r requirements-demo.txt
python -m jvsg_triage.demo rehearse
```

Open `temp/management-demo/index.html` locally in a browser. Use this folder
for the current rehearsal; open the refreshed HTML dashboard or download the
Excel dashboard and standard `profiles.toon` from the landing page. The dashboards add plain-language charts by office, staff review status and support area. No web
server, model, or cloud account is needed.

For the state laptop and Teams call, use the
[Codespaces quick start and troubleshooting table](docs/management_demo_runbook.md#codespaces-and-teams-quick-start).
See [Start the HTML preview in VS Code](docs/management_demo_runbook.md#start-the-html-preview-in-vs-code)
for the web server command. Download the verified presentation ZIP before the
meeting so it also works offline.

The Python demo matches and scrubs two invented reports using native MIS layouts.
A separate invented staff-review workbook supplies the fields used for
follow-up bands, Excel/HTML dashboards, and the lossless standard TOON
export. The optional AI-assisted wording uses invented totals only and
requires human review before display. The Python demo does not independently
compute the 203/205 anti-join, infer profile fields from notes, connect to
SharePoint, send notifications, or transmit data to a federal system.
Separate MIS SQL reports are maintained outside this repository in restricted
private storage. They are not an approved production service or automated
delivery.

## Documentation

| Start here | Use it for |
|---|---|
| [Stakeholder briefing](docs/management_presentation_briefing.md) | November 19 presentation, value and limits, and the December 4 NASWA deadline |
| [Demo runbook](docs/management_demo_runbook.md) and [historical recording script](docs/archive/management_demo_2026-11-19_script.md) | Rehearse the synthetic demo or review the dated presentation |
| [Documentation archive](docs/archive/README.md) | Find superseded scripts and drafts retained for history |
| MIS SQL reporting documents | Kept in restricted private storage, not in this repository |
| [MVP scope and approval checklist](docs/deliverables_and_required_inputs.md) | Agree on pilot scope, ownership, access, and evidence |
| [MIS intake contract](docs/mis_intake_contract.md) and [PII protocol](docs/pii_protocol.md) | Review report parsing, data tiers, scrubbing, and known limitations |
| [Security and publication requirements](SECURITY.md) | Handle sensitive material, repository governance, and external release |

## Development

Use the provided VS Code dev container or a local Python 3.11+ virtual
environment. In the container, activate with
`source /home/vscode/.venvs/jvsg/bin/activate`.

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m mypy src
```

The code for the rehearsal is under `src/jvsg_triage/demo/`. The underlying
intake and scrubber are under `etl/` and `privacy/`; generated test data and
evaluation tools are documented under [data/synthetic/](data/synthetic/README.md).
Azure, Microsoft 365 synchronization, case-note inference, and VOMA remain
unimplemented integration paths. The optional settings in `.env.example` do
not grant access or authorization.

Use only generated fixtures in development, demos, prompts, and CI. Do not copy
live reports into the workspace or use Git ignore rules as a privacy control.
Package metadata remains proprietary pending agency ownership and licensing
approval; repository visibility is not a license.
