# Public Release Notes Template

Use this template for a public CLUTCH GitHub release. Keep the language focused
on what a new user can install, test, and safely use.

The package builder also writes `clutch-public-<version>.release-notes.md` with
the actual zip SHA256 and gate results. Use that generated file when available,
and use this template when drafting manually.

## Release Summary

CLUTCH is a local-first Codex orchestration layer for AI and robotics labs. It
helps teams keep Codex sessions, project roles, multi-PC collaboration, Web
status, backups, snapshots, artifact pointers, and away-development plans in
one operator-visible workflow.

This release is intended for users who want to install CLUTCH on their own
machines without inheriting any private lab settings, accounts, peer addresses,
or hardware profiles.

## Install

```bash
unzip clutch-public-<version>.zip
cd clutch-public-<version>
export CLUTCH_HOME="${CLUTCH_HOME:-$HOME/.clutch}"
bash installer/install.sh --prefix "$CLUTCH_HOME"
cd "$CLUTCH_HOME/foundation/current"
python3 installer/clutch_first_run_wizard.py
python3 installer/clutch_doctor.py
python3 scripts/clutch_ctl.py session-entry
```

The installer does not require sudo. The first-run wizard asks the user to pick
local paths, machine identity, admin guard setup, GitHub setup preference, and
optional collab settings.

## 10-Minute First Use Path

1. Run the first-run wizard and choose local folders.
2. Run `session-entry` and confirm the Web console opens or prints a URL.
3. Register a small git project with `project-create`.
4. Attach the active Codex session as `main`.
5. Create a local backup and a snapshot.
6. Run `project-refresh --dry-run` to see what is ready and what still needs
   optional GitHub or artifact setup.

## Highlights

- Project re-entry for Codex sessions with `main`, `worker`, and `observer`
  bindings.
- Web console for Dashboard, Sessions, Monitor, Projects, Backups, Machines,
  Commands, and Help.
- Static public landing page with a 2-4 word hook hero, visual branding,
  guided first-run tutorial, multi-PC topology, safety boundary, example
  operator prompts, and a GitHub call-to-action.
- Prompt Cookbook with copy-ready prompts for first install, first project,
  multi-PC collab, backup/artifacts, away development, Web UI, public release
  review, and safety boundaries.
- Public Launch Readiness Brief that aligns the GitHub page, landing page,
  package evidence, first install path, core differentiators, and final
  private-first visibility decision.
- First-Use Acceptance Runbook that defines the install, first-run, doctor,
  session-entry, session_entry_repeat, first project, backup, snapshot, and
  refresh checks a new user should pass without repeated setup prompts or
  project workspace metadata pollution.
- Multi-PC collab guidance for lab setups with direct wired LAN, SSH, Codex
  worker sessions, or a user-owned shared folder.
- Visible collab monitor for role state, peer freshness, task evidence,
  acknowledgements, and results.
- Backup and reproducibility workflow using git source heads, local backup
  bundles, snapshot metadata, validation evidence, and artifact pointers.
- Large artifact policy that keeps datasets, model weights, robot bags, media,
  and caches outside git unless the project explicitly chooses otherwise.
- Away-development plans with objective, allowed scope, stop conditions,
  verification requirements, and expiry.
- Public first-run flow with no preset private GitHub account, SSH endpoint,
  LAN IP, machine id, hardware profile, token, or private project path.

## Safety Boundary

CLUTCH state, worker replies, and monitor heartbeat do not authorize:

- live robot motion;
- hardware recovery;
- sudo, service, network, kernel, or udev changes;
- credential handling;
- destructive restore;
- online publication.

Those actions require fresh explicit operator approval.

## Validation

Record the actual evidence for this release:

- public export scanner: `finding_count=0`
- private denylist scanner: `finding_count=0`
- public release gate: `ready_for_operator_review`
- visibility review: `ready_for_manual_visibility_review` from
  `tools/clutch_public_visibility_review.py --root . --json`
- landing page smoke: `tools/clutch_public_landing_smoke.py --root . --json`
  `<passed / deferred with reason>`
- Web console smoke: `tools/clutch_public_web_smoke.py --root . --json`
  `<passed / deferred with reason>`
- collab transport smoke:
  `tools/clutch_public_collab_smoke.py --root . --json`
  `<passed / deferred with reason>`
- release package manifest: `<path or attached artifact name>`
- clean install smoke: `<passed / deferred with reason>`
- first project smoke: `<passed / deferred with reason>`
- repeated setup prompt check: `<passed / failed>`
- project workspace hygiene: `<passed / failed>`
- real two-machine collab rehearsal: `<passed / deferred with reason>`
- release zip SHA256: `<sha256>`
- checksum file SHA256: `<sha256>`
- release notes SHA256: `<sha256>`
- release manifest SHA256: `<sha256>`
- public landing page source: `site/index.html`
- release artifact guide: `docs/release-artifacts.md`

## Known Limitations

- CLUTCH does not replace Codex. It is an operating layer around Codex sessions.
- CLUTCH does not ship a user's GitHub account, remotes, SSH keys, peer IPs, or
  artifact store.
- Multi-PC collab still depends on a user-owned transport such as wired LAN,
  shared folder, SSH, rsync, Syncthing, or another local sync tool.
- Large model and dataset artifacts are tracked by path, URI, hash, or manifest
  pointer unless the project chooses a storage backend.
- Public visibility must be enabled only after the Public Release Checklist
  passes and the operator explicitly approves the visibility change.

## Links

- Getting Started: `docs/getting-started.md`
- Public Landing Page: `site/index.html`
- Codex Session Entry: `docs/codex-session-entry.md`
- Multi-PC Collab: `docs/multi-pc-collab.md`
- Two-PC Lab Tutorial: `docs/two-pc-lab-tutorial.md`
- Backup And Restore: `docs/backup-and-restore.md`
- Away Development: `docs/away-development.md`
- Release Artifacts: `docs/release-artifacts.md`
- Verification Matrix: `docs/verification-matrix.md`
- Prompt Cookbook: `docs/prompt-cookbook.md`
- Public Launch Readiness Brief: `docs/launch-readiness-brief.md`
- First-Use Acceptance Runbook: `docs/first-use-acceptance.md`
- Public Release Checklist: `docs/public-release-checklist.md`
- Security Boundary: `SECURITY.md`
