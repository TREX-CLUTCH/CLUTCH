# Public Demo Script

This script is for a public CLUTCH walkthrough after the repository has passed
the release gate and the operator has approved publication. It keeps the demo
inside the public boundary: no private machine names, no lab IP addresses, no
SSH aliases, no robot motion, no credentials, and no hidden local folders.

## Demo Boundary

Say this before running commands:

CLUTCH is a local-first Codex orchestration layer for AI and robotics labs. It
helps Codex re-enter projects, coordinate multi-PC work, keep collab state
visible, and preserve backup/snapshot evidence. It does not grant authority for
hardware motion, sudo, credential changes, destructive restore, or publication
without explicit operator approval.

Use a disposable shell and a fresh local home:

```bash
export CLUTCH_HOME="$(mktemp -d)/.clutch"
```

## Single-PC Proof

This is the first demo path. It should take roughly 10 to 15 minutes and prove
that a user can install CLUTCH without private infrastructure.

```bash
unzip clutch-public-*.zip
cd clutch-public-*
export CLUTCH_HOME="${CLUTCH_HOME:-$HOME/.clutch}"
bash installer/install.sh --prefix "$CLUTCH_HOME"
cd "$CLUTCH_HOME/foundation/current"
python3 installer/clutch_first_run_wizard.py
python3 installer/clutch_doctor.py
python3 scripts/clutch_ctl.py session-entry
```

Explain what happened:

- the installer copied the public foundation into the chosen `CLUTCH_HOME`;
- the first-run wizard asked for the user's folders, machine id, GitHub
  preference, admin token, and optional collab plan;
- doctor checked layout and local readiness;
- `session-entry` entered through CLUTCH and opened or printed the Web console
  URL.

## First Project Demo

Create a small project and show that CLUTCH metadata stays outside the project
git repository.

```bash
MACHINE_ID="$(python3 scripts/clutch_ctl.py machine-profile --json \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["machine_id"])')"
PROJECT_ROOT="$HOME/clutch-projects/my-project"

mkdir -p "$PROJECT_ROOT"
cd "$PROJECT_ROOT"
git init
git config user.name "CLUTCH Example"
git config user.email "example@clutch.local"
printf '# My Project\n' > README.md
git add README.md
git commit -m "Initial project"
git branch -M main

cd "$CLUTCH_HOME/foundation/current"
python3 scripts/clutch_ctl.py project-create \
  --project my-project \
  --display-name "My Project" \
  --machine-workspace "$MACHINE_ID=$PROJECT_ROOT" \
  --repo-source "my-project:$MACHINE_ID=$PROJECT_ROOT" \
  --no-repo-required \
  --participant-machine "$MACHINE_ID" \
  --owner-machine "$MACHINE_ID" \
  --role-policy none \
  --no-admin-guard-required \
  --yes

python3 scripts/clutch_ctl.py session-attach --project my-project --bind-role main --cwd "$PROJECT_ROOT" --yes
python3 scripts/clutch_ctl.py project-backup --project my-project
python3 scripts/clutch_ctl.py project-snapshot --project my-project --write
python3 scripts/clutch_ctl.py project-refresh --project my-project --dry-run
```

Point out three things:

- `project-backup` records a recoverable local backup;
- `project-snapshot` records source heads and restore evidence;
- `project-refresh --project my-project --dry-run` is preview-first, so it
  explains readiness without applying changes.

## Web Console

If the browser did not open automatically:

```bash
python3 scripts/clutch_web.py --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

Show these areas:

- project overview and attention items;
- backup and snapshot evidence;
- Help tab for operating protocol;
- Monitor tab for collab visibility.

The Web console is a local operator surface. It should not be treated as
approval for hardware motion, publication, destructive restore, or credential
changes.

## Optional Two-PC Collab Demo

Run this only after the single-PC proof is working. The recommended public
topology is a direct wired LAN or another trusted local network with a shared
folder that both machines can read and write.

Before involving two machines, run the packaged local transport smoke:

```bash
python3 tools/clutch_public_collab_smoke.py --root . --json
```

It should report `status=passed` with `public-main`, `public-worker`,
`req-public-smoke`, `request_opened`, and `request_result` evidence.

On the main machine:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py init \
  --shared-root /tmp/clutch-collab \
  --project-id demo \
  --machine-id main-laptop \
  --role main
```

On the worker machine:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py init \
  --shared-root /tmp/clutch-collab \
  --project-id demo \
  --machine-id worker-box \
  --role worker
```

Then attach Codex sessions as `main` and `worker` through `session-entry` and
watch the Collab monitor. The point is not the transport path itself; the point
is that CLUTCH makes roles, peer freshness, active requests, and worker results
visible instead of leaving them buried in chat.

## Away Development Demo

Use away development as a bounded operating protocol, not as unlimited
automation. A good demo prompt is:

```text
Prepare an away plan for documentation and test hardening only. Stop before
publishing, changing credentials, touching hardware, or deleting user work.
```

Show that the plan contains:

- objective;
- allowed files and actions;
- stop conditions;
- verification commands;
- checkpoint expectation;
- expiry.

## Public Launch Talking Points

Use these talking points for the README, landing page, and live demo:

- CLUTCH is for research teams where one project spans multiple PCs, Codex
  sessions, datasets, model weights, artifacts, and long-lived context.
- The core differentiators are multi-PC collab, visible collab monitor,
  backup/snapshot evidence, away-development planning, and a local Web UI.
- The Prompt Cookbook gives copy-ready examples for first install, first
  project, multi-PC collab, backup/artifacts, away development, Web UI, public
  release review, and safety boundaries.
- The Public Launch Readiness Brief aligns the GitHub page, landing page,
  first install path, release evidence, and final private-first visibility
  decision before launch.
- The public distribution asks users for their own GitHub, folders, machine id,
  artifact store, and collab topology instead of shipping private lab settings.
- Large files do not have to be committed to git. CLUTCH records artifact
  pointers and recovery evidence.
- No hardware motion, credential publication, destructive restore, or public
  repository visibility change is allowed without explicit operator approval.

## Closeout Checklist

Before ending the demo, run:

```bash
make verify
python3 tools/clutch_public_release_gate.py --root . --json
python3 tools/clutch_public_landing_smoke.py --root . --json
python3 tools/clutch_public_web_smoke.py --root . --json
```

The expected public release state is zero scanner findings, release gate status
`ready_for_operator_review`, a passing clean install smoke, passing landing and
Web smoke, and a repository visibility change only after the operator explicitly
approves it.
