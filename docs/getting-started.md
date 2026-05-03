# Getting Started

This guide assumes you downloaded a CLUTCH release zip and want a local-first
setup on one machine before adding multi-PC collaboration.

## What This First Run Should Prove

The first run is not only an installation check. It should prove that CLUTCH can
re-enter a Codex session, open or report the Web console, register a normal git
project, create a local backup, create snapshot metadata, and explain remaining
readiness gaps without forcing you to publish anything online.

## 1. Install

```bash
unzip clutch-public-*.zip
cd clutch-public-*
export CLUTCH_HOME="${CLUTCH_HOME:-$HOME/.clutch}"
bash installer/install.sh --prefix "$CLUTCH_HOME"
```

The default install location is:

```text
$HOME/.clutch/foundation/current
```

Use a custom location only if you already know how you want to manage CLUTCH:

```bash
bash installer/install.sh --prefix "$HOME/dev/.clutch"
```

## 2. Run First-Run Setup

```bash
cd "$CLUTCH_HOME/foundation/current"
python3 installer/clutch_first_run_wizard.py
```

The wizard asks for:

- CLUTCH home directory;
- project root directory;
- local artifact store;
- machine display name and machine id;
- session attach default;
- online sync preference;
- GitHub setup preference;
- local admin token;
- optional multi-PC collab pairing.

The token is stored as a salted local hash. CLUTCH does not write the token into
commands, logs, or release files.

Interactive setup writes the local config by default. To preview without
writing, run:

```bash
python3 installer/clutch_first_run_wizard.py --plan-only
```

## 3. Run Doctor

```bash
python3 installer/clutch_doctor.py
```

Doctor is read-only. It checks the distribution layout, Python version, optional
Git/Codex availability, first-run config, and admin guard.

## 4. Enter Through CLUTCH

```bash
python3 scripts/clutch_ctl.py session-entry
```

By default, the public first-run wizard configures CLUTCH to start the local
Web console when `session-entry` runs. On a local desktop it will try to open the
browser safely. On a headless server or SSH session it will leave the browser
closed and print the URL.

For normal Codex work, make this the first step of every session. The public
package includes a reusable `AGENTS.md` template:

```text
templates/AGENTS.clutch.example.md
```

See [Codex Session Entry](codex-session-entry.md) for the recommended entry
block, custom-prefix handling, and what not to put in `AGENTS.md`.

## 5. Register Your First Project

The public distribution starts with an empty project registry. Create a normal
git workspace first, then register that workspace with CLUTCH.

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
```

CLUTCH keeps its own machine-local project memory under
`$CLUTCH_HOME/local/projects`. It should not create `machines/` or other CLUTCH
metadata folders inside your git workspace.

Attach the current Codex session to the project:

```bash
python3 scripts/clutch_ctl.py session-attach --project my-project --bind-role main --cwd "$PROJECT_ROOT" --yes
```

Then create the first local backup and reproducibility snapshot:

```bash
python3 scripts/clutch_ctl.py project-backup --project my-project
python3 scripts/clutch_ctl.py project-snapshot --project my-project --write
```

If you have not configured a GitHub remote yet, some online publication or
fresh metadata checks may remain informational. Local backup and snapshot
creation still work.

## 6. Open The Web Console

```bash
python3 scripts/clutch_web.py --host 127.0.0.1 --port 8765
```

Then open:

```text
http://127.0.0.1:8765
```

Use the dashboard for status, the Monitor tab for collab visibility, and Help
for the operating protocol.

## 7. Read The First Status Like An Operator

For a new project, warnings usually mean "finish setup" rather than "the system
is broken." Start with the read-only preview:

```bash
python3 scripts/clutch_ctl.py project-refresh --project my-project --dry-run
```

Then decide what to configure next:

- add a GitHub remote if source history should be online;
- choose an artifact store if large datasets, model weights, media, or robot
  logs should be tracked by pointer;
- set up multi-PC collab only after the single-PC loop works;
- keep hardware, sudo, credential, destructive restore, and public publication
  actions behind explicit operator approval.
