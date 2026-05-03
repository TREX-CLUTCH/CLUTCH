# Frequently Asked Questions

## Does CLUTCH include private lab settings?

No. The public distribution must not include private machine ids, hostnames,
LAN addresses, SSH aliases, robot profiles, GitHub tokens, account credentials,
local artifact paths, backups, snapshots, or private project history.

The first-run wizard asks each user to choose their own local folders, machine
identity, GitHub preference, admin token, artifact store, and optional multi-PC
setup.

## What problem does CLUTCH solve?

CLUTCH is a local-first Codex orchestration layer for AI and robotics teams. It
helps Codex sessions re-enter the right project, coordinate main/worker PCs,
make collab state visible, record backup and snapshot evidence, and bound
away development with explicit stop conditions.

## Is CLUTCH only for robotics labs?

No. Robotics labs are a strong target because they often have multiple PCs,
hardware safety boundaries, large artifacts, and long-lived project context.
The same model also fits AI teams that coordinate work across workstations,
servers, datasets, model weights, and local experiments.

## How do I install it?

Use the release zip first:

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

CLUTCH does not require sudo for the public install path.

## Can I install it with npm or npx?

Not in this release path. The current public distribution is release-zip based
so it can preserve the Python CLI, Web console static files, templates, docs,
and smoke tools without pretending that a package-manager wrapper is already
validated. A future wrapper can be added after the release zip path is stable.

## How do I connect GitHub?

The public package does not ship with a GitHub account or remote. The
first-run wizard asks for your GitHub setup preference. You can stay local
first, add your own project remotes later, or configure online sync only after
you know which repositories you own.

Public repository visibility changes still require operator approval.

## How do I choose an artifact store?

Choose a folder or storage location that you control and can back up. Use it
for large files that do not belong in git:

- datasets;
- model weights;
- generated checkpoints;
- robot bags;
- media captures;
- caches.

CLUTCH records artifact pointers and recovery notes. It does not copy every
large artifact into the source repository by default.

## How does Multi-PC collab work?

Install CLUTCH on each PC, use the same project id, and choose a shared
transport that both machines can access. A direct wired LAN is the recommended
starting point because it is predictable and easy to isolate.

The public file transport helper can initialize a shared folder:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py init \
  --shared-root /path/to/shared-clutch-collab \
  --project-id lab-demo \
  --machine-id main-laptop \
  --role main
```

Then initialize a worker with a different machine id and `--role worker`.

## What does the Collab monitor show?

The Collab monitor is an operator-visible surface for role source, peer
freshness, active requests, recent results, and stale-link warnings. It is
evidence and coordination context. It is not approval for hardware motion,
credential changes, destructive restore, or publication.

## What is the Web console for?

The Web console gives a local browser view of project status, attention items,
readiness checks, command previews, snapshots, backups, Help, and collab
monitor state.

Start it manually if needed:

```bash
python3 scripts/clutch_ctl.py web-console-start --host 127.0.0.1 --port 8765
```

Then open `http://127.0.0.1:8765`.

## What does backup and snapshot mean?

A backup preserves recoverable local state. A snapshot records reproducibility
metadata such as source heads, project id, machine id, restore hints, and
artifact pointers.

For a typical project:

```bash
python3 scripts/clutch_ctl.py project-backup --project my-project
python3 scripts/clutch_ctl.py project-snapshot --project my-project --write
```

Use `project-refresh --project my-project --dry-run` before applying sync or
metadata changes.

## What is away development?

Away development is a bounded plan for unattended Codex work. It should state
objective, allowed scope, forbidden actions, stop conditions, verification,
checkpoint cadence, and expiry.

It is not unrestricted automation. If work falls outside the plan, Codex should
stop and ask for a fresh operator decision.

## What always requires operator approval?

These actions require explicit operator approval:

- live robot motion;
- hardware recovery;
- sudo, driver, system service, network, or udev changes;
- credential, token, or private key changes;
- destructive restore or deleting user work;
- publishing private data;
- changing public repository visibility.
