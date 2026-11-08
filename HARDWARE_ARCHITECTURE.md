# Hardware and workspace architecture

Verified locally: November 8, 2026. This describes development infrastructure,
not an approved production deployment.

## Hardware and network roles

| Node | Role | Verified or required capability |
| --- | --- | --- |
| Dell Precision 7820 Windows server | Primary development and compute host | Ubuntu 24.04 on WSL2; native Linux Docker; NVIDIA RTX 3060, 12 GiB VRAM |
| TrueNAS SCALE server | Private file redundancy and PostgreSQL backup destination | Tailscale and pinned-key SSH verified; nightly Data Science container dump enabled; isolated PostgreSQL 16 restore passed |
| Personal home laptop | Secondary development client | Existing Windows Tailscale peer; use private SSH or its own checkout |
| Work laptop, Windows 11 Enterprise | Browser-only client | GitHub Codespaces; no administrator rights or local Docker/Tailscale installation assumed |

The Windows server, TrueNAS and personal laptop are the existing mesh devices.
The work laptop is not a mesh device. A Codespace may become a separately
authorized mesh device; it does not inherit the browser laptop's identity.
The server has two Xeon Gold 6126 CPUs: 24 physical cores and 48 logical
processors total. Live inventory reports **128 GiB installed RAM**, not the
160 GB stated in older documents. Physical storage inventory reports a Samsung
PM981a NVMe (954 GiB nominal capacity) and a Toshiba external USB disk (1863 GiB).
Capacity is not a free-space measurement or a backup/health certification.

## Architecture

```text
Work browser -> GitHub Codespaces (portable CPU environment)
                    |
                    | optional, authorized userspace Tailscale + SSH
                    v
Windows server / existing Tailscale
    tailnet-only TCP 2223 -> loopback WSL SSH TCP 2222
                               |
                               v
                        Ubuntu 24.04 WSL2
                        native ext4 source checkouts
                        native Docker + NVIDIA runtime
                          |                |
                          v                v
                     GPU dev worker    private PostgreSQL 16
                                             |
                                     local pg_dump + SSH
                                             v
                                  TrueNAS verified dataset
```

Codespaces performs CPU work in GitHub's infrastructure. Remote GPU work is an
SSH command executed on the local worker, not GPU passthrough into a Codespace.
The workstation and Codespaces databases are independent. Git synchronizes
committed code; it does not synchronize database volumes, ignored files,
credentials, datasets or uncommitted changes.

## Native Linux workspace

Use these paths inside Ubuntu:

```text
~/src/Data-Science
~/src/JVSG-Alabama
~/src/Data-Science-JVSG.code-workspace
```

The checkouts live on WSL's ext4 filesystem, not under `/mnt/c` or OneDrive.
This avoids cross-filesystem I/O penalties for Git, Python environments, Docker
bind mounts and package installation. The OneDrive copies remain as preserved
Windows copies; they are not continuously synchronized working trees.
JVSG's existing uncommitted ETL changes and local data were copied locally.
Windows virtual environments and caches were excluded; Linux environments were
recreated. Do not delete the preserved copies until any unique work is reviewed.

Open a checkout from Windows PowerShell using VS Code's WSL remote connection:

```powershell
code --remote wsl+Ubuntu-24.04 /home/$env:USERNAME/src/Data-Science
code --remote wsl+Ubuntu-24.04 /home/$env:USERNAME/src/JVSG-Alabama
code --remote wsl+Ubuntu-24.04 /home/$env:USERNAME/src/Data-Science-JVSG.code-workspace
```

If the Ubuntu username differs from the Windows username, substitute the real
Ubuntu home directory. In VS Code, confirm the lower-left remote indicator says
WSL: Ubuntu-24.04. Install workspace extensions into WSL or the container, not
only into the Windows extension host.

Data Science provides a portable CPU configuration and a local NVIDIA GPU
configuration under `.devcontainer`. Its explicit Compose project name is
`data-science`, shared by manual commands and the VS Code dev-container CLI.
JVSG retains its Python 3.11 container; native Ubuntu uses Python 3.12, supported
by its existing minimum-version declaration. Its native environment is `.venv`,
while the container uses `/home/vscode/.venvs/jvsg`, so incompatible interpreters
cannot reuse the same mounted virtual environment. JVSG installs `dev,data` extras.
Azure CLI is optional and is not automatically installed for an undeployed
Azure integration. Use each repository's own environment, not a shared Windows
`.venv`.

## Security and credentials

- No public PostgreSQL, Docker TCP API, public Jupyter or Tailscale Funnel.
- New worker access uses tailnet-only Serve TCP 2223. Ubuntu SSH is loopback-only,
  public-key-only, limited to the development user, with root login disabled.
- An existing separate Windows SSH listener on TCP 2222 has a broad firewall
  rule. It is **not fully hardened** until the administrator runs the documented
  firewall script and verifies effective policy. Ubuntu hardening does not
  harden Windows sshd.
- Restrict Codespace grants to the worker's required SSH port, not the entire
  mesh or NAS. Enroll it manually only after policy review.
- Generate a dedicated Codespace SSH key there if approved; authorize only its
  public key on the worker. Never upload the workstation private key.
- Docker group access is effectively host-root-capable. This worker is trusted
  development access, not a sandbox for hostile code.
- Keep secrets outside OneDrive and source control. Data Science refuses secret
  initialization in OneDrive paths and masks its bootstrap secret inside dev.
- Real veteran records, employer materials and confidential datasets must not
  enter GitHub, Codespaces, build contexts, prompts or cloud artifacts.
- Data Science builds allow only its Dockerfile and dependency manifest into
  the build context. JVSG uses a prebuilt development image; package installation
  occurs inside the locally mounted workspace, not by uploading it as an image.

## Backups and availability

Data Science PostgreSQL 16 runs without a published host port. The app role is
not a superuser and cannot create roles/databases, replicate or bypass RLS.
Its named volume persists beyond container replacement.

Backup tooling performs consistent custom-format dumps, checksum verification,
strict pinned-host SSH and atomic final-file publication. It does not provide
PITR, global-role backup, retention deletion or encryption at rest.
On November 8, a PostgreSQL 16 `app` dump was transferred to
`/mnt/backup-server/postgres/dumps/data-science-container/`, checksum-verified,
and restored into a disposable NAS PostgreSQL 18 database. Both source and
restore had zero user tables; this does not certify populated-data recovery.
The scratch database was dropped. A subsequent host-generated dump also passed
an isolated PostgreSQL 16 restore, without network access or a persistent test
volume. NAS PostgreSQL's existing nightly dumps, including `jvsg_synth`, are
successful.

The existing Syncthing Documents folder mirrors both OneDrive repositories to
`/mnt/backup-server/backups/server-documents/`. It is bidirectional and has no
Syncthing versioning; recursive daily ZFS snapshots retain two weeks. UrBackup
has completed workstation file backups in its app-managed `/backups` mount.
Restic is authenticated and append-only. No additional file backup or clone
was added.

The Data Science container's nightly dump timer is enabled on the Ubuntu host.
It runs at 02:10 America/Chicago, catches up after downtime and uses a dedicated
host-generated upload-only SSH key outside OneDrive. A root-owned NAS forced
command accepts only a dump filename and matching SHA256 checksum, publishes
atomically, and retains this dump family for 30 days after successful uploads.
Host staging in `~/.local/state/data-science/backups/` retains seven days;
failed partials are kept for diagnosis. Existing PostgreSQL dataset snapshots
cover the destination for 14 days. The timer's first run succeeded; arbitrary
commands and bad checksums were rejected.

Live Docker inspection verified both repository bind mounts are covered by
Syncthing. JVSG has no separate application-data volume, only its workspace,
editor tooling volume and display socket. No container clone or additional
whole-repository backup was added. User lingering keeps the timer available
without an open editor/Linux login, but WSL, Docker and Tailscale must run.
Failure status is available in the user systemd journal; there is no push/email
alert or automatic Windows pre-login startup.

Ubuntu Docker and SSH are enabled. Development services have restart policies.
The current-user `DataScienceUbuntuHost` scheduled task starts Ubuntu at Windows
logon without storing a password. This is not unattended availability before
login, a server sleep policy or a promise of continuous uptime.

## Verified and pending

Verified: native ext4 checkouts, CPU and GPU container smoke tests, CUDA nbody
computation, private mesh SSH GPU command, least-privilege PostgreSQL operations,
isolated PostgreSQL dump/restore, and published Data Science configurations.
JVSG tests, Ruff and mypy passed in native Python 3.12 and container Python 3.11.
The actual VS Code dev-container CLI successfully initialized both repositories.

The reproduced JVSG installation failure was an incompatible mounted virtual
environment: Python 3.11 reused the native Python 3.12 `.venv` and could not load
SSL. Separate environment paths fix it without bypassing TLS verification.
Registry and package downloads also showed intermittent network timeouts.
The host's VS Code Docker credential-helper injection is disabled; existing
credential stores are not erased. These containers do not need private registry
credentials. If a future private registry is needed, configure native Docker
authentication explicitly rather than forwarding a workstation store blindly.

Pending: browser-created Codespace runtime, Codespace Tailscale enrollment and
restricted grants, dedicated remote key, administrator Windows firewall
hardening, and unattended boot availability.
GitHub CLI authentication currently lacks the Codespaces scope; a successful
repository API call does not imply permission to create/manage Codespaces.
