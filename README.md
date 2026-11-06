# JVSG-Alabama

Python project scaffold for the Alabama JVSG Non-Case Managed (Non-CM) veteran
triage and VOMA stability-constraints initiative. The intended system includes
synthetic GeoSol data workflows, privacy-preserving processing, operational
digests, and local or Azure-hosted services.

> **Current status:** This repository contains the developer environment and
> package foundation. It does not yet process GeoSol data, classify case notes,
> send Microsoft 365 messages, or deploy Azure services.

## Development environments

The same Python 3.11 development container can be used in GitHub Codespaces or
locally with VS Code and Docker.

### GitHub Codespaces

1. Open the repository on GitHub and choose **Code → Codespaces → Create
   codespace**.
2. Wait for the dev container to finish creating and installing dependencies.
3. Open a terminal. The editable package and development tools are ready.

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
authentication, Key Vault retrieval, and Tailscale connectivity must be
configured and authorized separately. No Tailscale auth key is stored in this
repository or automatically used by the dev container.

## Project layout

```text
.devcontainer/       Shared Python 3.11 Codespaces/local container
.github/             Copilot guidance and CI workflow
azure_functions/     Reserved for the Azure Functions host
config/              Non-secret project configuration and data schemas
data/
  synthetic/         Safe location for generated synthetic fixtures
src/jvsg_triage/     Installable Python package
  etl/               GeoSol joins, aging, and privacy processing
  m365/              Microsoft 365 workbook, Graph, and digest integrations
  slm/               Barrier models and private inference integrations
  toon/              TOON serialization and validation
  voma_skill/        API and MCP integration surfaces
tests/               Automated tests
```

The domain modules above are directory scaffolding only; implementations will
be added and tested as each workflow is developed.

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
- [Implementation plan](docs/implementation_plan.md) - architecture boundaries,
  decision gates, source traceability, and release criteria.
- [Sprint TODO](docs/sprint_todo.md) - discrete tasks, dependencies, acceptance
  criteria, and completion evidence.

The plan and sprint TODO expand these milestones; they do not indicate that the
planned functionality has already been implemented.

1. Build deterministic synthetic GeoSol extracts and test fixtures.
2. Implement the 203/205 anti-join and contact-velocity state machine.
3. Add privacy scrubbing, reviewed barrier schemas, and TOON validation.
4. Add M365 and VOMA interfaces behind explicit configuration and tests.
5. Add Azure Functions and deployment workflows after the target environment,
   identity model, and security approvals are confirmed.

Human specialists retain decision authority over case interpretation and
referrals. AI-generated classifications or filters must remain reviewable and
must not be treated as final case decisions.
