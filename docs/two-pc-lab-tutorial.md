# Two-PC Lab Tutorial

This tutorial shows the smallest useful CLUTCH setup for a lab with two PCs:
one operator machine and one worker machine. It uses only user-provided local
paths and a shared folder. No private IP address, SSH alias, GitHub account, or
hardware profile is included in the public package.

## Goal

By the end, both machines should be able to:

- enter through CLUTCH with `session-entry`;
- attach to the same project with clear `main` and `worker` roles;
- exchange a text request/result through a shared collab folder;
- keep the Web Monitor or collab monitor visible while work is active;
- create local backup and snapshot evidence before risky handoff.

## 1. Install On Both PCs

Run the normal install and first-run setup on each machine:

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

Use different machine ids. Example names such as `main-laptop` and
`gpu-worker` are placeholders; choose names that make sense for your lab.
On each PC, print the local machine id:

```bash
LOCAL_MACHINE_ID="$(python3 scripts/clutch_ctl.py machine-profile --json \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["machine_id"])')"
printf 'This PC machine id: %s\n' "$LOCAL_MACHINE_ID"
```

Exchange those two machine ids between the operator and worker PCs. The
examples below use:

- `MAIN_MACHINE_ID`: the operator PC's machine id;
- `WORKER_MACHINE_ID`: the worker PC's machine id;
- `LOCAL_MACHINE_ID`: the machine id of the PC where the command is running.

On the operator PC:

```bash
MAIN_MACHINE_ID="$LOCAL_MACHINE_ID"
WORKER_MACHINE_ID="<worker-machine-id>"
```

On the worker PC:

```bash
MAIN_MACHINE_ID="<main-machine-id>"
WORKER_MACHINE_ID="$LOCAL_MACHINE_ID"
```

## 2. Prepare A Shared Folder

Choose one folder that both PCs can read and write. A direct wired LAN share is
usually the simplest reliable lab setup, but CLUTCH does not care which file
sharing tool provides the folder.

Examples of valid transports:

- an NFS or SMB share mounted on both PCs;
- SSHFS mounted by the user;
- Syncthing;
- rsync over SSH into a shared directory;
- any other local file sync tool you trust.

Use the same effective shared path on both PCs when possible:

```bash
export CLUTCH_COLLAB_ROOT="$HOME/clutch-collab-shared"
mkdir -p "$CLUTCH_COLLAB_ROOT"
```

## 3. Register The Same Project On Both PCs

The project id must match on both PCs. For a first smoke test, use
`lab-demo`. Each PC needs its own local registry entry because each PC has its
own workspace path and machine-local CLUTCH memory.

On each PC, create a normal git workspace:

```bash
PROJECT_ROOT="$HOME/clutch-projects/lab-demo"
mkdir -p "$PROJECT_ROOT"
cd "$PROJECT_ROOT"
git init
git config user.name "CLUTCH Example"
git config user.email "example@clutch.local"
printf '# Lab Demo\n' > README.md
git add README.md
git commit -m "Initial lab demo project"
git branch -M main
```

Then return to CLUTCH and register the project on that PC:

```bash
cd "$CLUTCH_HOME/foundation/current"
python3 scripts/clutch_ctl.py project-create \
  --project lab-demo \
  --display-name "Lab Demo" \
  --machine-workspace "$LOCAL_MACHINE_ID=$PROJECT_ROOT" \
  --repo-source "lab-demo:$LOCAL_MACHINE_ID=$PROJECT_ROOT" \
  --no-repo-required \
  --participant-machine "$LOCAL_MACHINE_ID" \
  --owner-machine "$MAIN_MACHINE_ID" \
  --role-policy none \
  --no-admin-guard-required \
  --update \
  --yes
```

On the operator PC, attach as `main`:

```bash
python3 scripts/clutch_ctl.py session-attach \
  --project lab-demo \
  --bind-role main \
  --cwd "$PROJECT_ROOT" \
  --yes
```

On the worker PC, attach as `worker`:

```bash
python3 scripts/clutch_ctl.py session-attach \
  --project lab-demo \
  --bind-role worker \
  --cwd "$PROJECT_ROOT" \
  --yes
```

The workspace paths can differ by PC. CLUTCH treats machine-local paths as
machine-local facts and translates context through project metadata and collab
evidence.

## 4. Initialize File-Based Collab

On the operator machine:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py init \
  --shared-root "$CLUTCH_COLLAB_ROOT" \
  --project-id lab-demo \
  --machine-id "$LOCAL_MACHINE_ID" \
  --role main
```

On the worker machine:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py init \
  --shared-root "$CLUTCH_COLLAB_ROOT" \
  --project-id lab-demo \
  --machine-id "$LOCAL_MACHINE_ID" \
  --role worker
```

## 5. Send A Request

On the operator machine:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py request \
  --shared-root "$CLUTCH_COLLAB_ROOT" \
  --project-id lab-demo \
  --from-machine "$LOCAL_MACHINE_ID" \
  --to-machine "$WORKER_MACHINE_ID" \
  --kind inspect \
  --summary "Check training logs" \
  --body "Read the latest run logs and report loss trend, OOM risk, throughput, and next action."
```

In normal use, you can ask the main Codex session in natural language, for
example:

```text
서브에게 최신 학습 로그를 보고 OOM 위험과 다음 조치를 정리하라고 맡겨줘.
```

CLUTCH's transport records the evidence. Codex still needs clear operator
instructions and must stay inside the current approval boundary.

## 6. Record A Worker Result

On the worker machine:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py result \
  --shared-root "$CLUTCH_COLLAB_ROOT" \
  --project-id lab-demo \
  --from-machine "$LOCAL_MACHINE_ID" \
  --request-id req-example \
  --status completed \
  --summary "Training smoke passed" \
  --body "The latest smoke run completed. Peak memory stayed under the selected limit."
```

Use the actual request id printed by the `request` command.

## 7. Keep The Monitor Visible

For a terminal monitor:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py monitor \
  --shared-root "$CLUTCH_COLLAB_ROOT" \
  --project-id lab-demo
```

For the Web console, run `session-entry` and open the Monitor tab. A healthy
collab session should make it obvious which machine is `main`, which machine is
`worker`, whether the peer is fresh, and which request/result is current.

## 8. Preserve Recovery Evidence

Before risky handoff, long work, or release:

```bash
python3 scripts/clutch_ctl.py project-refresh --project lab-demo --dry-run
python3 scripts/clutch_ctl.py project-backup --project lab-demo
python3 scripts/clutch_ctl.py project-snapshot --project lab-demo --write
```

Large datasets, model weights, robot bags, media dumps, and caches should stay
in your artifact store. Record their paths, hashes, or URIs instead of forcing
them into git.

## Safety Boundary

Collab evidence is not approval. Live robot motion, hardware recovery, sudo,
network reconfiguration, credential handling, destructive restore, and public
publication still require fresh explicit operator approval.
