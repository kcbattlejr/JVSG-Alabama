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
[Codespaces quick start and troubleshooting table](docs/operations/management_demo_runbook.md#codespaces-and-teams-quick-start).
See [Start the HTML preview in VS Code](docs/operations/management_demo_runbook.md#start-the-html-preview-in-vs-code)
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

See the [documentation guide](docs/README.md) for runbooks, privacy rules, plans,
briefings, and the historical archive.

## Development

Repository layout:

- `src/jvsg_triage/`: Python modules and Microsoft 365 integration assets.
- `tests/`: Python tests; integration-specific synthetic harnesses live with their assets.
- `data/synthetic/`: invented fixtures; `config/`: project configuration.
- `docs/`: runbooks and project documentation; `docs/archive/`: historical material.
- `azure_functions/`: optional Azure integration notes.

The Microsoft 365 assets, including the SharePoint dashboard, are under
`src/jvsg_triage/m365/`. Generated files under `temp/` stay local and ignored;
restricted SQL and live data must remain in approved private storage.

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
