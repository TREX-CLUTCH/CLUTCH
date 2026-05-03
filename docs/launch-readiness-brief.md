# Public Launch Readiness Brief

Use this brief before presenting CLUTCH as a public GitHub project. It is a
review aid for the repository page, landing page, release package, and first
install path. It does not replace the release gate or the public release
checklist.

## Positioning

CLUTCH is a local-first Codex orchestration layer for AI and robotics labs. It
helps a user keep project re-entry, main and worker roles, multi-PC Codex collab,
visible monitor state, backups, snapshots, artifact pointers, Web UI, and
bounded away development in one operator-visible workflow.

The public distribution must feel useful on a single personal machine first,
then guide the user toward a lab-scale multi-PC topology when they choose one.
It must never assume a private peer host, LAN IP, SSH alias, GitHub account,
artifact root, robot profile, or hardware configuration.

## Core Differentiators

- Multi-PC Codex collab with a user-owned transport path, preferably direct
  wired LAN when practical.
- Collab monitor evidence for role state, peer freshness, active requests,
  acknowledgements, and returned results.
- Backup and snapshot workflow for large projects, with artifact pointers for
  datasets, model weights, media, logs, and generated outputs.
- Away-development plans with objective, allowed scope, expiry, stop
  conditions, and verification evidence.
- Web UI for Dashboard, Monitor, Commands, Backups, Machines, and Help.
- First-run wizard that asks the user for local folders, machine identity,
  GitHub setup preference, admin guard policy, and optional collab topology.

## First Visitor Path

1. The README first screen shows the CLUTCH image, one-line positioning, and
   the 10-minute first-use path.
2. The landing page explains CLUTCH through the research-agent use case, not a
   generic automation pitch.
3. The install path starts from the release zip and uses the user's own
   `CLUTCH_HOME`.
4. The First-Use Acceptance Runbook defines the install, doctor,
   `session-entry`, first project, backup, snapshot, and refresh checks a new
   user should pass without repeated setup prompts.
5. The Prompt Cookbook gives copy-ready prompts for install, first project,
   multi-PC collab, backups, away development, Web UI, release review, and
   safety boundaries.
6. The Verification Matrix tells reviewers which command proves each user
   promise.

## GitHub Page Review

Before the private repository is made public, check that the GitHub page makes
these points clear without requiring tribal knowledge:

- CLUTCH is an operating layer around Codex sessions, not a replacement for
  Codex.
- A single-PC user can install, create a first project, back it up, snapshot
  it, and open the Web console.
- A lab user can later build multi-PC collab through their own wired LAN,
  shared folder, SSH, or sync tool.
- Private information is not bundled into the release tree.
- Large artifacts are recorded as pointers unless the user chooses a storage
  backend.
- Public visibility requires explicit operator approval after the final gate.

## Required Evidence

The release is not ready for public visibility until all of these are true:

- `make verify` passes from the exported release root.
- `tools/clutch_public_release_gate.py --root . --json` reports
  `ready_for_operator_review` with `finding_count=0`.
- `tools/clutch_public_visibility_review.py --root . --json` reports
  `ready_for_manual_visibility_review`.
- `remote_visibility_change_performed=false`.
- `tools/clutch_public_landing_smoke.py --root . --json` passes.
- `tools/clutch_public_web_smoke.py --root . --json` passes with first-run Web
  auto-start, `/api/health`, Help, Monitor, Backups, and asset evidence.
- `tools/clutch_public_collab_smoke.py --root . --json` passes with main,
  worker, request, result, and recent event evidence.
- `tools/clutch_public_install_smoke.py --root . --json` passes or has a
  documented operator-approved deferral.
- The release zip, checksum file, release notes, and release manifest stay
  together.
- The private staging repository remains private until the operator approves
  the visibility change.

## Go / No-Go

Go only when the README, landing page, Prompt Cookbook, Verification Matrix,
First-Use Acceptance Runbook, privacy guide, release checklist, release notes,
installer, Web Help, and package manifest all tell the same story.

No-go if any public file contains private machine ids, hostnames, home paths,
LAN IPs, SSH aliases, GitHub tokens, private remotes, runtime state, backups,
snapshots, project histories, or lab-specific hardware assumptions.

No-go if the first install path asks the user for the same decision repeatedly
after first-run setup. The first-run wizard should collect durable local
choices once, and later commands should use those choices or explain the
missing setup.

No-go if any command would publish the repository, alter credentials, change
network settings, touch hardware, delete user work, or perform a destructive
restore without fresh explicit approval.
