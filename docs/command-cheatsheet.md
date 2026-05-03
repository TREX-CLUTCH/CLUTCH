# Command Cheat Sheet

This page collects the commands a new CLUTCH user is most likely to need after
installing the public distribution. Use it as a quick map, then read the linked
guides when a workflow becomes important.

## Verify A Release Tree

From the extracted release root:

```bash
make verify
make web-smoke
```

Equivalent detailed checks:

```bash
python3 tools/clutch_distribution_scan.py . --json
python3 tools/clutch_public_release_gate.py --root . --json
python3 tools/clutch_public_visibility_review.py --root . --json
python3 tools/clutch_public_landing_smoke.py --root . --json
python3 tools/clutch_public_web_smoke.py --root . --json
python3 tools/clutch_public_collab_smoke.py --root . --json
python3 tools/clutch_public_install_smoke.py --root . --json
```

Expected result: scanner findings are zero, the release gate says
`ready_for_operator_review`, visibility review says
`ready_for_manual_visibility_review`, landing smoke passes, Web smoke proves
first-run Web auto-start and Help/Monitor assets, collab smoke records
main/worker/request/result evidence, and the clean install smoke can create a
first project without private defaults.

For a feature-by-feature proof plan, use
[Verification Matrix](verification-matrix.md).

## Install And Enter

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

Use `--plan-only` with the wizard if you want to preview local config writes.

## Project Loop

Register a normal git workspace:

```bash
python3 scripts/clutch_ctl.py project-create --help
```

Then bind the active Codex session:

```bash
python3 scripts/clutch_ctl.py session-attach --project my-project --bind-role main --cwd /path/to/my-project --yes
```

Preview readiness before applying changes:

```bash
python3 scripts/clutch_ctl.py project-refresh --project my-project --dry-run
```

Check status:

```bash
python3 scripts/clutch_ctl.py project-status --project my-project
```

## Backup And Snapshot

Before risky work:

```bash
python3 scripts/clutch_ctl.py project-backup --project my-project
python3 scripts/clutch_ctl.py project-snapshot --project my-project --write
```

After a meaningful change:

```bash
python3 scripts/clutch_ctl.py project-versioning-readiness --project my-project
python3 scripts/clutch_ctl.py project-refresh --project my-project --dry-run
```

Large datasets, model weights, robot bags, media dumps, and caches should stay
in an artifact store unless your project intentionally chooses another policy.

## Web Console

`session-entry` normally starts the Web console after first-run setup. To start
it manually:

```bash
python3 scripts/clutch_ctl.py web-console-start --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

Use the dashboard for readiness, Help for operating protocol, and Monitor for
multi-PC collab visibility.

## Multi-PC Collab

Initialize a shared file transport on the main machine:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py init \
  --shared-root /path/to/shared-clutch-collab \
  --project-id lab-demo \
  --machine-id main-laptop \
  --role main
```

Initialize the worker:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py init \
  --shared-root /path/to/shared-clutch-collab \
  --project-id lab-demo \
  --machine-id gpu-worker \
  --role worker
```

Monitor the shared channel:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py monitor \
  --shared-root /path/to/shared-clutch-collab \
  --project-id lab-demo
```

Run the packaged local collab transport smoke:

```bash
make collab-smoke
```

For the full workflow, read [Multi-PC Collab](multi-pc-collab.md) and
[Two-PC Lab Tutorial](two-pc-lab-tutorial.md).

## Away Development

Use away development only with a bounded plan:

```text
Prepare an away plan for documentation and test hardening only. Stop before
publishing, changing credentials, touching hardware, or deleting user work.
```

The plan should name objective, scope, forbidden actions, stop conditions,
verification, checkpoint cadence, and expiry.

## Approval Boundary

CLUTCH command previews, Web status, collab monitor state, snapshots, and away
plans do not grant hidden authority. The following still require explicit
operator approval:

In short: any action that changes hardware, credentials, destructive recovery,
or public visibility requires explicit operator approval.

- live robot motion;
- hardware recovery;
- sudo, driver, system service, network, or udev changes;
- credential, token, or private key changes;
- destructive restore or deleting user work;
- changing a private repository to public.
