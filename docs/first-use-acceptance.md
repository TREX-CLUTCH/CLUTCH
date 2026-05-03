# First-Use Acceptance Runbook

Use this runbook after installing a CLUTCH public release. It defines the
minimum experience a new user should have before trusting the package for real
project work.

The automated form is:

```bash
make verify
```

The specific clean install path is:

```bash
tools/clutch_public_install_smoke.py --root . --json
```

The smoke uses a temporary home and proves that CLUTCH can install, collect first-run choices once, run doctor, enter through CLUTCH, repeat `session-entry` without setup prompts, create a first git project, attach a main session, create a backup, create a snapshot, run a read-only project refresh, and keep the user project workspace clean.

## Acceptance Criteria

- The installer completes without sudo.
- The first-run wizard records durable local choices for `CLUTCH_HOME`, project
  root, artifact store, machine id, GitHub setup preference, Web console
  preference, and admin guard setup.
- `session-entry` does not ask for the same first-run decisions again after the
  wizard writes config.
- `session-entry` opens the Web console or prints the URL, depending on the
  user's local browser policy.
- A repeated `session-entry` reports durable local state and does not ask the
  user to choose machine defaults, run first-run setup again, or re-enter
  GitHub/artifact/collab choices.
- `project-create` can register a normal user-owned git workspace.
- `session-attach` can bind the current Codex session as `main`.
- `project-backup` creates local backup evidence.
- `project-snapshot --write` creates snapshot metadata without writing CLUTCH
  metadata into the user's project repository.
- `project-refresh --dry-run` explains remaining readiness gaps without
  publishing online, changing credentials, moving hardware, deleting user work,
  or changing network settings.
- `project_workspace_hygiene` reports no `.clutch`, `machines`, `snapshots`,
  `backups`, `runtime`, or `registry` folders in the user's project repo, and
  `git status --porcelain` remains clean.

## Manual Check

Run:

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

Then create a small git project and run:

```bash
python3 scripts/clutch_ctl.py project-create --help
python3 scripts/clutch_ctl.py session-attach --project <project_id> --bind-role main --cwd <project_root> --yes
python3 scripts/clutch_ctl.py project-backup --project <project_id>
python3 scripts/clutch_ctl.py project-snapshot --project <project_id> --write
python3 scripts/clutch_ctl.py project-refresh --project <project_id> --dry-run
```

Expected result:

- CLUTCH uses the folders chosen during first-run setup.
- CLUTCH does not request a private GitHub account, SSH endpoint, LAN IP,
  artifact root, robot profile, or hardware configuration from the release
  tree.
- Warnings, if present, are actionable setup gaps such as optional GitHub sync
  or artifact pointers.
- The user can continue single-PC work without configuring multi-PC collab.

## No-Go Signals

Do not publish the release if any first-use path:

- asks for the same first-run choices repeatedly after config was written;
- writes CLUTCH runtime or machine-local state into the user's project repo;
- requires sudo for the default install;
- requires a private GitHub remote, SSH alias, LAN IP, machine id, token, or
  hardware profile;
- starts live hardware actions;
- performs online publication or public visibility changes;
- deletes user work or runs a destructive restore.

## Evidence To Record

For a release candidate, record:

- `clutch_public_install_smoke.py` status;
- `session_entry` step status;
- `session_entry_repeat` step status;
- `first_run_repeat_prompt_check` status;
- `project_create` step status;
- `session_attach` step status;
- `project_backup` step status;
- `project_snapshot` step status;
- `project_refresh` step status;
- `project_workspace_hygiene` step status;
- whether `remote_visibility_change_performed=false`;
- whether the private staging repository remains private.
