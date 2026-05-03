# Multi-PC Collab

CLUTCH collab is designed for lab-style AI and robotics work where one PC is
the operator's main session and another PC may have extra compute, a different
GPU, hardware access, or a long-running worker task.

If you want a concrete start-to-finish walkthrough, use
[Two-PC Lab Tutorial](two-pc-lab-tutorial.md) first, then return here for the
collab model and safety boundary.

## Recommended Network

Use a direct wired LAN when possible. It is predictable, fast, and easy to
isolate from public networks.

CLUTCH does not ship with peer IPs or SSH aliases. Each user chooses their own
transport:

- NFS or SMB shared folder;
- SSHFS;
- Syncthing;
- rsync over SSH;
- a git remote owned by the user;
- another local file sync tool.

## Roles

- `main`: the operator-facing session that owns project direction.
- `worker`: the peer session that receives bounded tasks or questions.
- `observer`: a read-only or low-authority session for inspection.

The active binding matters more than the machine name. A laptop can be `main`
today and `worker` tomorrow if the project operator binds it that way.

## Safe File Transport

The public distribution includes a file-based collab helper. It works anywhere
both machines can see the same shared folder.

On the main machine:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py init \
  --shared-root /path/to/shared-clutch-collab \
  --project-id lab-demo \
  --machine-id main-laptop \
  --role main
```

On the worker machine:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py init \
  --shared-root /path/to/shared-clutch-collab \
  --project-id lab-demo \
  --machine-id gpu-worker \
  --role worker
```

Send a request:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py request \
  --shared-root /path/to/shared-clutch-collab \
  --project-id lab-demo \
  --from-machine main-laptop \
  --to-machine gpu-worker \
  --kind inspect \
  --summary "Check training memory pressure" \
  --body "Read the latest run logs and report OOM risk, throughput, and next action."
```

Record a worker result:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py result \
  --shared-root /path/to/shared-clutch-collab \
  --project-id lab-demo \
  --from-machine gpu-worker \
  --request-id req-example \
  --status completed \
  --summary "No OOM at batch size 2" \
  --body "The run completed the smoke window. Peak memory remained below the selected limit."
```

Monitor:

```bash
python3 collab_transport/scripts/clutch_collab_file_transport.py monitor \
  --shared-root /path/to/shared-clutch-collab \
  --project-id lab-demo
```

## Codex Worker Pattern

The practical pattern is still natural language:

1. Bind one Codex session as `main`.
2. Bind the other session as `worker`.
3. Use CLUTCH status and monitor evidence to confirm roles.
4. Tell the main Codex session what to delegate.
5. The worker records results in the shared collab channel or directly in its
   Codex session, depending on the operator's setup.

The transport is evidence and handoff plumbing. It is not a replacement for
operator judgement.

## Safety Boundary

Collab state does not authorize live robot motion, sudo changes, credential
changes, network reconfiguration, hardware recovery, or destructive restore.
Those actions require fresh explicit approval.
