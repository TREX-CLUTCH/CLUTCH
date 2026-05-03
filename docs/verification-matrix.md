# Verification Matrix

Use this matrix to prove the public CLUTCH distribution feature by feature.
It is written for a clean release tree or a fresh install, not for a private
lab workspace.

## Release Tree Gates

| Capability | Command | Expected Evidence |
| --- | --- | --- |
| Private-data scanner | `python3 tools/clutch_distribution_scan.py . --json` | `finding_count=0` |
| Public release gate | `python3 tools/clutch_public_release_gate.py --root . --json` | `status=ready_for_operator_review` |
| Final visibility review | `python3 tools/clutch_public_visibility_review.py --root . --json` | `status=ready_for_manual_visibility_review` and `remote_visibility_change_performed=false` |
| Combined public verification | `make verify` | scanner, release gate, visibility review, landing smoke, Web smoke, collab transport smoke, and install smoke pass |
| Static landing page | `make landing-smoke` | `status=passed`, local CSS loads, `assets/clutch.png` loads, GitHub CTA is present |

## First Install Gates

| Capability | Command | Expected Evidence |
| --- | --- | --- |
| Install without sudo | `bash installer/install.sh --prefix "$CLUTCH_HOME"` | files install under the user-owned `CLUTCH_HOME` |
| First-run wizard preview | `python3 installer/clutch_first_run_wizard.py --plan-only` | local paths, machine id, artifact store, GitHub preference, and Web preference are shown before writes |
| Doctor check | `python3 installer/clutch_doctor.py` | missing optional setup is reported as actionable guidance, not a crash |
| Session re-entry | `python3 scripts/clutch_ctl.py session-entry` | project inference or manual attach guidance appears, and the Web console starts or prints a local URL |
| Clean install smoke | `python3 tools/clutch_public_install_smoke.py --root . --json` | install, first-run wizard, doctor, session-entry, session_entry_repeat, first project, backup, snapshot, refresh, and project_workspace_hygiene all pass |

## Core Workflow Gates

| Capability | Command | Expected Evidence |
| --- | --- | --- |
| Project registration | `python3 scripts/clutch_ctl.py project-create --help` then register a small git project | project metadata stays under `CLUTCH_HOME`, not in the project git workspace |
| Main session binding | `python3 scripts/clutch_ctl.py session-attach --project <project_id> --bind-role main --yes` | binding appears in project status with role `main` |
| Backup | `python3 scripts/clutch_ctl.py project-backup --project <project_id>` | local backup manifest and repo bundle are created |
| Snapshot | `python3 scripts/clutch_ctl.py project-snapshot --project <project_id> --write` | snapshot manifest records source heads and restore plan |
| Refresh preview | `python3 scripts/clutch_ctl.py project-refresh --project <project_id> --dry-run` | readiness, sync, restore, and artifact-pointer status are reported without writes |
| Artifact pointers | `python3 scripts/clutch_ctl.py project-artifact-pointers --project <project_id>` | large datasets, model weights, media, and logs are represented by user-owned paths or URIs rather than committed files |

## Web And Monitor Gates

| Capability | Command | Expected Evidence |
| --- | --- | --- |
| Web console | `python3 scripts/clutch_ctl.py web-console-start --host 127.0.0.1 --port 8765` | Dashboard, Monitor, Commands, Backups, and Help render locally |
| Web health | `python3 scripts/clutch_ctl.py web-console-status` | backend reports ready and the command surface is render-ready |
| Packaged Web smoke | `python3 tools/clutch_public_web_smoke.py --root . --json` | first-run config enables Web auto-start, session-entry reports readiness, `/api/health` is ready, and Help/Monitor/Backups static UI markers load |
| Help tab | open `http://127.0.0.1:8765` | Help describes CLUTCH as a local-first multi-PC Codex layer for AI and robotics labs |
| Collab monitor | `python3 scripts/clutch_ctl.py collab-monitor-status --project <project_id> --json` | role source, monitor visibility, worker freshness, and recent evidence are visible |
| Notifications | `python3 scripts/clutch_ctl.py notify-mode-long --minutes 5` | notification preference changes locally and does not authorize any gated action |

## Multi-PC Collab Gates

CLUTCH recommends a direct wired LAN when practical, but the public package
must not contain a real peer address, SSH alias, credential, or private mount.
Users choose their own transport after install.

| Capability | Command | Expected Evidence |
| --- | --- | --- |
| Packaged collab transport smoke | `python3 tools/clutch_public_collab_smoke.py --root . --json` | `machine_count=2`, `open_request_count=0`, `public-main`, `public-worker`, `req-public-smoke`, `request_opened`, and `request_result` are present |
| Shared transport init | `python3 collab_transport/scripts/clutch_collab_file_transport.py init --shared-root /path/to/shared-clutch-collab --project-id demo --machine-id main-laptop --role main` | main role state is written under the user-owned shared root |
| Worker transport init | same command with `--machine-id gpu-worker --role worker` | worker role state is written under the same project namespace |
| Main-to-worker request | use the collab guide to write a request record, then inspect the shared root | request, acknowledgement, and result evidence stay project-scoped |
| Monitor integration | open the Web Monitor tab or run `collab-monitor-status` | main and worker state appears in the same operator-visible monitor flow |
| SSH or Codex exec usage | configure your own SSH and Codex sessions outside the release tree | CLUTCH records role/evidence state but does not ship or infer private SSH endpoints |

## Away Development Gates

| Capability | Command | Expected Evidence |
| --- | --- | --- |
| Plan review | `python3 scripts/clutch_ctl.py project-away-report --project <project_id> --json` | objective, scope, stop conditions, expiry, and verification requirements are visible |
| Continue intent | use the Web Commands tab or project away commands | work continues only inside the current plan and stops when scope or approval boundaries are exceeded |
| Recovery evidence | run backup, snapshot, refresh, and test commands after each slice | the next operator can see what changed, what passed, and what remains blocked |

## Publication Gates

| Capability | Command | Expected Evidence |
| --- | --- | --- |
| Release package | `python3 scripts/clutch_public_release_package.py --output-dir /path/to/release-output --version <version> --clean --json` | `status=ready_for_private_release_upload` |
| Artifact integrity | `sha256sum -c clutch-public-<version>.sha256` | checksum reports `OK` |
| Release notes review | inspect `clutch-public-<version>.release-notes.md` | notes describe public behavior and contain no private machine, path, IP, SSH, credential, or private repo evidence |
| GitHub first screen | inspect `README.md` in the private staging repository | brand image, landing preview, quick start, feature list, release confidence, and final visibility gate are visible |
| Manual public switch | no command in CLUTCH performs this | the repository stays private until the operator explicitly approves the visibility change |
